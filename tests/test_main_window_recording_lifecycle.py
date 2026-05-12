from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pydisplay.gui.main_window import MainWindow
from pydisplay.io.serial_manager import SerialState
from pydisplay.recorder.recorder_worker import RecordingState
from pydisplay.replay.replay_worker import ReplayState


class RecorderFake:
    def __init__(self, state: RecordingState) -> None:
        self.state = state
        self.stop_count = 0

    def stop(self) -> None:
        self.stop_count += 1
        self.state = RecordingState.STOPPED


class RecorderPanelFake:
    def __init__(self) -> None:
        self.statuses: list[str] = []

    def set_status(self, text: str) -> None:
        self.statuses.append(text)


class HealthFake:
    def __init__(self) -> None:
        self.states: list[dict[str, str]] = []
        self.last_error: str | None = None

    def set_states(self, **kwargs: str) -> None:
        self.states.append(kwargs)

    def set_last_error(self, message: str | None) -> None:
        self.last_error = message


class SerialManagerFake:
    def __init__(self, *, connected: bool = True) -> None:
        self.state = SerialState.CONNECTED
        self.status = SimpleNamespace(receive_paused=False)
        self.close_count = 0
        self.pause_count = 0
        self._connected = connected

    def close(self) -> None:
        self.close_count += 1
        self.state = SerialState.DISCONNECTED
        self.status.receive_paused = True

    def is_connected(self) -> bool:
        return self._connected

    def pause_receiving(self) -> None:
        self.pause_count += 1
        self.status.receive_paused = True


class ReplayWorkerFake:
    def __init__(self, state: ReplayState) -> None:
        self.state = state
        self.pause_count = 0
        self.resume_count = 0

    def pause(self) -> None:
        self.pause_count += 1
        self.state = ReplayState.PAUSED

    def resume(self) -> None:
        self.resume_count += 1
        self.state = ReplayState.PLAYING


class WindowStub:
    _stop_recording = MainWindow._stop_recording
    _serial_state_text = MainWindow._serial_state_text
    _pause_replay = MainWindow._pause_replay
    _resume_replay = MainWindow._resume_replay

    def __init__(
        self,
        recorder_state: RecordingState,
        *,
        serial_connected: bool = True,
        replay_state: ReplayState | None = None,
    ) -> None:
        self.recorder = RecorderFake(recorder_state)
        self.recorder_panel = RecorderPanelFake()
        self.health = HealthFake()
        self.serial_manager = SerialManagerFake(connected=serial_connected)
        self.replay_worker = ReplayWorkerFake(replay_state) if replay_state is not None else None


def make_window_stub(
    recorder_state: RecordingState,
    *,
    serial_connected: bool = True,
    replay_state: ReplayState | None = None,
) -> WindowStub:
    return WindowStub(recorder_state, serial_connected=serial_connected, replay_state=replay_state)


def test_close_serial_stops_active_recording_and_updates_state() -> None:
    window = make_window_stub(RecordingState.RECORDING)

    MainWindow._close_serial(window)

    assert window.serial_manager.close_count == 1
    assert window.recorder.stop_count == 1
    assert window.recorder_panel.statuses[-1]
    assert any(state.get("recording_state") == "STOPPED" for state in window.health.states)


def test_close_serial_does_not_stop_when_recorder_is_not_recording() -> None:
    window = make_window_stub(RecordingState.STOPPED)

    MainWindow._close_serial(window)

    assert window.serial_manager.close_count == 1
    assert window.recorder.stop_count == 0


def test_pause_receiving_does_not_stop_recording() -> None:
    window = make_window_stub(RecordingState.RECORDING)

    MainWindow._pause_receiving(window)

    assert window.serial_manager.pause_count == 1
    assert window.recorder.stop_count == 0
    assert not any("recording_state" in state for state in window.health.states)


def test_pause_receiving_also_pauses_active_replay_without_serial() -> None:
    window = make_window_stub(
        RecordingState.STOPPED,
        serial_connected=False,
        replay_state=ReplayState.PLAYING,
    )

    MainWindow._pause_receiving(window)

    assert window.replay_worker is not None
    assert window.replay_worker.pause_count == 1
    assert window.replay_worker.state == ReplayState.PAUSED
    assert any(state.get("replay_state") == "PAUSED" for state in window.health.states)


def test_start_receiving_resumes_paused_replay_without_serial() -> None:
    window = make_window_stub(
        RecordingState.STOPPED,
        serial_connected=False,
        replay_state=ReplayState.PAUSED,
    )

    MainWindow._start_receiving(window)

    assert window.replay_worker is not None
    assert window.replay_worker.resume_count == 1
    assert window.replay_worker.state == ReplayState.PLAYING
    assert any(state.get("replay_state") == "PLAYING" for state in window.health.states)
