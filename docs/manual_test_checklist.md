# Pydisplay Manual Test Checklist

## 1. Startup

- [ ] `conda activate Pydisplay_env`
- [ ] `cd D:\Desktop\STM32G474\Pydisplay`
- [ ] `python -m pydisplay`
- [ ] Double-click `Start_Pydisplay.bat`.
- [ ] GUI starts.
- [ ] Chinese text displays correctly.
- [ ] Left column is compact and leaves most width for plots.
- [ ] Left column order is serial, control, recording, health, replay.
- [ ] Replay panel can be reached by scrolling down below health.
- [ ] k value defaults to `24`.
- [ ] Control defaults are MultiLED / G-R-IR / LED `5,1,1` / PPG range `3` / pulse `3` / gyro `500 dps` / accel `2 g`.

## 2. Serial

- [ ] Click `刷新串口`.
- [ ] Select a COM port.
- [ ] Select baudrate `460800`.
- [ ] Click `打开串口`.
- [ ] Click `暂停接收` and confirm serial port remains open.
- [ ] Click `开始接收` and confirm data receiving resumes.
- [ ] Click `关闭串口`.
- [ ] Click `重连`.
- [ ] Unplug HJ380 and confirm GUI does not crash.
- [ ] Serial errors appear in status/health area and logs.

## 3. Protocol Health

- [ ] bytes/s updates.
- [ ] Valid frame rate updates.
- [ ] Bad frame rate updates.
- [ ] Bad frame count updates.
- [ ] Bad frame ratio updates.
- [ ] Lost frame count updates when firmware frame_seq skips.
- [ ] Lost frame ratio updates.
- [ ] Duplicate frame_seq count updates for repeated frame_seq.
- [ ] Sequence reset/reorder count updates for large frame_seq deltas.
- [ ] resync count updates.
- [ ] Serial buffer bytes update.
- [ ] Parser buffer bytes update.
- [ ] Valid frame rate, parser buffer, and latest error fields are wide enough and do not overlap adjacent rows.

## 4. Plots

- [ ] PPG_G / PPG_R / PPG_IR curves display.
- [ ] PPG displays three independent subplots, without a combined PPG plot.
- [ ] ACC_X / ACC_Y / ACC_Z curves display.
- [ ] GYRO_X / GYRO_Y / GYRO_Z curves display.
- [ ] Uh2 / Uh3 display independent subplots, without a combined Uh2/Uh3 plot.
- [ ] Uc2 / Uc3 display independent subplots, without a combined Uc2/Uc3 plot.
- [ ] UD1 / UD2 display independent subplots, without a combined UD plot.
- [ ] Uh/Uc channel 1/4 displays as two subplots: sensor 1 Uh/Uc and sensor 4 Uh/Uc.
- [ ] ACC and GYRO plots display in the bottom row.
- [ ] Plot group titles do not include `a/b/c/d/e/f/g` letter prefixes.
- [ ] PPG colors are green/red/purple, Uh2/Uh3 are red/orange, Uc2/Uc3 are blue/cyan, and UD1/UD2 are yellow/orange.
- [ ] Plot refresh defaults to about 20 Hz.
- [ ] `暂停绘图` stops curve refresh while data can still be recorded.
- [ ] `清空图表` clears visible curves without stopping serial receiving or recording.
- [ ] `X轴长度` changes the realtime visible time window.
- [ ] `X轴长度` defaults to `5 s`.
- [ ] Live or raw replay curves spread along the x-axis instead of appearing as a single vertical line.
- [ ] Curve visibility checkboxes are reachable only after scrolling down to the bottom of the plot area, leaving more first-screen space for plots.
- [ ] Curve visibility checkboxes hide/show curves.

## 5. Recording

- [ ] Set record path.
- [ ] Set experiment name.
- [ ] Click `开始记录`.
- [ ] Click `暂停接收` and confirm recording remains active.
- [ ] Click `关闭串口` while recording and confirm recording stops cleanly.
- [ ] Click `停止记录`.
- [ ] Session directory is created.
- [ ] `raw_frames.bin` is created.
- [ ] `decoded.csv` is created.
- [ ] `metadata.json` is created.
- [ ] `metadata.json` contains start and end time.
- [ ] `decoded.csv` contains `frame_seq`, `absolute_seq_u64`, `segment_id`, decoded signal fields, and `parser_valid`.
- [ ] `decoded.csv` does not contain `relative_time_s`, `timestamp_pc_ns`, `seq_gap`, `lost_before`, or `source`.

## 6. Replay

- [ ] Select a `raw_frames.bin` file.
- [ ] Start raw bin replay.
- [ ] Raw-bin replay reconstructs a stable 100 Hz frame clock from parsed raw frames.
- [ ] Raw-bin replay does not show false loss/error when a no-error recording is replayed.
- [ ] Raw-bin replay still runs raw frames through the parser/decoder path.
- [ ] Select a `decoded.csv` file.
- [ ] Start decoded csv replay.
- [ ] Pause replay.
- [ ] Click serial panel `暂停接收` during replay and confirm replay pauses.
- [ ] Click serial panel `开始接收` after that and confirm replay resumes.
- [ ] Resume replay.
- [ ] Test `0.25x`, `0.5x`, `1x`, `2x`, `5x`.
- [ ] Stop replay.
- [ ] Replay file format errors show a Chinese prompt.

## 7. No-Hardware

- [ ] `python -m pydisplay --smoke-test` prints `Pydisplay 上位机`.
- [ ] `pytest` passes without HJ380/HJ131 connected.
- [ ] Decoded CSV replay can exercise plots without serial hardware.
