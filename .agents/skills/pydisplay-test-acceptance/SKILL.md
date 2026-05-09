---
name: pydisplay-test-acceptance
description: Use when validating Pydisplay implementation quality, writing pytest tests, running lint/format checks, creating smoke tests, reviewing acceptance criteria, and deciding whether the STM32G474 Python GUI is ready for hardware experiments.
---

# Pydisplay Test and Acceptance Skill

Use this skill when checking whether the Pydisplay Python GUI implementation is correct, stable, and ready for experiments.

This skill should be used after each development phase and before each git commit.

## Scope

This skill covers:

- Phase validation.
- Unit tests.
- Integration tests.
- GUI smoke tests.
- Simulated 100 Hz data tests.
- Recorder/replay tests.
- Lint and formatting.
- Manual acceptance checklist.
- Stop conditions.

## Standard commands

Use the configured Python interpreter:

    D:\Code\anaconda24\envs\Pydisplay_env\python

Basic environment check:

    D:\Code\anaconda24\envs\Pydisplay_env\python --version
    D:\Code\anaconda24\envs\Pydisplay_env\python -c "import PySide6, pyqtgraph, serial, numpy, pandas; print('ok')"

Test command:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest -q

Lint and format commands:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
    D:\Code\anaconda24\envs\Pydisplay_env\python -m black .
    D:\Code\anaconda24\envs\Pydisplay_env\python -m isort .

Optional type check:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m mypy src

Manual GUI run:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pydisplay

## Required test categories

### Protocol tests

Files:

    tests/test_parser.py
    tests/test_decoder.py
    tests/test_commands.py

Must cover:

- Valid frame.
- Multiple concatenated frames.
- Noise before header.
- Partial frames across chunks.
- Bad tail.
- Bad checksum.
- Resync after corruption.
- Parser buffer size.
- Decoder scaling.
- UD denominator protection.
- Command parameter validation.
- Command binary format.

If protocol is not confirmed, tests should only cover generic parser skeleton and documented placeholders. Do not hardcode guessed protocol fields.

### Serial tests

Files:

    tests/test_serial_reader.py

Must cover:

- Open and close with fake serial.
- Read bytes.
- Timeout.
- Device removal exception.
- Port occupied exception.
- Write when disconnected.
- Write failure.
- Clean stop.

### Recorder tests

Files:

    tests/test_recorder.py

Must cover:

- Creates session directory.
- Writes raw_frames.bin.
- Writes decoded.csv.
- Writes metadata.json.
- Batch writing.
- Safe stop.
- Error on unwritable path.
- Metadata contains required fields.

### Replay tests

Files:

    tests/test_replay.py

Must cover:

- Replay raw_frames.bin.
- Replay decoded.csv.
- Pause.
- Resume.
- Stop.
- Speed factor.
- Malformed file.
- Version mismatch.

### GUI smoke tests

Files:

    tests/test_gui_smoke.py

Must cover when feasible:

- QApplication starts.
- MainWindow constructs.
- MainWindow closes.
- Timers start and stop.
- Simulated data can update plot buffers without crash.

If pytest-qt is unstable on the current Windows setup, document a manual GUI smoke test instead of hiding failure.

## Simulated 100 Hz test

Create or maintain a simulation mode.

Purpose:

- Test UI without hardware.
- Test plotting.
- Test recording.
- Test replay.

Minimum simulated signals:

- PPG_G, PPG_R, PPG_IR.
- acc_x, acc_y, acc_z.
- gyro_x, gyro_y, gyro_z.
- uh_1..uh_4.
- uc_1..uc_4.
- ud_1..ud_2.

Rules:

- Simulation must not replace protocol parser validation.
- Simulation data should be clearly marked as simulated.
- Recorder metadata should indicate simulation mode if recording simulated data.

## Phase acceptance

### Phase 0: Project and protocol audit

Accept only if:

- `docs/protocol_analysis.md` exists.
- Confirmed and unknown protocol fields are listed.
- Evidence paths and line numbers are included where possible.
- Stop conditions are reported if protocol is incomplete.

### Phase 1: Parser

Accept only if:

- Parser state machine exists.
- Parser tests pass.
- Bad frames and resync are counted.
- Parser is independent from GUI.

### Phase 2: Decoder and commands

Accept only if:

- Decoder uses confirmed scaling.
- UD calculation is protected.
- Command builder uses confirmed command format.
- Tests pass.
- Unknown command fields are not guessed.

### Phase 3: Serial

Accept only if:

- Serial open/close/reconnect exists.
- Exceptions are handled.
- GUI cannot freeze due to serial read.
- Fake serial tests pass.

### Phase 4: Recorder

Accept only if:

- Raw, CSV, metadata are written.
- Writer runs outside GUI thread.
- No per-frame flush.
- No pandas append per frame.
- Recorder tests pass.

### Phase 5: GUI

Accept only if:

- App starts.
- Chinese UI displays.
- Main sections exist.
- GUI closes cleanly.
- Timers are used correctly.

### Phase 6: Realtime plotting

Accept only if:

- 20 Hz default plot refresh.
- Recent N seconds visible.
- Pause plotting works.
- Recording continues while plotting is paused.
- Curve visibility works.
- Simulated 100 Hz data runs without obvious freeze.

### Phase 7: Replay

Accept only if:

- Raw replay works.
- CSV replay works.
- Pause/resume/stop works.
- Speed control works.
- Replay does not block GUI.

### Phase 8: Final integration

Accept only if:

- Full test suite passes or failures are explained.
- README exists.
- Data format doc exists.
- User guide exists.
- Git status is clean after commit.

## Performance acceptance

Check:

- GUI refresh: 10–30 FPS.
- Default GUI refresh: 20 FPS.
- Health panel refresh: 1–5 Hz.
- Recording: 100 Hz full data.
- No GUI thread file writes.
- No GUI thread blocking serial reads.
- No unbounded GUI data history.
- Queue lengths visible.
- Queue buildup warning visible.

## Manual hardware checklist

When hardware is available:

- [ ] HJ380 appears as serial port.
- [ ] Port can open.
- [ ] Data bytes/s is nonzero.
- [ ] Valid frame rate is near expected sampling rate.
- [ ] Bad frame ratio is reasonable or explained.
- [ ] Unplug HJ380 does not freeze GUI.
- [ ] Reconnect works.
- [ ] Start recording.
- [ ] Stop recording.
- [ ] Check raw_frames.bin.
- [ ] Check decoded.csv.
- [ ] Check metadata.json.
- [ ] Send each supported command.
- [ ] Verify firmware response or observable behavior.
- [ ] Run at least 10 minutes.

## Stop and report conditions

Stop and report if:

1. Protocol is incomplete.
2. Tests require guessed values.
3. GUI freezes under simulated data.
4. Recorder loses data silently.
5. Serial exceptions crash the app.
6. raw_frames.bin cannot be replayed.
7. decoded.csv schema is inconsistent with metadata.
8. command format is unknown.
9. command parameter range is unknown.
10. New dependency is required.

Use report format:

    ## 验收暂停原因

    ## 已通过项目

    ## 失败项目

    ## 风险

    ## 建议下一步

## Git rule

Before each commit:

    git status
    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest -q
    D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .

If tests pass:

    git add .
    git commit -m "describe completed phase"

If tests fail:

- Do not commit broken code unless user explicitly asks for WIP commit.
- Report failure summary.
- Fix small local issues when possible.