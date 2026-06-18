from __future__ import annotations

from pydisplay.gui.plots.ring_buffer import SampleRingBuffer
from pydisplay.protocol.models import DecodedSample


def make_sample(index: int, t: float) -> DecodedSample:
    adc_fields = {f"adc_ch{channel}_slot{slot}": index + channel * 10 + slot for channel in range(1, 5) for slot in range(6)}
    return DecodedSample(
        timestamp_pc_ns=index,
        relative_time_s=t,
        frame_seq=None,
        sample_seq=index,
        **adc_fields,
    )


def test_ring_buffer_keeps_capacity() -> None:
    buffer = SampleRingBuffer(capacity=3)
    for index in range(5):
        buffer.append(make_sample(index, index * 0.01))

    assert len(buffer) == 3
    x, y = buffer.get_series("adc_ch1_slot0")
    assert x == [0.02, 0.03, 0.04]
    assert y == [12.0, 13.0, 14.0]


def test_ring_buffer_filters_recent_window() -> None:
    buffer = SampleRingBuffer(capacity=10)
    for index in range(5):
        buffer.append(make_sample(index, float(index)))

    x, y = buffer.get_series("adc_ch1_slot1", window_seconds=2.0)

    assert x == [2.0, 3.0, 4.0]
    assert y == [13.0, 14.0, 15.0]
