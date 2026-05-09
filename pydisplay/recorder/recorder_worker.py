"""Background recorder worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import logging
from pathlib import Path
import queue
import re
import threading
import time
from typing import Literal

from pydisplay.protocol.models import DecodedSample
from .csv_writer import DecodedCsvWriter
from .metadata import build_metadata, write_metadata
from .raw_bin_format import RawBinWriter, RecordType


LOGGER = logging.getLogger(__name__)


class RecordingState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RECORDING = "recording"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class RecordEvent:
    kind: Literal["raw", "valid_frame", "bad_frame", "decoded", "stop"]
    timestamp_ns: int
    payload: bytes | DecodedSample | None


class RecorderWorker:
    """Batch file writer for raw bin, decoded csv, and metadata."""

    def __init__(self, *, max_queue_size: int = 10000, flush_interval_s: float = 1.0) -> None:
        self.queue: queue.Queue[RecordEvent] = queue.Queue(maxsize=max_queue_size)
        self.flush_interval_s = flush_interval_s
        self.state = RecordingState.IDLE
        self.session_dir: Path | None = None
        self.last_error: str | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._raw_writer: RawBinWriter | None = None
        self._csv_writer: DecodedCsvWriter | None = None
        self._metadata: dict | None = None

    @property
    def queue_size(self) -> int:
        return self.queue.qsize()

    def start(
        self,
        *,
        base_dir: str | Path,
        experiment_name: str = "experiment",
        metadata: dict | None = None,
    ) -> Path:
        if self.state == RecordingState.RECORDING:
            raise RuntimeError("recorder is already running")
        self.state = RecordingState.STARTING
        self._stop_event.clear()
        self.session_dir = _make_session_dir(Path(base_dir), experiment_name)
        self.session_dir.mkdir(parents=True, exist_ok=False)
        start_iso = datetime.now(timezone.utc).isoformat()
        self._metadata = metadata or build_metadata(record_path=self.session_dir, record_start_time=start_iso)
        self._raw_writer = RawBinWriter(self.session_dir / "raw_frames.bin", created_unix_ns=time.time_ns())
        self._csv_writer = DecodedCsvWriter(self.session_dir / "decoded.csv")
        self._raw_writer.open()
        self._csv_writer.open()
        write_metadata(self.session_dir / "metadata.json", self._metadata)
        self._thread = threading.Thread(target=self._run, name="RecorderWorker", daemon=True)
        self._thread.start()
        self.state = RecordingState.RECORDING
        return self.session_dir

    def stop(self, timeout_s: float = 3.0) -> None:
        if self.state not in {RecordingState.RECORDING, RecordingState.ERROR}:
            return
        self.state = RecordingState.STOPPING
        self.enqueue_stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout_s)
        self._finalize()
        self.state = RecordingState.STOPPED if self.last_error is None else RecordingState.ERROR

    def enqueue_raw_chunk(self, timestamp_ns: int, data: bytes) -> None:
        self.queue.put_nowait(RecordEvent("raw", timestamp_ns, bytes(data)))

    def enqueue_valid_frame(self, timestamp_ns: int, data: bytes) -> None:
        self.queue.put_nowait(RecordEvent("valid_frame", timestamp_ns, bytes(data)))

    def enqueue_bad_fragment(self, timestamp_ns: int, data: bytes) -> None:
        self.queue.put_nowait(RecordEvent("bad_frame", timestamp_ns, bytes(data)))

    def enqueue_decoded(self, sample: DecodedSample) -> None:
        self.queue.put_nowait(RecordEvent("decoded", sample.timestamp_pc_ns, sample))

    def enqueue_stop(self) -> None:
        self.queue.put(RecordEvent("stop", time.time_ns(), None))

    def _run(self) -> None:
        last_flush = time.monotonic()
        try:
            while True:
                event = self.queue.get()
                if event.kind == "stop":
                    break
                self._write_event(event)
                if time.monotonic() - last_flush >= self.flush_interval_s:
                    self._flush()
                    last_flush = time.monotonic()
        except Exception as exc:
            LOGGER.exception("Recorder worker failed")
            self.last_error = str(exc)
            self.state = RecordingState.ERROR
        finally:
            self._flush()

    def _write_event(self, event: RecordEvent) -> None:
        if event.kind == "decoded":
            if not isinstance(event.payload, DecodedSample) or self._csv_writer is None:
                raise RuntimeError("invalid decoded record event")
            self._csv_writer.write_sample(event.payload)
            return

        if not isinstance(event.payload, bytes) or self._raw_writer is None:
            raise RuntimeError("invalid raw record event")
        record_type = {
            "raw": RecordType.RAW_SERIAL_CHUNK,
            "valid_frame": RecordType.VALID_RAW_FRAME,
            "bad_frame": RecordType.BAD_FRAME_FRAGMENT,
        }[event.kind]
        self._raw_writer.write_record(record_type, event.timestamp_ns, event.payload)

    def _flush(self) -> None:
        if self._raw_writer:
            self._raw_writer.flush()
        if self._csv_writer:
            self._csv_writer.flush()

    def _finalize(self) -> None:
        if self._metadata is not None and self.session_dir is not None:
            self._metadata["session"]["record_end_time"] = datetime.now(timezone.utc).isoformat()
            write_metadata(self.session_dir / "metadata.json", self._metadata)
        if self._raw_writer:
            self._raw_writer.close()
            self._raw_writer = None
        if self._csv_writer:
            self._csv_writer.close()
            self._csv_writer = None


def _make_session_dir(base_dir: Path, experiment_name: str) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", experiment_name).strip("_") or "experiment"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_dir / f"{timestamp}_{safe_name}"
