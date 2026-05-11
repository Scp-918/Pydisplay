"""Firmware frame sequence tracking.

The STM32 data frame carries a uint16 little-endian source sequence number.
This module turns that wrapping counter into per-sample gap metadata and
lightweight cumulative counters. It is deliberately independent of Qt,
serial I/O, recorder files, and decoder field parsing.
"""

from __future__ import annotations

from dataclasses import dataclass


UINT16_MASK = 0xFFFF
RESET_OR_REORDER_THRESHOLD = 32768


@dataclass(frozen=True, slots=True)
class SequenceResult:
    frame_seq: int | None
    absolute_seq_u64: int | None
    seq_gap: int
    lost_before: int
    segment_id: int
    is_duplicate: bool = False
    is_reset: bool = False


class FrameSequenceTracker:
    """Track uint16 firmware frame sequence continuity.

    `absolute_seq_u64` starts at 0 for the first sequenced frame in a stream.
    Normal gaps advance it by the uint16 delta, so it does not wrap at 65535.
    A large delta is treated as reset/reorder, not as massive packet loss; the
    tracker starts a new segment and advances the absolute counter by one to
    keep it monotonic across the whole run.
    """

    def __init__(self) -> None:
        self.prev_seq: int | None = None
        self.absolute_seq_u64: int | None = None
        self.segment_id = 0
        self.lost_frames = 0
        self.seq_checked_frames = 0
        self.duplicate_seq_count = 0
        self.seq_reset_count = 0

    def update(self, frame_seq: int | None) -> SequenceResult:
        if frame_seq is None:
            return SequenceResult(
                frame_seq=None,
                absolute_seq_u64=None,
                seq_gap=0,
                lost_before=0,
                segment_id=self.segment_id,
            )

        curr_seq = frame_seq & UINT16_MASK
        if self.prev_seq is None:
            self.prev_seq = curr_seq
            self.absolute_seq_u64 = 0
            return SequenceResult(
                frame_seq=curr_seq,
                absolute_seq_u64=0,
                seq_gap=0,
                lost_before=0,
                segment_id=self.segment_id,
            )

        delta = (curr_seq - self.prev_seq) & UINT16_MASK
        self.seq_checked_frames += 1

        if delta == 0:
            self.duplicate_seq_count += 1
            return SequenceResult(
                frame_seq=curr_seq,
                absolute_seq_u64=self.absolute_seq_u64,
                seq_gap=0,
                lost_before=0,
                segment_id=self.segment_id,
                is_duplicate=True,
            )

        if 1 < delta < RESET_OR_REORDER_THRESHOLD:
            lost_before = delta - 1
            self.lost_frames += lost_before
            self.absolute_seq_u64 = (self.absolute_seq_u64 or 0) + delta
            self.prev_seq = curr_seq
            return SequenceResult(
                frame_seq=curr_seq,
                absolute_seq_u64=self.absolute_seq_u64,
                seq_gap=delta,
                lost_before=lost_before,
                segment_id=self.segment_id,
            )

        if delta >= RESET_OR_REORDER_THRESHOLD:
            self.seq_reset_count += 1
            self.segment_id += 1
            self.absolute_seq_u64 = (self.absolute_seq_u64 or 0) + 1
            self.prev_seq = curr_seq
            return SequenceResult(
                frame_seq=curr_seq,
                absolute_seq_u64=self.absolute_seq_u64,
                seq_gap=delta,
                lost_before=0,
                segment_id=self.segment_id,
                is_reset=True,
            )

        self.absolute_seq_u64 = (self.absolute_seq_u64 or 0) + 1
        self.prev_seq = curr_seq
        return SequenceResult(
            frame_seq=curr_seq,
            absolute_seq_u64=self.absolute_seq_u64,
            seq_gap=1,
            lost_before=0,
            segment_id=self.segment_id,
        )
