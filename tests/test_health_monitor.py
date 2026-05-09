from __future__ import annotations

from pydisplay.protocol.models import ParserStats
from pydisplay.services.health_monitor import HealthMonitor


def test_health_monitor_calculates_rates_from_counter_deltas() -> None:
    monitor = HealthMonitor()
    monitor.snapshot(now_ns=0)

    stats = ParserStats(total_bytes=0, total_frames=12, valid_frames=10, bad_frames=2, resync_count=1, buffer_bytes=3)
    monitor.add_raw_bytes(100)
    monitor.update_parser_stats(stats)
    monitor.add_decoded_sample()
    monitor.add_plot_frame()
    monitor.set_queue_sizes(plot_queue_size=4, record_queue_size=5)

    snapshot = monitor.snapshot(now_ns=1_000_000_000)

    assert snapshot.bytes_per_second == 100
    assert snapshot.valid_frame_rate == 10
    assert snapshot.bad_frame_rate == 2
    assert snapshot.bad_frame_ratio == 2 / 12
    assert snapshot.resync_count == 1
    assert snapshot.parser_buffer_bytes == 3
    assert snapshot.decoded_sample_rate == 1
    assert snapshot.plot_fps == 1
    assert snapshot.plot_queue_size == 4
    assert snapshot.record_queue_size == 5


def test_health_monitor_keeps_status_and_errors() -> None:
    monitor = HealthMonitor()
    monitor.set_states(serial_state="CONNECTED", recording_state="RECORDING", replay_state="IDLE")
    monitor.set_last_error("checksum error")

    snapshot = monitor.snapshot(now_ns=1)

    assert snapshot.serial_state == "CONNECTED"
    assert snapshot.recording_state == "RECORDING"
    assert snapshot.replay_state == "IDLE"
    assert snapshot.last_error == "checksum error"
