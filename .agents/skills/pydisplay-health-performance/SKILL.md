---
name: pydisplay-health-performance
description: Use this skill when implementing Pydisplay health monitoring, performance counters, GUI anti-freeze checks, queues, timers, bad-frame rates, bytes/s, plotting FPS, recorder queue metrics, or long-run stability checks.
---

# Pydisplay Health and Performance Skill

## Purpose

Use this skill for:

- link health monitor;
- parser statistics;
- serial statistics;
- recorder queue status;
- GUI FPS;
- plot refresh FPS;
- bad frame rate;
- bytes/s;
- anti-freeze design;
- long-running stability checks.

## Required Health Metrics

The health panel must display:

- bytes/s;
- valid frame rate;
- bad frame rate;
- bad frame count;
- bad frame ratio;
- resync count;
- serial input buffer bytes;
- parser buffer bytes;
- plotting FPS;
- recorder queue length;
- serial connection state;
- recording state.

Useful optional metrics:

- last valid frame age;
- reconnect count;
- write command count;
- write error count;
- dropped recording samples;
- replay state;
- CPU and memory usage via psutil.

## Refresh Frequency

Health display refresh:

```text
1–5 Hz
```

Do not update health QLabel text per sample or per frame.

Use a `QTimer` in GUI.

## Data Ownership

Health monitor aggregates stats from:

* SerialReader;
* Parser;
* Decoder;
* RecorderWorker;
* ReplayWorker;
* PlotPanel;
* AppController.

It should not own serial ports or files.

It should not directly parse protocol bytes.

It should not directly update GUI widgets unless it is the GUI-facing adapter.

## Recommended Model

Use a dataclass such as `HealthStats`.

Fields may include:

```text
timestamp_ns
bytes_per_second
valid_frames_per_second
bad_frames_per_second
bad_frame_count
bad_frame_ratio
resync_count
serial_input_waiting
parser_buffer_bytes
plot_fps
recorder_queue_size
serial_state
recording_state
last_error
```

## Queue Monitoring

Recorder queue must expose length.

If queue length grows continuously:

* show warning;
* log warning;
* avoid GUI freeze;
* do not silently drop samples unless explicitly designed and counted.

## Performance Rules

Target:

```text
data receive: 100 Hz or actual firmware rate
recording: 100 Hz full-rate
plotting: 10–30 FPS, default 20 FPS
health panel: 1–5 Hz
```

Forbidden:

* GUI thread reading serial;
* GUI thread writing files;
* GUI thread doing parser loops over large buffers;
* per-sample QLabel updates;
* per-sample DataFrame append;
* unbounded plot arrays;
* unbounded parser buffer;
* unbounded queue without warning.

## Long-Run Stability Checklist

During implementation, check:

* start/stop serial repeatedly;
* connect/disconnect HJ380 or fake port;
* start/stop recording repeatedly;
* pause/resume plotting repeatedly;
* start/stop replay repeatedly;
* run fake data for at least 30 minutes if practical;
* close GUI while workers are running;
* force invalid file path for recorder;
* force invalid replay file.

## Logging Requirements

Log important events to:

```text
logs/pydisplay.log
```

Log:

* app start;
* serial open/close;
* serial errors;
* reconnect attempts;
* parser error summary;
* recording start/stop;
* replay start/stop;
* command send result;
* queue warning;
* uncaught exceptions.

Do not log every frame.

## UI Warning Levels

Recommended status categories:

```text
正常
警告
错误
断开
记录中
回放中
暂停
```

Use clear Chinese messages.

Examples:

```text
串口已连接
串口打开失败：端口被占用
蓝牙可能断连：超过 2 秒未收到有效帧
记录队列过长，请降低绘图负载或检查磁盘速度
坏帧率较高，请检查蓝牙链路或协议设置
```

## Tests

Required tests where possible:

* HealthStats aggregation from fake counters;
* bad frame ratio calculation;
* rate calculation over time windows;
* queue warning threshold;
* plot FPS counter update;
* health panel can update from stats object without crashing.

## Completion Criteria

Before committing:

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_health_monitor.py
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check pydisplay/services pydisplay/gui/widgets/health_panel.py
```

Then commit:

```bash
git add .
git commit -m "add health monitoring and performance counters"
```