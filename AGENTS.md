# AGENTS.md

## 0. 项目定位

本项目是在现有文件夹 `D:\Desktop\STM32G474\Pydisplay` 下开发一个 Python GUI 上位机子项目，用于 STM32G474 下位机实验数据的接收、协议解析、数据解算、实时绘图、控制命令发送、数据记录、链路健康监控和离线回放。

上位机技术栈：

- Python 3.11
- PySide6
- PyQtGraph
- pyserial
- numpy
- pandas
- scipy
- psutil
- pyyaml
- pytest / pytest-qt / pytest-cov / pytest-timeout
- ruff / black / mypy / isort
- pyinstaller

指定 Python 解释器：

```text
D:\Code\anaconda24\envs\Pydisplay_env\python
```

开发目录：

```text
D:\Desktop\STM32G474\Pydisplay
```

下位机信息：

* MCU：STM32G474
* 固件仓库：`https://github.com/Scp-918/PulseTIMR2/tree/Single`
* 构建系统：CMake
* 下位机发送端：HJ131 蓝牙模块
* 上位机接收端：HJ380 蓝牙模块
* 传感器手册：固件工程中的 `sensorlist` 部分

必须注意：

> 本项目的通信协议、字段顺序、缩放系数、控制命令格式必须从固件源码、协议定义文件、sensorlist 或相关文档中确认。禁止凭经验臆造协议。

当前已知协议事实：

* 帧头为：`0xAA 0xBB`
* 帧尾为：`0xCC`

除上述已知事实外，其他协议细节均必须从源码或文档确认后再实现。

---

## A. Codex 的任务目标与计划

### A.1 总目标

在 `D:\Desktop\STM32G474\Pydisplay` 下实现一个可运行、可测试、可长期实验使用的 Python GUI 上位机，完成：

1. 串口选择、打开、关闭、重连；
2. HJ380 蓝牙串口数据接收；
3. 按 STM32 固件真实协议进行帧解析；
4. PPG、IMU、电压、UD 信号解算；
5. PySide6 + PyQtGraph 实时绘图；
6. 控制命令发送；
7. raw frame 与 decoded CSV 全量记录；
8. metadata.json 自动生成；
9. 链路健康监控；
10. raw_frames.bin / decoded.csv 回放；
11. 测试阶段的模拟数据源或虚拟串口测试支持；
12. 单元测试、基础集成测试、GUI 基础测试；
13. 打包准备。

### A.2 总体开发策略

不得一次性盲目重写全部工程。必须分阶段小步提交。

推荐阶段：

1. 初始化项目结构；
2. 阅读固件仓库，输出协议分析报告；
3. 若协议清楚，实现协议层和测试；
4. 实现解码层和数据模型；
5. 实现串口读取线程；
6. 实现记录线程；
7. 实现回放线程；
8. 实现 GUI 框架；
9. 接入实时绘图；
10. 接入控制命令发送；
11. 接入健康监控；
12. 增加模拟数据源；
13. 增加测试；
14. 长时间运行压测；
15. PyInstaller 打包准备。

每个阶段通过测试后执行 git commit。

推荐提交粒度示例：

```bash
git add .
git commit -m "init pydisplay project structure"
git add .
git commit -m "add firmware protocol analysis report"
git add .
git commit -m "implement protocol parser with tests"
git add .
git commit -m "implement decoder and data models"
git add .
git commit -m "implement serial reader worker"
git add .
git commit -m "implement recorder worker"
git add .
git commit -m "implement replay worker"
git add .
git commit -m "implement pyside6 main window layout"
git add .
git commit -m "add realtime pyqtgraph plotting"
git add .
git commit -m "add command sending and validation"
git add .
git commit -m "add health monitor and status panel"
git add .
git commit -m "add simulator and integration tests"
```

---

## B. 在修改代码前必须先检查的文件和内容

在写任何 Python 上位机协议代码前，必须先检查下位机固件仓库。

### B.1 必须检查的固件内容

优先检查：

```text
PulseTIMR2/
PulseTIMR2/Core/
PulseTIMR2/Core/Src/
PulseTIMR2/Core/Inc/
PulseTIMR2/Drivers/
PulseTIMR2/CMakeLists.txt
PulseTIMR2/sensorlist/
```

需要用 `ripgrep` 搜索以下关键词：

```bash
rg "0xAA|0xBB|0xCC|AA BB|frame|Frame|FRAME|uart|UART|USART|DMA|BLE|HJ131|HJ380|packet|Packet|checksum|crc|CRC|PPG|IMU|acc|gyro|Uh|Uc|metadata|mode|brightness|range|pulse|width|LED"
```

### B.2 必须确认的数据帧内容

必须确认：

1. 帧头；
2. 帧尾；
3. 帧总长度；
4. payload 长度；
5. 字段顺序；
6. 字段类型；
7. 字节序；
8. 是否有帧序号；
9. 是否有时间戳；
10. 是否有采样序号；
11. PPG_G / PPG_R / PPG_IR 原始字段；
12. 加速度计三轴字段；
13. 陀螺仪三轴字段；
14. 4 路 Uh 字段；
15. 4 路 Uc 字段；
16. 电压缩放系数；
17. PPG 缩放系数；
18. IMU 加速度缩放系数；
19. IMU 陀螺仪缩放系数；
20. 校验方式；
21. 坏帧处理逻辑；
22. 上位机控制命令格式。

### B.3 必须确认的控制命令

必须确认 GUI 需要发送的命令格式：

1. PPG mode；
2. LED 亮度；
3. PPG 量程；
4. 脉宽；
5. IMU 量程。

必须确认：

1. 命令帧头；
2. 命令帧尾；
3. 命令 ID；
4. 参数字段；
5. 参数合法范围；
6. 字节序；
7. 校验；
8. 下位机是否返回 ACK / NACK；
9. 超时与重发策略。

### B.4 必须输出协议分析报告

在实现 parser 前，必须生成：

```text
docs/protocol_analysis.md
```

内容至少包括：

```markdown
# Protocol Analysis

## Firmware source files checked

列出实际检查过的源码、头文件、sensorlist 文件。

## Data frame format

- Header:
- Tail:
- Frame length:
- Payload length:
- Field order:
- Field type:
- Endianness:
- Checksum:
- Sample rate:
- Sequence field:
- Timestamp field:

## Scaling factors

- PPG_G:
- PPG_R:
- PPG_IR:
- Accel X/Y/Z:
- Gyro X/Y/Z:
- Uh[0:4]:
- Uc[0:4]:

## Control command format

- PPG mode:
- LED brightness:
- PPG range:
- Pulse width:
- IMU range:

## Unresolved questions

列出所有无法从源码确认的问题。

## Implementation decision

只有在协议足够清楚时，才允许继续实现 parser。
```

---

## C. 禁止假设的内容，尤其是通信协议

### C.1 严禁假设

禁止假设以下内容：

1. 帧长度；
2. payload 长度；
3. 字段顺序；
4. 字段数据类型；
5. 字节序；
6. 校验算法；
7. PPG 缩放系数；
8. IMU 缩放系数；
9. 电压缩放系数；
10. 控制命令 ID；
11. 控制命令参数范围；
12. ACK / NACK 格式；
13. 采样频率是否固定为 100 Hz；
14. 固件是否发送时间戳；
15. 固件是否发送帧序号。

### C.2 已知事实

当前用户已确认：

```text
Frame header = 0xAA 0xBB
Frame tail   = 0xCC
```

仅可把这两项作为已知事实。其他内容必须确认。

### C.3 协议不清楚时的处理

如果源码中无法确认协议，必须暂停实现 parser，并输出：

```text
docs/protocol_blockers.md
```

内容包括：

1. 已确认内容；
2. 未确认内容；
3. 需要用户或固件工程师确认的问题；
4. 建议的最小协议文档模板；
5. 暂时可以实现的非协议模块，例如 GUI 骨架、记录框架、回放框架、模拟数据接口。

不得编造协议继续实现。

---

## D. 推荐的 Pydisplay 文件夹架构

推荐项目结构：

```text
Pydisplay/
  AGENTS.md
  README.md
  pyproject.toml
  requirements.txt
  requirements-dev.txt
  .gitignore
  .ruff.toml
  mypy.ini

  docs/
    protocol_analysis.md
    protocol_blockers.md
    architecture.md
    user_manual.md
    test_plan.md

  pydisplay/
    __init__.py
    __main__.py

    app.py
    version.py

    core/
      __init__.py
      models.py
      constants.py
      exceptions.py
      timebase.py

    protocol/
      __init__.py
      parser.py
      decoder.py
      command.py
      checksum.py
      spec.py

    io/
      __init__.py
      serial_reader.py
      serial_port.py
      recorder.py
      replay.py
      raw_format.py
      csv_format.py
      metadata.py

    gui/
      __init__.py
      main_window.py
      widgets/
        __init__.py
        serial_panel.py
        control_panel.py
        record_panel.py
        health_panel.py
        replay_panel.py
        plot_panel.py
      plots/
        __init__.py
        realtime_plot.py
        plot_buffers.py

    services/
      __init__.py
      health_monitor.py
      app_controller.py
      data_router.py

    simulator/
      __init__.py
      fake_device.py
      fake_frames.py
      virtual_serial.py

    utils/
      __init__.py
      logging_config.py
      path_utils.py
      qt_utils.py
      system_info.py

  tests/
    conftest.py
    test_parser.py
    test_decoder.py
    test_command.py
    test_recorder.py
    test_replay.py
    test_health_monitor.py
    test_gui_smoke.py

  scripts/
    run_app.bat
    run_tests.bat
    format.bat
    lint.bat
    make_fake_data.py
    run_fake_device.py
    package_pyinstaller.bat

  sample_data/
    README.md
    raw_frames_example.bin
    decoded_example.csv
    metadata_example.json

  logs/
    .gitkeep

  recordings/
    .gitkeep
```

---

## E. 每个模块的职责说明

### E.1 `pydisplay.app`

应用入口。负责：

1. 创建 QApplication；
2. 初始化日志；
3. 创建主窗口；
4. 启动 Qt 事件循环。

### E.2 `pydisplay.__main__`

支持：

```bash
python -m pydisplay
```

### E.3 `core.models`

定义核心数据模型。

建议至少包含：

1. `RawFrame`
2. `DecodedSample`
3. `ControlSettings`
4. `SerialConfig`
5. `RecordConfig`
6. `HealthStats`
7. `ParserStats`
8. `ReplayConfig`

### E.4 `core.constants`

定义常量：

1. 默认波特率；
2. 默认绘图刷新率；
3. 默认状态刷新率；
4. 默认显示窗口秒数；
5. 默认 k 值；
6. 软件版本；
7. 协议版本；
8. CSV 字段名。

### E.5 `core.exceptions`

定义明确异常类型：

1. `ProtocolError`
2. `ChecksumError`
3. `FrameSyncError`
4. `SerialConnectionError`
5. `RecorderError`
6. `ReplayError`
7. `CommandFormatError`

### E.6 `protocol.spec`

承载从固件确认后的协议定义。

注意：

* 不得在未确认前写死虚构协议。
* 如果协议尚未确认，可以保留 TODO 和异常提示。
* 协议确认后再补充 frame layout。

### E.7 `protocol.parser`

负责字节流到帧的解析。

要求：

1. 支持连续 byte stream；
2. 支持半帧；
3. 支持粘包；
4. 支持坏帧；
5. 支持 resync；
6. 维护坏帧统计；
7. 不因坏帧丢弃整段数据流。

### E.8 `protocol.decoder`

负责 RawFrame 到 DecodedSample 的转换。

要求：

1. 根据真实字段顺序解析；
2. 应用真实缩放系数；
3. 解算 PPG；
4. 解算 IMU；
5. 解算 Uh / Uc；
6. 解算 UD：

```text
UD = (Uh - Uc) / (k - Uc)
```

注意：

* k 是 GUI 可输入常量。
* 解算时必须保留时间戳、帧序号或采样序号。
* 需要处理分母接近 0 的情况。

### E.9 `protocol.command`

负责控制命令打包。

支持至少：

1. PPG mode；
2. LED 亮度；
3. PPG 量程；
4. 脉宽；
5. IMU 量程。

要求：

1. 发送前做合法性检查；
2. 按固件真实格式打包；
3. 发送失败返回明确错误；
4. 如果固件支持 ACK / NACK，需要实现超时处理。

### E.10 `io.serial_reader`

串口读取线程。

职责：

1. 打开串口；
2. 连续读取 bytes；
3. 捕获异常；
4. 不阻塞 GUI；
5. 向 parser 或数据路由发送原始 bytes；
6. 统计 bytes/s；
7. 检测端口拔掉、占用、蓝牙断连；
8. 支持关闭和重连。

### E.11 `io.recorder`

记录线程。

职责：

1. 批量写入 `raw_frames.bin`；
2. 批量写入 `decoded.csv`；
3. 写入 `metadata.json`；
4. 不在 GUI 主线程写文件；
5. 不每帧 flush；
6. 不每帧 pandas append；
7. 支持安全停止；
8. 停止时补全 metadata 的结束时间。

### E.12 `io.replay`

回放线程。

职责：

1. 从 `raw_frames.bin` 回放；
2. 从 `decoded.csv` 回放；
3. 模拟 100 Hz 节奏；
4. 支持暂停；
5. 支持继续；
6. 支持倍速；
7. 支持慢速；
8. 向 GUI 发送与实时模式一致的数据结构。

### E.13 `gui.main_window`

主窗口。

包含区域：

1. 串口连接区；
2. 下位机控制区；
3. 记录设置区；
4. 链路健康监控区；
5. 实时绘图区；
6. 回放区。

### E.14 `gui.widgets.serial_panel`

负责串口 UI：

1. 串口扫描；
2. 选择端口；
3. 选择波特率；
4. 打开；
5. 关闭；
6. 重连；
7. 状态提示。

### E.15 `gui.widgets.control_panel`

负责控制 UI：

1. PPG mode；
2. LED 亮度；
3. PPG 量程；
4. 脉宽；
5. IMU 量程；
6. 发送按钮；
7. 参数合法性提示。

### E.16 `gui.widgets.record_panel`

负责记录 UI：

1. 记录路径；
2. 文件名前缀；
3. 开始记录；
4. 停止记录；
5. 记录状态；
6. 记录队列长度提示。

### E.17 `gui.widgets.health_panel`

负责链路健康显示。

显示：

1. bytes/s；
2. 有效帧率；
3. 坏帧率；
4. bad frame count；
5. bad frame ratio；
6. resync 次数；
7. 串口缓冲区字节数；
8. 解析缓冲字节数；
9. 绘图 FPS；
10. 记录队列长度；
11. 串口连接状态；
12. 记录状态。

状态栏刷新频率 1–5 Hz，不允许每帧更新 QLabel。

### E.18 `gui.widgets.plot_panel`

负责实时绘图。

包含：

1. 三色 PPG；
2. 三轴加速度；
3. 三轴陀螺仪；
4. 4 路 Uh；
5. 4 路 Uc；
6. 2 路 UD。

要求：

1. 最近 N 秒窗口；
2. 默认绘图刷新率 20 Hz；
3. 支持 10–30 FPS；
4. 支持暂停绘图但继续记录；
5. 支持隐藏部分曲线；
6. 坐标轴、单位、标题清楚；
7. 中文不乱码。

### E.19 `services.health_monitor`

聚合健康状态，不直接操作 UI。

### E.20 `services.data_router`

连接串口、parser、decoder、recorder、GUI 绘图和健康监控。

### E.21 `simulator.fake_device`

生成模拟下位机数据。

注意：

* 只有在协议已经确认后，模拟器才能生成真实格式的 fake frame。
* 如果协议未确认，可以只生成 decoded sample 用于测试 GUI 绘图。
* 虚拟串口失败时不要阻塞主项目，可以跳过，采用文件回放或内存 fake source 测试 UI。

---

## F. 推荐的数据流架构

### F.1 实时采集模式

推荐数据流：

```text
HJ380 Serial Port
    ↓ bytes
SerialReader Thread
    ↓ bytes chunks
Parser
    ↓ RawFrame
Decoder
    ↓ DecodedSample
DataRouter
    ├── RecorderWorker Queue
    │       ├── raw_frames.bin
    │       ├── decoded.csv
    │       └── metadata.json
    ├── PlotBuffer
    │       └── GUI Timer 10–30 FPS refresh
    └── HealthMonitor
            └── GUI Timer 1–5 Hz refresh
```

### F.2 回放模式

```text
raw_frames.bin / decoded.csv
    ↓
ReplayWorker Thread
    ↓ RawFrame or DecodedSample
DataRouter
    ├── PlotBuffer
    ├── optional Decoder
    └── HealthMonitor
```

### F.3 控制命令数据流

```text
GUI ControlPanel
    ↓ validated ControlSettings
CommandBuilder
    ↓ command bytes
SerialWriter / SerialReader owning serial object
    ↓
HJ380 Serial Port
    ↓
HJ131 → STM32G474
```

---

## G. 协议解析状态机要求

Parser 必须实现异常恢复状态机。

### G.1 状态

至少包含：

1. `FIND_HEADER_1`
2. `FIND_HEADER_2`
3. `READ_BODY`
4. `READ_TAIL`
5. `VERIFY_CHECKSUM`
6. `EMIT_FRAME`
7. `RESYNC`

如果协议中长度字段明确，也可以使用：

1. `FIND_HEADER`
2. `READ_LENGTH`
3. `READ_PAYLOAD`
4. `READ_CHECKSUM`
5. `READ_TAIL`
6. `VERIFY`
7. `RESYNC`

### G.2 统计指标

Parser 必须维护：

1. 总输入字节数；
2. 有效帧数量；
3. 坏帧数量；
4. 坏帧比例；
5. resync 次数；
6. 当前解析缓冲区字节数；
7. 校验失败次数；
8. 帧尾错误次数；
9. 长度错误次数；
10. 不完整帧次数。

### G.3 坏帧处理原则

坏帧只统计，不得清空整段数据流。

要求：

1. 坏帧后从已有 buffer 内寻找下一个 `0xAA 0xBB`；
2. 支持粘包；
3. 支持半帧；
4. 支持乱字节；
5. 支持帧中出现类似帧头时的恢复；
6. 不能因为一个坏帧导致后续所有数据丢失。

### G.4 单元测试场景

必须测试：

1. 单帧完整输入；
2. 多帧粘包；
3. 一帧拆成多次输入；
4. 前面有垃圾字节；
5. 中间有坏帧；
6. 校验错误；
7. 帧尾错误；
8. 长度错误；
9. 坏帧后能恢复；
10. 长时间随机噪声后能恢复；
11. 输入空 bytes 不崩溃。

---

## H. GUI 线程、串口线程、记录线程的并发设计

### H.1 总原则

GUI 主线程只允许做：

1. UI 响应；
2. 图表刷新；
3. 状态面板刷新；
4. 用户操作事件分发。

GUI 主线程禁止做：

1. 阻塞串口读取；
2. 大量协议解析；
3. 文件写入；
4. pandas append；
5. 每帧 QLabel 更新；
6. 长时间循环；
7. sleep 阻塞。

### H.2 串口读取线程

`SerialReader` 独立线程，负责：

1. 串口打开；
2. 串口读取；
3. 串口异常捕获；
4. 断连检测；
5. 重连支持；
6. bytes/s 统计。

串口异常不得让 GUI 卡死。

### H.3 Parser / Decoder 执行位置

可以有两种设计：

#### 方案 1：SerialReader 线程内解析

适用于协议解析轻量的情况。

```text
SerialReader Thread:
  read bytes → parser.feed → decoder.decode → emit DecodedSample
```

#### 方案 2：独立 ParserWorker

适用于后续协议复杂或高吞吐情况。

```text
SerialReader Thread → bytes queue → ParserWorker → DecodedSample
```

初期可采用方案 1，但代码结构要允许后续拆分。

### H.4 RecorderWorker

记录必须在独立线程中完成。

要求：

1. 使用 queue 接收数据；
2. 批量写入；
3. 定期 flush；
4. 停止时 flush；
5. 不阻塞 GUI；
6. 队列过长时发出健康警告。

### H.5 GUI 绘图刷新

GUI 使用 QTimer 刷新图表。

推荐：

```text
plot_timer interval = 50 ms  # 20 Hz
health_timer interval = 500 ms or 1000 ms
```

每个刷新周期从 ring buffer 取最近 N 秒数据，而不是每帧立即重画。

---

## I. 数据记录格式设计

每次记录建议生成一个独立目录：

```text
recordings/
  20260510_153012_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

### I.1 `raw_frames.bin`

必须记录。

用途：

1. 复盘协议问题；
2. 回放原始数据；
3. 验证 parser；
4. 排查坏帧、断连、粘包、半帧问题。

建议格式：

```text
Magic:       8 bytes, e.g. PYDISP01
Version:     uint16
Record item repeated:
  host_timestamp_ns: uint64
  frame_len:         uint32
  frame_bytes:       uint8[frame_len]
```

注意：

* `frame_bytes` 应包含完整原始帧，包括帧头和帧尾。
* 如果 parser 已经切出 RawFrame，则记录 RawFrame。
* 如果未来要记录未解析 bytes chunk，可另行增加 `raw_stream.bin`，但当前必须保证 `raw_frames.bin` 可回放。

### I.2 `decoded.csv`

面向 Excel / Origin / MATLAB。

必须只包含解码后可读字段和相对时间。

推荐字段：

```text
sample_index
frame_seq
host_time_ns
relative_time_s
device_time
ppg_g
ppg_r
ppg_ir
acc_x
acc_y
acc_z
gyro_x
gyro_y
gyro_z
uh_1
uh_2
uh_3
uh_4
uc_1
uc_2
uc_3
uc_4
ud_1
ud_2
k_value
```

如果协议确认有更多字段，可以追加。

### I.3 写入策略

禁止：

```python
df = df.append(...)
df.to_csv(..., mode="a")  # 每帧调用
file.flush()              # 每帧调用
```

推荐：

1. `csv.writer` 批量写；
2. 内存 list 缓冲若干行；
3. 定期写入；
4. 停止记录时 flush；
5. raw bin 使用 buffered binary writer。

### I.4 记录频率

100 Hz 全量记录，不因绘图暂停而停止。

---

## J. metadata.json 字段设计

`metadata.json` 至少包含：

```json
{
  "software": {
    "name": "Pydisplay",
    "version": "0.1.0",
    "python_version": "",
    "platform": ""
  },
  "firmware": {
    "repository": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
    "branch": "Single",
    "commit": "",
    "commit_available": false
  },
  "protocol": {
    "version": "",
    "frame_header": "AA BB",
    "frame_tail": "CC",
    "frame_length": null,
    "endianness": "",
    "checksum": "",
    "source_files": []
  },
  "serial": {
    "port": "",
    "baudrate": 0,
    "bytesize": "",
    "parity": "",
    "stopbits": "",
    "timeout": ""
  },
  "control_settings": {
    "ppg_mode": "",
    "led_brightness": "",
    "ppg_range": "",
    "pulse_width": "",
    "imu_range": ""
  },
  "decode_settings": {
    "k_value": 0.0,
    "ud_formula": "UD = (Uh - Uc) / (k - Uc)"
  },
  "recording": {
    "recording_name": "",
    "recording_dir": "",
    "start_time_local": "",
    "end_time_local": "",
    "start_time_utc": "",
    "end_time_utc": "",
    "sample_rate_target_hz": 100,
    "raw_file": "raw_frames.bin",
    "decoded_file": "decoded.csv"
  },
  "csv_fields": {
    "sample_index": "zero-based sample counter generated by host if firmware sequence is unavailable",
    "frame_seq": "firmware frame sequence if available",
    "host_time_ns": "monotonic host timestamp in ns",
    "relative_time_s": "seconds since recording start",
    "device_time": "device timestamp if available",
    "ppg_g": "decoded green PPG",
    "ppg_r": "decoded red PPG",
    "ppg_ir": "decoded infrared PPG",
    "acc_x": "accelerometer x",
    "acc_y": "accelerometer y",
    "acc_z": "accelerometer z",
    "gyro_x": "gyroscope x",
    "gyro_y": "gyroscope y",
    "gyro_z": "gyroscope z",
    "uh_1": "sensor high-level voltage channel 1",
    "uh_2": "sensor high-level voltage channel 2",
    "uh_3": "sensor high-level voltage channel 3",
    "uh_4": "sensor high-level voltage channel 4",
    "uc_1": "sensor low-level voltage channel 1",
    "uc_2": "sensor low-level voltage channel 2",
    "uc_3": "sensor low-level voltage channel 3",
    "uc_4": "sensor low-level voltage channel 4",
    "ud_1": "decoded differential signal channel 1",
    "ud_2": "decoded differential signal channel 2",
    "k_value": "k value used for UD calculation"
  },
  "runtime_stats": {
    "total_frames": 0,
    "valid_frames": 0,
    "bad_frames": 0,
    "bad_frame_ratio": 0.0,
    "resync_count": 0,
    "dropped_record_samples": 0
  }
}
```

如果固件 commit 可以通过 git 获取，应写入 commit hash；如果不可获取，写：

```json
"commit_available": false
```

---

## K. 回放模式设计

### K.1 支持来源

回放模式支持：

1. `raw_frames.bin`
2. `decoded.csv`

### K.2 raw 回放

raw 回放路径：

```text
raw_frames.bin
    ↓
RawFrameReader
    ↓ RawFrame
Parser optional / direct RawFrame
    ↓
Decoder
    ↓ DecodedSample
GUI PlotBuffer
```

如果 `raw_frames.bin` 中已经保存完整 RawFrame，可以直接送 Decoder；如果未来保存 raw stream，则必须重新走 Parser。

### K.3 decoded.csv 回放

decoded 回放路径：

```text
decoded.csv
    ↓
DecodedCsvReader
    ↓ DecodedSample
GUI PlotBuffer
```

### K.4 节奏控制

默认模拟 100 Hz：

```text
sample interval = 10 ms
```

支持：

1. 暂停；
2. 继续；
3. 0.25x；
4. 0.5x；
5. 1x；
6. 2x；
7. 5x；
8. 单步可选。

### K.5 回放期间的 GUI 行为

回放期间：

1. 不需要串口连接；
2. 可以测试绘图；
3. 可以测试健康面板；
4. 可以测试算法；
5. 可以暂停绘图；
6. 可以继续记录回放输出为新文件，可选。

---

## L. 性能限制与防卡顿要求

### L.1 刷新频率

要求：

```text
串口采集：按实际速率，目标 100 Hz 数据帧
数据记录：100 Hz 全量
绘图刷新：默认 20 Hz，可选 10–30 Hz
状态刷新：1–5 Hz
```

### L.2 GUI 防卡顿要求

禁止：

1. GUI 主线程读串口；
2. GUI 主线程写 CSV；
3. GUI 主线程写 raw bin；
4. GUI 主线程每帧更新 QLabel；
5. GUI 主线程每帧新建大量 PlotDataItem；
6. 每帧 pandas append；
7. 每帧重建 DataFrame；
8. 每帧 flush；
9. 未限制长度的绘图数组无限增长。

必须：

1. 使用 ring buffer；
2. 使用 QTimer 控制绘图刷新；
3. 使用批量写文件；
4. 使用线程或 Qt worker 解耦 IO；
5. 支持隐藏曲线；
6. 支持暂停绘图但继续记录；
7. 控制记录队列长度；
8. 状态面板低频刷新。

### L.3 推荐 ring buffer

每类曲线只保留最近 N 秒。

例如：

```text
sample_rate = 100 Hz
window_seconds = 30
max_points = 3000
```

### L.4 绘图优化

建议：

1. 创建曲线一次，后续只调用 `setData`；
2. 不在刷新周期内频繁创建 widget；
3. 对不可见曲线跳过 setData；
4. 使用 PyQtGraph 的 downsampling 或 clipToView；
5. 对大窗口数据可做显示降采样，但记录必须全量。

---

## M. 异常处理要求

### M.1 串口异常

必须处理：

1. 串口不存在；
2. 串口被占用；
3. 打开失败；
4. HJ380 拔掉；
5. 蓝牙断连；
6. read timeout；
7. 写命令失败；
8. 重连失败；
9. 关闭时线程未退出。

GUI 必须明确提示状态，不得卡死。

### M.2 协议异常

必须处理：

1. 错误帧头；
2. 错误帧尾；
3. 长度错误；
4. 校验错误；
5. payload 不完整；
6. 字段解析失败；
7. 缩放异常；
8. UD 分母接近 0；
9. 数值溢出；
10. 未知命令 ACK。

### M.3 记录异常

必须处理：

1. 路径不存在；
2. 无写权限；
3. 磁盘满；
4. 文件被占用；
5. 记录队列过长；
6. 停止记录时 flush 失败；
7. metadata 写入失败。

### M.4 回放异常

必须处理：

1. 文件不存在；
2. raw magic 不匹配；
3. raw version 不匹配；
4. raw item 不完整；
5. csv 字段缺失；
6. csv 数值解析失败；
7. 回放中暂停 / 停止。

---

## N. 代码风格要求

### N.1 基本风格

必须：

1. 类型标注；
2. dataclass 表达数据结构；
3. 小函数；
4. 模块边界清晰；
5. 中文 UI 文案；
6. 英文代码命名；
7. 关键逻辑中文注释；
8. 协议相关代码注释必须引用来源文件；
9. 不在 GUI 类里堆积所有逻辑；
10. 不使用全局可变状态传递核心数据。

### N.2 工具

推荐配置：

```bash
ruff check .
black .
isort .
mypy pydisplay
pytest
```

### N.3 Python 版本

面向 Python 3.11。

不要使用仅 Python 3.12+ 才支持的语法。

### N.4 日志

必须有日志：

```text
logs/pydisplay.log
```

日志内容包括：

1. 程序启动；
2. 串口打开 / 关闭；
3. 串口异常；
4. 协议错误摘要；
5. 记录开始 / 停止；
6. 回放开始 / 停止；
7. 控制命令发送；
8. 未处理异常。

---

## O. 阶段性开发步骤

### O.1 阶段 0：环境检查

检查：

```bash
D:\Code\anaconda24\envs\Pydisplay_env\python --version
D:\Code\anaconda24\envs\Pydisplay_env\python -c "import PySide6, pyqtgraph, serial, numpy, pandas, scipy, psutil, yaml; print('ok')"
```

如环境不可用，停止后续开发并报告。

### O.2 阶段 1：初始化项目结构

创建推荐目录结构。

添加：

1. `README.md`
2. `pyproject.toml`
3. `.gitignore`
4. `docs/architecture.md`
5. `scripts/run_app.bat`
6. `scripts/run_tests.bat`

完成后运行基础 import 测试，并 git commit。

### O.3 阶段 2：固件协议分析

克隆或检查固件仓库。

搜索协议相关文件。

生成：

```text
docs/protocol_analysis.md
```

如果协议不完整，生成：

```text
docs/protocol_blockers.md
```

然后暂停 parser 实现。

完成后 git commit。

### O.4 阶段 3：协议 spec / parser

只有协议清楚后才实现。

实现：

1. `protocol/spec.py`
2. `protocol/checksum.py`
3. `protocol/parser.py`
4. `tests/test_parser.py`

测试必须覆盖坏帧恢复。

完成后 git commit。

### O.5 阶段 4：decoder

实现：

1. `protocol/decoder.py`
2. `core/models.py`
3. `tests/test_decoder.py`

必须支持：

1. PPG_G / PPG_R / PPG_IR；
2. acc_x/y/z；
3. gyro_x/y/z；
4. uh_1..uh_4；
5. uc_1..uc_4；
6. ud_1..ud_2；
7. k 值输入；
8. 分母异常保护。

完成后 git commit。

### O.6 阶段 5：控制命令

实现：

1. `protocol/command.py`
2. `tests/test_command.py`

支持：

1. PPG mode；
2. LED 亮度；
3. PPG 量程；
4. 脉宽；
5. IMU 量程。

必须有合法性检查。

完成后 git commit。

### O.7 阶段 6：串口线程

实现：

1. `io/serial_port.py`
2. `io/serial_reader.py`

支持：

1. 列出串口；
2. 打开；
3. 关闭；
4. 重连；
5. 异常状态上报；
6. 写命令；
7. bytes/s 统计。

完成后 git commit。

### O.8 阶段 7：记录线程

实现：

1. `io/recorder.py`
2. `io/raw_format.py`
3. `io/csv_format.py`
4. `io/metadata.py`
5. `tests/test_recorder.py`

必须生成：

1. `raw_frames.bin`
2. `decoded.csv`
3. `metadata.json`

完成后 git commit。

### O.9 阶段 8：回放线程

实现：

1. `io/replay.py`
2. `tests/test_replay.py`

支持：

1. raw 回放；
2. decoded csv 回放；
3. 暂停；
4. 继续；
5. 倍速；
6. 慢速。

完成后 git commit。

### O.10 阶段 9：GUI 骨架

实现：

1. `gui/main_window.py`
2. `serial_panel.py`
3. `control_panel.py`
4. `record_panel.py`
5. `health_panel.py`
6. `plot_panel.py`
7. `replay_panel.py`

要求中文界面不乱码。

完成 GUI smoke test 后 git commit。

### O.11 阶段 10：实时绘图

接入 PyQtGraph。

绘制：

1. PPG；
2. Acc；
3. Gyro；
4. Uh；
5. Uc；
6. UD。

要求：

1. 默认最近 N 秒；
2. 默认 20 Hz；
3. 支持暂停；
4. 支持隐藏曲线。

完成后 git commit。

### O.12 阶段 11：健康监控

实现：

1. `services/health_monitor.py`
2. `tests/test_health_monitor.py`

状态显示：

1. bytes/s；
2. 有效帧率；
3. 坏帧率；
4. resync；
5. 串口缓冲；
6. 解析缓冲；
7. 绘图 FPS；
8. 记录队列；
9. 串口状态；
10. 记录状态。

完成后 git commit。

### O.13 阶段 12：模拟数据源

实现：

1. `simulator/fake_frames.py`
2. `simulator/fake_device.py`
3. `scripts/run_fake_device.py`

可选实现：

1. 虚拟串口模拟；
2. 若虚拟串口不可靠，则使用内存 fake source 或文件回放。

不得因虚拟串口失败阻塞主项目。

完成后 git commit。

### O.14 阶段 13：集成测试与长时间测试

至少测试：

1. 打开 GUI；
2. fake source 绘图；
3. fake source 记录；
4. 停止记录；
5. 回放记录文件；
6. 串口不存在时不崩溃；
7. 坏帧恢复；
8. 运行 30 分钟无明显卡顿。

完成后 git commit。

### O.15 阶段 14：打包准备

添加：

1. `scripts/package_pyinstaller.bat`
2. 打包说明；
3. 图标可选；
4. README 使用说明。

完成后 git commit。

---

## P. 验收标准

### P.1 基础验收

必须满足：

1. `python -m pydisplay` 能启动 GUI；
2. GUI 中文显示正常；
3. 可以选择串口号和波特率；
4. 串口异常不导致 GUI 卡死；
5. 可以打开 / 关闭 / 重连；
6. 状态区能显示串口状态；
7. 记录路径可配置。

### P.2 协议验收

必须满足：

1. 协议来自固件源码或文档；
2. `docs/protocol_analysis.md` 完整；
3. Parser 单元测试通过；
4. 坏帧不导致数据流整体丢失；
5. bad frame count / ratio / resync count 正常更新。

### P.3 解码验收

必须满足：

1. PPG 三色数据正确解码；
2. 加速度三轴正确解码；
3. 陀螺仪三轴正确解码；
4. 4 路 Uh 正确解码；
5. 4 路 Uc 正确解码；
6. 2 路 UD 正确计算；
7. k 值可从 GUI 输入并影响后续解算；
8. 分母异常有保护。

### P.4 绘图验收

必须满足：

1. PPG 图正常；
2. Acc 图正常；
3. Gyro 图正常；
4. Uh 图正常；
5. Uc 图正常；
6. UD 图正常；
7. 最近 N 秒窗口正常；
8. 暂停绘图时记录继续；
9. 隐藏曲线后负载下降；
10. 默认刷新 20 Hz 左右。

### P.5 记录验收

必须满足：

1. 开始记录后生成独立目录；
2. 生成 `raw_frames.bin`；
3. 生成 `decoded.csv`；
4. 生成 `metadata.json`；
5. 100 Hz 全量记录；
6. GUI 主线程不写文件；
7. 停止记录后文件完整；
8. metadata 有开始时间和结束时间；
9. decoded.csv 可被 Excel / Origin / MATLAB 读取。

### P.6 回放验收

必须满足：

1. raw_frames.bin 可回放；
2. decoded.csv 可回放；
3. 回放节奏接近 100 Hz；
4. 支持暂停 / 继续；
5. 支持倍速 / 慢速；
6. 无硬件时可测试 UI 和绘图。

### P.7 性能验收

必须满足：

1. 100 Hz 记录不丢样或有明确丢样统计；
2. GUI 长时间运行不卡死；
3. 状态栏不每帧刷新；
4. 绘图数组不无限增长；
5. 记录队列长度可监控；
6. 串口断开后 GUI 仍可操作。

### P.8 测试验收

必须通过：

```bash
ruff check .
black --check .
isort --check-only .
pytest
```

`mypy` 尽量通过，若存在 PySide6 动态类型导致的问题，需要在报告中说明。

---

## Q. 需要 Code Agent 在不确定时暂停并报告的问题清单

遇到以下任一情况，必须暂停相关实现并报告，不得猜测：

### Q.1 协议不确定

暂停并报告：

1. 无法确认帧长度；
2. 无法确认 payload 字段顺序；
3. 无法确认字段数据类型；
4. 无法确认字节序；
5. 无法确认校验方式；
6. 无法确认缩放系数；
7. 无法确认 PPG / IMU / 电压字段含义；
8. 无法确认采样率；
9. 无法确认帧序号或时间戳；
10. 无法确认控制命令格式。

### Q.2 控制命令不确定

暂停并报告：

1. 不知道 PPG mode 命令 ID；
2. 不知道 LED 亮度范围；
3. 不知道 PPG 量程枚举；
4. 不知道脉宽枚举；
5. 不知道 IMU 量程枚举；
6. 不知道命令是否需要 checksum；
7. 不知道命令是否有 ACK / NACK。

### Q.3 传感器缩放不确定

暂停并报告：

1. PPG 原始值如何换算；
2. Acc 原始值如何换算到 g 或 m/s²；
3. Gyro 原始值如何换算到 dps 或 rad/s；
4. Uh / Uc 原始 ADC 如何换算成电压；
5. UD 的 2 路信号如何对应 4 路 Uh / Uc。

### Q.4 运行环境不确定

暂停并报告：

1. 指定 Python 解释器不可用；
2. PySide6 无法导入；
3. pyqtgraph 无法导入；
4. pyserial 无法导入；
5. 没有写入权限；
6. 测试工具缺失。

### Q.5 架构风险

暂停并报告：

1. 当前实现会导致 GUI 主线程阻塞；
2. 记录线程无法跟上 100 Hz；
3. parser 不支持坏帧恢复；
4. 数据记录格式无法回放；
5. metadata 无法完整记录实验参数；
6. 虚拟串口方案在当前系统不可行。

---

## 最终开发要求

1. 先读固件源码；
2. 先写协议分析报告；
3. 协议明确后再写 parser；
4. 小步实现；
5. 每阶段测试；
6. 每阶段 git commit；
7. 不要一次性重写全部工程；
8. 不要编造协议；
9. GUI 主线程不得阻塞；
10. raw frame 必须记录；
11. decoded csv 必须可读；
12. metadata 必须完整；
13. 回放模式必须可用；
14. 长时间运行必须稳定。