from __future__ import annotations

from pydisplay.gui.plots.ring_buffer import SampleRingBuffer
from pydisplay.protocol.models import DecodedSample


def make_sample(index: int, t: float) -> DecodedSample:
    return DecodedSample(
        timestamp_pc_ns=index,
        relative_time_s=t,
        frame_seq=None,
        sample_seq=index,
        ppg_g=index,
        ppg_r=index + 1,
        ppg_ir=index + 2,
        acc_x=0,
        acc_y=0,
        acc_z=1,
        gyro_x=0,
        gyro_y=0,
        gyro_z=0,
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


def test_ring_buffer_keeps_capacity() -> None:
    buffer = SampleRingBuffer(capacity=3)
    for index in range(5):
        buffer.append(make_sample(index, index * 0.01))

    assert len(buffer) == 3
    x, y = buffer.get_series("ppg_g")
    assert x == [0.02, 0.03, 0.04]
    assert y == [2.0, 3.0, 4.0]


def test_ring_buffer_filters_recent_window() -> None:
    buffer = SampleRingBuffer(capacity=10)
    for index in range(5):
        buffer.append(make_sample(index, float(index)))

    x, y = buffer.get_series("ppg_r", window_seconds=2.0)

    assert x == [2.0, 3.0, 4.0]
    assert y == [3.0, 4.0, 5.0]
