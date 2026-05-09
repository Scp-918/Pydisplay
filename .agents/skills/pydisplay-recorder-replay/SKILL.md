---
name: pydisplay-recorder-replay
description: Use when implementing or modifying Pydisplay raw_frames.bin recording, decoded.csv writing, metadata.json generation, RecorderWorker batching, raw-bin replay, decoded-csv replay, and replay controls.
---

# Skill: pydisplay-recorder-replay

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 实现 `raw_frames.bin` 记录；
- 实现 `decoded.csv` 记录；
- 实现 `metadata.json`；
- 实现记录线程；
- 实现 raw bin 回放；
- 实现 decoded csv 回放；
- 实现无硬件 UI / 算法调试；
- 修改 `pydisplay/recorder/` 或 `pydisplay/replay/`。

---

## 2. 核心原则

1. `raw_frames.bin` 必须记录；
2. `decoded.csv` 必须记录；
3. `metadata.json` 必须记录；
4. GUI 主线程不得写文件；
5. 不要每帧 flush；
6. 不要每帧 pandas append；
7. 记录必须支持 100 Hz 全量数据；
8. 绘图可以降刷新率，记录不能降采样；
9. 回放应复用真实数据流架构。

---

## 3. 推荐文件结构

```text
pydisplay/
  recorder/
    __init__.py
    recorder_worker.py
    raw_bin_format.py
    csv_writer.py
    metadata.py

  replay/
    __init__.py
    replay_worker.py
    raw_bin_reader.py
    decoded_csv_reader.py

tests/
  test_raw_bin_format.py
  test_replay.py
  test_metadata.py
```

---

## 4. 记录目录设计

默认每次记录生成一个 session 目录：

```text
records/
  20260510_013000_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

如果用户在 GUI 中指定路径和文件名前缀，则使用用户指定内容。

目录创建失败要提示：

```text
路径不存在
没有写权限
磁盘空间不足
```

---

## 5. `raw_frames.bin` 设计

### 5.1 记录目的

`raw_frames.bin` 用于复盘协议问题，因此必须尽量保存原始信息。

应至少保存：

1. 原始 bytes 或原始帧；
2. PC 时间戳；
3. record type；
4. payload 长度；
5. payload bytes。

---

### 5.2 推荐二进制格式

文件头：

```text
magic: b"PYDISPRAW"
format_version: uint16
created_unix_ns: uint64
header_length: uint32
reserved: bytes
```

记录项：

```text
record_type: uint8
timestamp_ns: uint64
payload_length: uint32
payload: bytes[payload_length]
```

record_type：

```text
1 = raw_serial_chunk
2 = valid_raw_frame
3 = bad_frame_fragment
```

字节序建议：

```text
little-endian
```

但 raw bin 文件格式的字节序应在 `docs/data_format.md` 中明确。

---

### 5.3 raw chunk 与 raw frame

推荐同时支持：

```text
raw_serial_chunk
valid_raw_frame
bad_frame_fragment
```

最低要求：

```text
必须保存 raw_serial_chunk 或 valid_raw_frame 中至少一种。
```

更推荐保存 raw serial chunk，因为这样最适合复盘 parser 问题。

---

## 6. `decoded.csv` 设计

CSV 用于 Excel / Origin / MATLAB 分析。

推荐字段：

```text
relative_time_s
timestamp_pc_ns
frame_seq
sample_seq
PPG_G
PPG_R
PPG_IR
ACC_X
ACC_Y
ACC_Z
GYRO_X
GYRO_Y
GYRO_Z
Uh1
Uh2
Uh3
Uh4
Uc1
Uc2
Uc3
Uc4
UD1
UD2
parser_valid
source
```

字段名应与 `DecodedSample` 保持一致。

如果协议分析报告中字段名不同，以协议分析报告为准。

---

## 7. `metadata.json` 设计

必须包含：

```json
{
  "software": {
    "name": "Pydisplay",
    "version": "0.1.0"
  },
  "firmware": {
    "repo": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
    "branch": "Single",
    "commit": null,
    "protocol_version": null
  },
  "session": {
    "record_start_time": null,
    "record_end_time": null,
    "record_path": null
  },
  "serial": {
    "port": null,
    "baudrate": null,
    "device": "HJ380"
  },
  "bluetooth": {
    "tx_module": "HJ131",
    "rx_module": "HJ380"
  },
  "decode": {
    "k": null,
    "ud_formula": "UD = (Uh - Uc) / (k - Uc)"
  },
  "control_parameters": {
    "ppg_mode": null,
    "led_brightness": null,
    "ppg_range": null,
    "pulse_width": null,
    "imu_range": null
  },
  "protocol": {
    "frame_header": "AA BB",
    "frame_tail": "CC",
    "frame_length": null,
    "payload_length": null,
    "byte_order": null,
    "checksum": null,
    "field_layout": []
  },
  "csv_fields": {}
}
```

实际字段应根据协议分析更新。

---

## 8. RecorderWorker 设计

`RecorderWorker` 独立运行，接收 queue 数据并批量写入。

### 8.1 输入队列

建议分两个队列或一个统一队列：

```text
raw_queue
decoded_queue
```

或：

```python
RecordEvent:
    kind: Literal["raw", "decoded", "bad_frame"]
    timestamp_ns: int
    payload: bytes | DecodedSample
```

### 8.2 批量写入策略

要求：

1. 不每帧 flush；
2. 不每帧 open / close；
3. 不使用 pandas append；
4. 批量写 csv rows；
5. 定期 flush，例如每 1 秒或每 N 条；
6. 停止记录时必须 final flush；
7. 关闭文件句柄；
8. 写入异常必须上报 GUI。

---

## 9. 记录状态

推荐状态：

```python
class RecordingState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RECORDING = "recording"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
```

GUI 显示中文：

```text
未记录
正在启动记录
记录中
正在停止记录
记录已停止
记录异常
```

---

## 10. 记录线程禁止事项

禁止：

1. GUI 主线程写文件；
2. 每帧 flush；
3. 每帧 pandas append；
4. 在记录线程中操作 GUI；
5. 队列无限增长却不报警；
6. 写入异常静默吞掉；
7. 停止记录时不写结束时间；
8. metadata 缺失关键实验参数。

---

## 11. raw bin 回放设计

### 11.1 回放目标

从 `raw_frames.bin` 回放原始数据，尽量复用真实链路：

```text
raw_frames.bin
  ↓
ReplayWorker
  ↓
Parser
  ↓
Decoder
  ↓
GUI Plot + HealthMonitor
```

### 11.2 回放要求

1. 支持读取文件头；
2. 支持读取 record；
3. 支持按 timestamp 模拟原节奏；
4. 支持速度倍率；
5. 支持暂停；
6. 支持继续；
7. 支持停止；
8. 支持回放进度；
9. 文件格式错误时有中文提示。

### 11.3 速度倍率

建议支持：

```text
0.25x
0.5x
1x
2x
5x
```

节奏计算：

```text
sleep_time = original_delta_time / speed
```

注意避免 sleep 负数。

---

## 12. decoded csv 回放设计

### 12.1 回放目标

从 decoded.csv 直接恢复 `DecodedSample`：

```text
decoded.csv
  ↓
ReplayWorker
  ↓
DecodedSample
  ↓
GUI Plot + HealthMonitor
```

### 12.2 回放要求

1. 检查必需字段；
2. 支持 100 Hz 默认节奏；
3. 如果 CSV 有 `relative_time_s`，优先使用真实时间差；
4. 支持速度倍率；
5. 支持暂停 / 继续 / 停止；
6. 不经过 parser；
7. 用于无硬件调试 UI 和算法。

---

## 13. ReplayWorker 状态

推荐状态：

```python
class ReplayState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"
    FINISHED = "finished"
    ERROR = "error"
```

GUI 显示：

```text
未回放
正在加载
回放中
回放暂停
正在停止
回放完成
回放异常
```

---

## 14. 回放与记录关系

需要明确处理：

1. 回放时是否允许再次记录；
2. 如果允许，metadata 中 source 应写 `replay_raw_bin` 或 `replay_decoded_csv`；
3. 如果不允许，GUI 中禁用记录按钮；
4. 不要让真实串口和回放同时向同一 pipeline 输入，除非明确支持并标注 source。

推荐初版：

```text
实时串口模式和回放模式互斥。
```

---

## 15. 文档要求

必须更新：

```text
docs/data_format.md
```

说明：

1. raw bin 文件头；
2. raw bin record 格式；
3. decoded csv 字段；
4. metadata 字段；
5. 版本号；
6. 兼容性说明。

---

## 16. 测试要求

### 16.1 raw bin 测试

测试：

1. 写文件头；
2. 写 raw record；
3. 写 decoded record 可选；
4. 读回一致；
5. 文件截断时有错误；
6. magic 错误时有错误；
7. version 不兼容时有错误。

### 16.2 csv 测试

测试：

1. header 正确；
2. 数值写入正确；
3. NaN 可处理；
4. Excel 兼容；
5. 字段缺失时报错。

### 16.3 replay 测试

测试：

1. raw bin 回放能产生 raw chunk；
2. decoded csv 回放能产生 DecodedSample；
3. 暂停 / 继续；
4. 倍速；
5. 文件错误处理。

---

## 17. 推荐开发步骤

### Step 1：实现 raw bin format

先完成读写二进制格式和测试。

### Step 2：实现 csv writer

使用 csv 标准库或批量文本写入。

### Step 3：实现 metadata writer

记录开始时创建基础 metadata，停止时写入结束时间。

### Step 4：实现 RecorderWorker

接入 queue，批量写入。

### Step 5：接入 GUI recorder panel

开始 / 停止记录。

### Step 6：实现 raw bin reader

支持回放。

### Step 7：实现 decoded csv reader

支持回放。

### Step 8：实现 ReplayWorker

接入 GUI replay panel。

### Step 9：更新 docs/data_format.md

---

## 18. 验收标准

1. 开始记录后生成 session 目录；
2. 包含 `raw_frames.bin`；
3. 包含 `decoded.csv`；
4. 包含 `metadata.json`；
5. 100 Hz 数据可全量记录；
6. GUI 主线程不写文件；
7. 记录过程中 GUI 不明显卡顿；
8. 停止记录后 metadata 有结束时间；
9. raw bin 可回放；
10. decoded csv 可回放；
11. 回放支持暂停 / 继续 / 倍速；
12. 文件错误有明确提示。

完成后建议：

```bash
pytest tests/test_raw_bin_format.py tests/test_replay.py tests/test_metadata.py
git status
git diff
git add pydisplay/recorder pydisplay/replay tests docs/data_format.md
git commit -m "feat: implement recorder and replay pipeline"
```