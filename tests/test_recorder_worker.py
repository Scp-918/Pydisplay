from __future__ import annotations

import json

from pydisplay.protocol.models import DecodedSample
from pydisplay.recorder.raw_bin_format import RecordType, read_raw_bin
from pydisplay.recorder.recorder_worker import RecorderWorker, RecordingState


def make_sample() -> DecodedSample:
    return DecodedSample(
        timestamp_pc_ns=100,
        relative_time_s=0.1,
        frame_seq=None,
        sample_seq=1,
        ppg_g=1,
        ppg_r=2,
        ppg_ir=3,
        acc_x=0.0,
        acc_y=0.0,
        acc_z=1.0,
        gyro_x=0.0,
        gyro_y=0.0,
        gyro_z=0.0,
        uh1=1,
        uh2=2,
        uh3=3,
        uh4=4,
        uc1=0.5,
        uc2=1,
        uc3=1.5,
        uc4=2,
        ud1=0.25,
        ud2=0.4,
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
    assert "PPG_G" in (session_dir / "decoded.csv").read_text(encoding="utf-8")

    metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["session"]["record_start_time"] is not None
    assert metadata["session"]["record_end_time"] is not None
    assert metadata["session"]["record_path"] == str(session_dir)
