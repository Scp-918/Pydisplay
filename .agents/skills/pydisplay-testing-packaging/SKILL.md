---
name: pydisplay-testing-packaging
description: Use this skill when setting up Pydisplay tests, pytest-qt GUI tests, ruff/black/isort/mypy checks, fake data tests, CI-like local validation, PyInstaller packaging, run scripts, or final acceptance verification.
---

# Pydisplay Testing and Packaging Skill

## Purpose

Use this skill for:

- test strategy;
- pytest;
- pytest-qt;
- parser tests;
- decoder tests;
- recorder tests;
- replay tests;
- GUI smoke tests;
- fake data generation;
- formatting;
- linting;
- type checking;
- PyInstaller packaging;
- final acceptance checks.

## Environment

Use the specified interpreter:

```text
D:\Code\anaconda24\envs\Pydisplay_env\python
```

Do not assume another Python environment.

## Environment Check

Before running tests or packaging, check:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python --version
D:\Code\anaconda24\envs\Pydisplay_env\python -c "import PySide6, pyqtgraph, serial, numpy, pandas, scipy, psutil, yaml, pytest; print('ok')"
```

If imports fail, stop and report missing packages.

## Recommended Test Layout

```text
tests/
  conftest.py
  test_parser.py
  test_decoder.py
  test_command.py
  test_recorder.py
  test_replay.py
  test_health_monitor.py
  test_gui_smoke.py
```

## Required Test Categories

### Parser tests

Cover:

* full frame;
* split frame;
* sticky frames;
* garbage before header;
* bad frame recovery;
* checksum failure;
* tail failure;
* empty input;
* long noise recovery.

### Decoder tests

Cover:

* field decoding;
* scaling;
* signedness;
* byte order;
* k value effect;
* UD denominator near zero.

### Command tests

Cover:

* valid command;
* invalid mode;
* out-of-range LED brightness;
* invalid PPG range;
* invalid pulse width;
* invalid IMU range;
* checksum if applicable.

### Recorder tests

Cover:

* raw_frames.bin write/read;
* decoded.csv write/read;
* metadata required keys;
* start/stop lifecycle;
* invalid output path.

### Replay tests

Cover:

* raw replay;
* csv replay;
* pause/continue if feasible;
* invalid raw magic;
* missing csv fields.

### GUI smoke tests

Use pytest-qt.

Cover:

* main window instantiates;
* panels instantiate;
* plot panel accepts fake samples;
* pause plotting state change;
* health panel update;
* window close does not leave workers running.

Do not require physical hardware for automated tests.

## Local Commands

Recommended scripts:

```text
scripts/run_app.bat
scripts/run_tests.bat
scripts/format.bat
scripts/lint.bat
scripts/package_pyinstaller.bat
scripts/make_fake_data.py
scripts/run_fake_device.py
```

## Quality Commands

Use:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m black --check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m isort --check-only .
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest
```

Optional:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m mypy pydisplay
```

If mypy reports PySide6 dynamic type issues, document them rather than hiding real logic errors.

## Formatting

Use:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m black .
D:\Code\anaconda24\envs\Pydisplay_env\python -m isort .
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check . --fix
```

Do not reformat unrelated external firmware files.

## PyInstaller Packaging

Prepare but do not over-optimize early.

Expected script:

```text
scripts/package_pyinstaller.bat
```

Package target:

```text
dist/Pydisplay/
```

Packaging should include:

* PySide6;
* pyqtgraph;
* required metadata;
* default config if any;
* README or user manual.

Before packaging, make sure:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pydisplay
```

can launch.

## Fake Data

Provide fake data for tests and manual GUI debugging.

Fake data can be:

* decoded sample generator;
* decoded.csv sample;
* raw_frames.bin sample after protocol is confirmed;
* fake device script.

Do not generate fake raw protocol frames before the real protocol is confirmed.

## Git Commit Rule

After each meaningful stage:

```bash
git status
git add .
git commit -m "clear stage message"
```

Recommended stage commits:

```text
init project structure and tooling
add protocol analysis report
implement parser tests
implement decoder tests
implement serial worker tests
implement recorder replay tests
implement gui smoke tests
add packaging scripts
```

## Final Acceptance Checklist

Before reporting completion:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m black --check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m isort --check-only .
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest
```

Then manually verify:

* GUI launches;
* serial panel works without hardware;
* fake/replay mode works;
* plotting updates;
* recording creates raw_frames.bin, decoded.csv, metadata.json;
* replay reads generated files;
* closing GUI stops workers;
* no GUI freeze during fake 100 Hz data.

## Report Format

When finished, Codex should report:

```markdown
## Completed

- ...

## Tests run

- ...

## Files changed

- ...

## Known limitations

- ...

## Manual checks needed

- ...
```

If anything failed, include exact command and error summary.