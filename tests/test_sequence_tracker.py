from __future__ import annotations

from pydisplay.protocol.sequence import FrameSequenceTracker


def test_sequence_tracker_treats_uint16_wrap_as_continuous() -> None:
    tracker = FrameSequenceTracker()

    first = tracker.update(65535)
    wrapped = tracker.update(0)

    assert first.absolute_seq_u64 == 0
    assert first.seq_gap == 0
    assert wrapped.seq_gap == 1
    assert wrapped.lost_before == 0
    assert wrapped.absolute_seq_u64 == 1
    assert tracker.lost_frames == 0


def test_sequence_tracker_counts_missing_frames_before_current_sample() -> None:
    tracker = FrameSequenceTracker()

    tracker.update(100)
    result = tracker.update(103)

    assert result.seq_gap == 3
    assert result.lost_before == 2
    assert result.absolute_seq_u64 == 3
    assert tracker.lost_frames == 2


def test_sequence_tracker_counts_duplicates_without_lost_frames() -> None:
    tracker = FrameSequenceTracker()

    tracker.update(42)
    result = tracker.update(42)

    assert result.seq_gap == 0
    assert result.lost_before == 0
    assert result.absolute_seq_u64 == 0
    assert result.is_duplicate is True
    assert tracker.lost_frames == 0
    assert tracker.duplicate_seq_count == 1


def test_sequence_tracker_starts_new_segment_on_large_reverse_or_reset_delta() -> None:
    tracker = FrameSequenceTracker()

    tracker.update(100)
    result = tracker.update(40000)

    assert result.seq_gap == ((40000 - 100) & 0xFFFF)
    assert result.lost_before == 0
    assert result.segment_id == 1
    assert result.absolute_seq_u64 == 1
    assert result.is_reset is True
    assert tracker.lost_frames == 0
    assert tracker.seq_reset_count == 1
