from __future__ import annotations

import json

from pydisplay.protocol.models import DecodedSample
from pydisplay.recorder.raw_bin_format import RecordType, read_raw_bin
from pydisplay.recorder.recorder_worker import RecorderWorker, RecordingState


def make_sample() -> DecodedSample:
    adc_fields = {f"adc_ch{channel}_slot{slot}": channel * 100 + slot for channel in range(1, 5) for slot in range(6)}
    return DecodedSample(
        timestamp_pc_ns=100,
        relative_time_s=0.1,
        frame_seq=None,
        sample_seq=1,
        **adc_fields,
    )


def test_recorder_worker_writes_all_session_files_and_end_time(tmp_path) -> None:
    worker = RecorderWorker(flush_interval_s=99)
    session_dir = worker.start(base_dir=tmp_path, experiment_name="worker test")

    worker.enqueue_raw_chunk(10, b"abc")
    worker.enqueue_valid_frame(20, b"frame")
    worker.enqueue_decoded(make_sample())
    worker.stop()

    assert worker.state == RecordingState.STOPPED
    assert (session_dir / "raw_frames.bin").exists()
    assert (session_dir / "decoded.csv").exists()
    assert (session_dir / "metadata.json").exists()

    _header, records = read_raw_bin(session_dir / "raw_frames.bin")
    assert [record.record_type for record in records] == [
        RecordType.RAW_SERIAL_CHUNK,
        RecordType.VALID_RAW_FRAME,
    ]
    assert "adc_ch1_slot0" in (session_dir / "decoded.csv").read_text(encoding="utf-8")

    metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["session"]["record_start_time"] is not None
    assert metadata["session"]["record_end_time"] is not None
    assert metadata["session"]["record_path"] == str(session_dir)
