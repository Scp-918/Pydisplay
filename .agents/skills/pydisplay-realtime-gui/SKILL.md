---
name: pydisplay-realtime-gui
description: Use when implementing or reviewing the PySide6 + PyQtGraph Chinese GUI, real-time plots, widgets, layout, timers, curve visibility, pause plotting, FPS monitoring, and anti-freeze behavior for Pydisplay.
---

# Pydisplay Realtime GUI Skill

Use this skill when building the PySide6 + PyQtGraph GUI for the STM32G474 Pydisplay upper-computer application.

The GUI must be usable for long experiments, remain responsive, display Chinese labels correctly, and avoid unnecessary per-frame UI work.

## Scope

This skill covers:

- PySide6 main window.
- Widget layout.
- Chinese UI text.
- PyQtGraph real-time plotting.
- Plot ring buffers.
- Curve visibility.
- Pause plotting while continuing recording.
- GUI timers.
- Health status widgets.
- Long-running responsiveness.

This skill does not define protocol fields. Use `pydisplay-protocol-audit` for protocol details.

## Target files

Recommended files:

    src/pydisplay/app.py
    src/pydisplay/__main__.py
    src/pydisplay/gui/main_window.py
    src/pydisplay/gui/widgets_serial.py
    src/pydisplay/gui/widgets_control.py
    src/pydisplay/gui/widgets_record.py
    src/pydisplay/gui/widgets_health.py
    src/pydisplay/gui/widgets_replay.py
    src/pydisplay/gui/plots.py
    src/pydisplay/gui/styles.py
    src/pydisplay/core/ring_buffer.py
    src/pydisplay/core/models.py
    tests/test_gui_smoke.py

## Required GUI sections

The main window must include:

1. 串口连接区
   - 串口号
   - 波特率
   - 刷新串口
   - 打开串口
   - 关闭串口
   - 重连
   - 连接状态

2. 下位机控制区
   - PPG mode
   - LED 亮度
   - PPG 量程
   - 脉宽
   - IMU 量程
   - 发送控制命令
   - 命令状态提示

3. 记录设置区
   - 记录路径
   - 实验名或文件名前缀
   - 开始记录
   - 停止记录
   - 记录状态

4. 链路健康监控区
   - bytes/s
   - 有效帧率
   - 坏帧率
   - 坏帧比例
   - resync 次数
   - 串口缓冲区字节数
   - 解析缓冲区字节数
   - 绘图 FPS
   - 记录队列长度
   - 串口连接状态
   - 记录状态

5. 实时绘图区
   - 3 色 PPG 曲线
   - 3 轴加速度计
   - 3 轴陀螺仪
   - 4 路 Uh
   - 4 路 Uc
   - 2 路 UD

6. 回放区
   - 选择 raw_frames.bin
   - 选择 decoded.csv
   - 开始回放
   - 暂停
   - 继续
   - 停止
   - 倍速 / 慢速

## Layout guidance

Prefer a practical experiment-oriented layout:

- Left or top control panel:
  - serial
  - device control
  - recording
  - replay
  - health
- Main central area:
  - plot tabs or stacked plot panels
- Bottom status bar:
  - latest status
  - error message
  - recording path

Suggested plot grouping:

1. Tab: PPG
2. Tab: IMU
3. Tab: 电压
4. Tab: UD
5. Optional tab: 全部概览

Avoid trying to perfectly copy LabVIEW. Keep it clear, stable, and usable.

## Chinese UI requirements

1. All visible labels and buttons should be Chinese.
2. Use clear experimental language:
   - 打开串口
   - 关闭串口
   - 重连
   - 开始记录
   - 停止记录
   - 暂停绘图
   - 继续绘图
   - 开始回放
   - 停止回放
3. Avoid mojibake by using UTF-8 source files.
4. Do not hardcode paths with invalid escape sequences.

## Plot requirements

Use PyQtGraph.

Required curves:

- PPG_G
- PPG_R
- PPG_IR
- acc_x
- acc_y
- acc_z
- gyro_x
- gyro_y
- gyro_z
- uh_1
- uh_2
- uh_3
- uh_4
- uc_1
- uc_2
- uc_3
- uc_4
- ud_1
- ud_2

Each plot must have:

- Title.
- Axis labels.
- Unit when known.
- Legend or clear curve labels.
- Recent N seconds display window.
- Adaptive y-range or controlled auto-range.
- Visibility toggle for curves.

## Real-time plotting rules

1. Default refresh rate: 20 Hz.
2. Allowed range: 10–30 Hz.
3. Use QTimer for GUI refresh.
4. Do not update plot for every sample.
5. Do not recreate PlotDataItem each refresh.
6. Store incoming data in ring buffers.
7. On timer tick, update curve data arrays.
8. Plot only recent N seconds.
9. Allow plotting to pause while recording continues.
10. Hiding curves must reduce plotting work.

## Ring buffer requirements

Use a ring buffer or deque to store recent samples.

Recommended design:

- One time buffer.
- One value buffer per signal.
- Capacity = sample_rate * visible_seconds * margin.
- Example:
  - 100 Hz
  - 30 seconds
  - margin 1.5
  - capacity about 4500 samples

Do not store unlimited history in GUI memory.

## Pause plotting behavior

When user clicks 暂停绘图:

- GUI stops refreshing curves.
- Serial reading continues.
- Parser continues.
- Decoder continues.
- Recorder continues.
- Health metrics continue.

When user resumes:

- Plots show the latest recent window.
- Do not try to replay all skipped plot frames.

## Health panel refresh

Use a separate QTimer at 1–5 Hz.

Do not update health QLabel every frame.

Health panel should show stale status if no data arrives recently.

## Control widgets

Do not build command bytes inside GUI widgets.

Flow:

    GUI input
      -> validate parameter type and range
      -> call command builder
      -> send via serial worker
      -> display result

If parameter ranges are not confirmed by protocol audit, disable or mark controls as awaiting confirmation.

## Error display

The GUI should show user-friendly Chinese errors, for example:

- 串口不存在
- 串口被占用
- 蓝牙断连或设备拔出
- 校验失败数量过高
- 记录路径不可写
- 回放文件格式错误
- UD 分母接近 0

Use logs for technical details.

## GUI smoke test

Create a minimal pytest-qt smoke test if feasible:

- Start QApplication.
- Create MainWindow.
- Ensure window constructs.
- Ensure timers can start and stop.
- Ensure closing window does not crash.

Run:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_gui_smoke.py -q

If GUI tests are fragile on the current platform, document the limitation and provide a manual smoke test command:

    D:\Code\anaconda24\envs\Pydisplay_env\python -m pydisplay

## Manual test checklist

Before marking GUI complete, verify:

- [ ] App starts.
- [ ] Chinese labels display correctly.
- [ ] Window can close cleanly.
- [ ] Serial controls are visible.
- [ ] Device control controls are visible.
- [ ] Recording controls are visible.
- [ ] Health panel updates at low rate.
- [ ] Plots update using simulated data.
- [ ] Plot FPS is displayed.
- [ ] Pause plotting works.
- [ ] Recording can continue while plotting is paused.
- [ ] Curve visibility toggles work.
- [ ] No obvious freeze after 10 minutes of simulated 100 Hz data.

## Performance limits

Do not allow:

- Per-frame QLabel updates.
- Per-frame PlotDataItem creation.
- Full-history plot redraw.
- GUI thread file writes.
- GUI thread blocking serial reads.
- Unlimited list growth.

## Git rule

After GUI implementation and tests pass:

    git status
    git add src/pydisplay/gui src/pydisplay/app.py src/pydisplay/__main__.py tests
    git commit -m "add pyside6 pyqtgraph realtime gui"