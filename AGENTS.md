# AGENTS.md — Pydisplay Python 上位机开发规范

## 0. 项目背景

本项目是在现有目录 `D:\Desktop\STM32G474\Pydisplay` 下开发一个 Python GUI 上位机子项目。

目标是连接 STM32G474 下位机系统，通过 PC 端 HJ380 蓝牙串口模块接收由 HJ131 蓝牙模块发送的数据，完成：

- 串口选择、连接、关闭、重连；
- 连续数据接收；
- 基于 STM32 固件实际协议的二进制帧解析；
- PPG / IMU / 电压类数据解算；
- PySide6 + PyQtGraph 实时绘图；
- 下位机控制命令发送；
- raw bin + decoded csv + metadata json 数据记录；
- 链路健康监控；
- raw_frames.bin / decoded.csv 回放；
- 无硬件情况下的测试支持。

STM32 固件仓库：

```text
https://github.com/Scp-918/PulseTIMR2/tree/Single
```

STM32 型号：

```text
STM32G474
```

构建系统：

```text
CMake
```

蓝牙链路：

```text
下位机：HJ131 蓝牙模块发送
上位机：HJ380 蓝牙模块接收串口数据
```

Python 虚拟环境：

```text
Pydisplay_env
```

注意：用户已经说明 `Pydisplay_env` 中依赖包已经安装完成，不要把“检查依赖是否安装”作为阻塞项。可以在必要时记录运行环境，但不要停止开发等待用户安装包。

---

## A. Codex 的任务目标与总体计划

### A.1 最终目标

在 `D:\Desktop\STM32G474\Pydisplay` 下完成一个可运行、可测试、可扩展的 Python 上位机项目，实现：

1. 串口通信；
2. 固件真实协议解析；
3. 数据解算；
4. 实时绘图；
5. 下位机控制；
6. 数据记录；
7. 链路健康监控；
8. 数据回放；
9. 测试与基础打包入口。

### A.2 分阶段开发原则

不得一次性重写全部工程。必须按阶段推进：

1. **阶段 0：仓库与协议调查**

   * 阅读 STM32 固件源码；
   * 阅读 sensorlist；
   * 搜索协议定义、串口发送代码、控制命令解析代码；
   * 输出 `docs/protocol_analysis.md`；
   * 若协议不完整，先暂停并报告待确认问题。

2. **阶段 1：建立 Python 项目骨架**

   * 建立包结构；
   * 建立入口；
   * 建立配置、日志、数据模型；
   * 不要先实现复杂 GUI。

3. **阶段 2：实现协议 parser / decoder 的纯 Python 核心**

   * 实现状态机；
   * 实现坏帧统计；
   * 实现解码数据结构；
   * 用单元测试覆盖正常帧、粘包、半包、错帧、resync。

4. **阶段 3：实现串口读取与命令发送**

   * 串口读取线程；
   * 连接、断开、重连；
   * 异常不阻塞 GUI；
   * 控制命令必须来自固件真实定义。

5. **阶段 4：实现数据记录**

   * `raw_frames.bin`；
   * `decoded.csv`；
   * `metadata.json`；
   * 记录线程批量写入；
   * GUI 主线程不写文件。

6. **阶段 5：实现基础 GUI**

   * 串口区；
   * 控制区；
   * 记录区；
   * 健康监控区；
   * 回放区；
   * 实时绘图区。

7. **阶段 6：实现 PyQtGraph 实时绘图**

   * 10–30 FPS 绘图刷新；
   * 默认 20 Hz；
   * 最近 N 秒窗口；
   * 支持暂停绘图但继续记录；
   * 支持隐藏曲线。

8. **阶段 7：实现回放模式**

   * 从 raw bin 回放；
   * 从 decoded csv 回放；
   * 支持暂停、继续、倍速、慢速；
   * 尽量模拟 100 Hz 节奏。

9. **阶段 8：集成测试与验收**

   * 有硬件时串口测试；
   * 无硬件时模拟数据或回放测试；
   * 检查 GUI 卡顿；
   * 检查记录文件完整性；
   * 检查 metadata 字段完整性。

### A.3 Git 保存要求

每个阶段完成并通过基本测试后：

```bash
git status
git diff
git add .
git commit -m "..."
```

如果当前目录不是 git 仓库，则不要强行初始化，先报告当前状态，并继续完成代码变更。若用户后续要求再初始化 git。

---

## B. 修改代码前必须先检查的文件和内容

在实现任何通信协议、解析器、控制命令、缩放系数之前，必须先检查以下内容。

### B.1 固件仓库源码

需要从以下仓库或本地对应源码中检查：

```text
https://github.com/Scp-918/PulseTIMR2/tree/Single
```

优先检查：

```text
CMakeLists.txt
Core/Src/
Core/Inc/
Drivers/
Middlewares/
sensorlist/
*.c
*.h
*.cpp
*.hpp
*.md
*.txt
```

如果仓库已经被 clone 到本地，则优先使用本地文件。否则再根据可用方式获取源码。

### B.2 必须搜索的关键词

至少搜索以下关键词：

```text
AA
BB
CC
0xAA
0xBB
0xCC
UART
USART
HAL_UART
HAL_UART_Transmit
HAL_UART_Receive
DMA
BLE
HJ131
HJ380
frame
packet
protocol
checksum
crc
crc8
crc16
sum
tail
header
PPG
IMU
acc
gyro
Uh
Uc
UD
metadata
mode
LED
range
pulse
cmd
command
control
sensorlist
```

### B.3 必须确认的协议内容

必须在 `docs/protocol_analysis.md` 中明确写出：

1. 帧头；
2. 帧尾；
3. 固定帧长或变长规则；
4. payload 长度；
5. 字段顺序；
6. 每个字段的数据类型；
7. 每个字段字节数；
8. 字节序；
9. 校验方式；
10. PPG_G / PPG_R / PPG_IR 原始值含义；
11. 加速度计三轴原始值含义；
12. 陀螺仪三轴原始值含义；
13. 4 路 Uh 原始值含义；
14. 4 路 Uc 原始值含义；
15. 电压缩放系数；
16. PPG 缩放系数（PPG 只记录固件输出的 raw count）；
17. IMU 缩放系数；
18. 帧序号目前不存在；
19. 时间戳由上位机提供，下位机暂时不提供时间戳；
20. 上位机控制命令格式（控制帧目前设计为无 ACK/NACK）；
21. metadata 控制参数枚举或取值范围；
22. 协议版本信息；
23. 未确认问题清单;

额外增加传感器数据说明，无需确认：
`adc_data[ch].early_code` 对应`Uc`,和 `adc_data[ch].late_code` 对应 `Uh`;
4 个 ADC 通道按照帧记录顺序从前到后与实验通道 `1..4`一一对应; 
`UD1` / `UD2` 分别使用通道2/通道3两路 `Uh` / `Uc`分别计算，通道2对应`UD1`,通道3对应`UD2`;
AD4007 原始码到电压的换算公式可以参考如下代码（data[2]到data[5]对应帧2-5位字节），其中VREF=4.096V，无外部偏置，满量程17位：
temp32 = (data[2] & 255) + ((data[3] & 255) * 256) + ((data[4] & 255) * 65536);
if (temp32 >= 8388608) temp32 = temp32 - 16777216;
Ul1 = temp32 * (VREF / 131072.0);
PPG 只记录固件输出的 raw count;
控制帧设计为无 ACK/NACK;

### B.4 sensorlist 检查要求

必须检查工程中的 `sensorlist` 部分，确认：

1. 传感器型号；
2. PPG 数据格式；
3. IMU 数据格式；
4. 电压 / ADC 转换方式；
5. PPG mode；
6. LED 亮度；
7. PPG 量程；
8. 脉宽；
9. IMU 量程；
10. 任何寄存器配置和单位换算说明。

### B.5 不允许跳过协议分析

如果协议定义不清楚，不得继续实现“假协议解析器”。必须先输出：

```text
docs/protocol_analysis.md
docs/protocol_questions.md
```

然后暂停并报告用户需要确认的问题。

---

## C. 禁止假设的内容，尤其是通信协议

### C.1 已知且可使用的事实

用户已明确确认：

```text
帧头：0xAA 0xBB
帧尾：0xCC
```

这两个事实可以直接作为初始 parser 设计约束。

### C.2 禁止臆造的内容

以下内容禁止凭经验假设，必须从固件、sensorlist 或文档中确认：

1. 帧总长度；
2. payload 长度；
3. 字段顺序；
4. 每个字段的字节数；
5. 有符号 / 无符号类型；
6. float / int / fixed-point 表示；
7. little-endian / big-endian（确认是否有）；
8. checksum 算法；
9. CRC 多项式（实际中是没有使用CRC 多项式）；
10. PPG 缩放系数；
11. IMU 缩放系数；
12. 电压缩放系数；
13. Uh / Uc 的原始单位；
14. UD 的 k 值含义和范围；
15. 控制命令帧格式；
16. PPG mode 枚举；
17. LED 亮度范围；
18. PPG 量程枚举；
19. 脉宽枚举；
20. IMU 量程枚举；
21. 协议版本。

### C.3 不能做的事情

不得因为 GUI 需要数据就临时编造如下结构：

```text
AA BB + 固定 payload + checksum + CC
```

除非该结构已被固件源码证实。

可以临时实现 “模拟数据源” 用于 GUI 测试，但必须明确标注为：

```text
simulation only
not firmware protocol
```

模拟数据不得冒充真实协议。

---

## D. 推荐的 Pydisplay 文件夹架构

目标目录建议如下。可以根据实际情况小幅调整，但必须保持模块职责清晰。

```text
Pydisplay/
  AGENTS.md
  README.md
  pyproject.toml
  requirements.txt              # 可选：仅记录依赖，不强制重装
  .gitignore

  .agents/
    skills/
      pydisplay-firmware-protocol-analysis/
        SKILL.md
      pydisplay-protocol-parser-state-machine/
        SKILL.md
      pydisplay-serial-ble-io/
        SKILL.md
      pydisplay-pyside6-pyqtgraph-gui/
        SKILL.md
      pydisplay-recorder-replay/
        SKILL.md
      pydisplay-health-performance/
        SKILL.md
      pydisplay-testing-packaging/
        SKILL.md

  docs/
    protocol_analysis.md
    protocol_questions.md
    data_format.md
    user_manual.md

  pydisplay/
    __init__.py
    __main__.py
    app.py
    config.py
    logging_config.py
    version.py

    protocol/
      __init__.py
      constants.py
      models.py
      parser.py
      decoder.py
      commands.py
      errors.py

    io/
      __init__.py
      serial_manager.py
      serial_reader.py
      serial_writer.py
      port_discovery.py
      simulated_device.py

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

    gui/
      __init__.py
      main_window.py
      widgets/
        __init__.py
        serial_panel.py
        control_panel.py
        recorder_panel.py
        health_panel.py
        replay_panel.py
        plot_panel.py
      plots/
        __init__.py
        ring_buffer.py
        plot_manager.py
        curve_config.py

    services/
      __init__.py
      pipeline.py
      health_monitor.py
      data_bus.py

    utils/
      __init__.py
      timebase.py
      paths.py
      safe_queue.py

  tests/
    test_protocol_parser.py
    test_decoder.py
    test_commands.py
    test_raw_bin_format.py
    test_replay.py

  scripts/
    run_app.py
    simulate_device.py
    inspect_raw_bin.py
```

注意：

1. 不要求第一阶段一次性创建所有文件。
2. 应按阶段逐步增加模块。
3. 每个模块需要有清晰 docstring 和中文注释，便于实验人员维护。
4. GUI 文案使用中文，但代码命名使用英文。

---

## E. 每个模块的职责说明

### E.1 `pydisplay.protocol`

负责协议相关逻辑，不依赖 GUI。

#### `constants.py`

存放从固件确认后的协议常量，例如：

```text
FRAME_HEADER
FRAME_TAIL
FRAME_LENGTH
PAYLOAD_LENGTH
PROTOCOL_VERSION
```

注意：除 `FRAME_HEADER = b"\xAA\xBB"` 和 `FRAME_TAIL = b"\xCC"` 外，其他常量必须由固件确认后再写入。

#### `models.py`

定义数据结构：

```text
RawFrame
ParsedFrame
DecodedSample
ParserStats
ControlMetadata
CommandFrame
```

建议使用 `dataclasses.dataclass`。

#### `parser.py`

实现二进制帧状态机。

职责：

* 连续接收 bytes；
* 找帧头；
* 收帧体；
* 校验；
* 找帧尾；
* 输出 ParsedFrame；
* 统计坏帧；
* resync；
* 不因坏帧丢弃整段数据流。

#### `decoder.py`

负责将 `ParsedFrame` 解码成 `DecodedSample`。

解码内容：

```text
timestamp_pc_ns
relative_time_s
frame_seq or sample_seq
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
```

UD 公式：

```text
UD = (Uh - Uc) / (k - Uc)
```

k 来自 GUI 输入。

#### `commands.py`

负责上位机控制命令编码。

必须基于固件真实命令格式实现，不得臆造。

至少支持 metadata 参数：

```text
PPG mode
LED brightness
PPG range
pulse width
IMU range
```

职责：

* 参数合法性检查；
* 命令编码；
* 命令发送前预览；
* 命令发送失败时返回错误信息。

---

### E.2 `pydisplay.io`

负责串口与模拟数据源。

#### `serial_manager.py`

负责串口打开、关闭、重连、状态管理。

#### `serial_reader.py`

独立线程或 QObject worker，负责连续读取串口 bytes。

要求：

* 不阻塞 GUI；
* 支持异常捕获；
* 支持端口占用；
* 支持蓝牙断连；
* 支持 HJ380 拔出；
* 状态变化发给 GUI 和 health monitor。

#### `serial_writer.py`

负责发送控制命令。

要求：

* 发送前检查串口状态；
* 发送失败要有明确状态提示；
* 不得在 GUI 线程中做长时间阻塞。

#### `port_discovery.py`

负责列出可用串口号。

#### `simulated_device.py`

可选测试工具。

用于没有硬件时模拟下位机发送数据。

注意：

* 如果虚拟串口方案失败，不要阻塞主项目；
* 可改为文件回放或内存模拟数据；
* 模拟数据必须明确标注为 simulation only。

---

### E.3 `pydisplay.recorder`

负责数据记录。

#### `recorder_worker.py`

独立记录线程，负责批量写入：

```text
raw_frames.bin
decoded.csv
metadata.json
```

要求：

* GUI 主线程不写文件；
* 不要每帧 flush；
* 不要每帧 pandas append；
* 使用 queue 接收待写数据；
* 批量写入；
* 记录开始、暂停、停止状态明确。

#### `raw_bin_format.py`

定义 raw bin 格式。

建议 raw bin 不只保存 decoded frame，而是尽量保存原始接收数据或原始帧数据与 PC 时间戳，便于复盘协议问题。

推荐格式：

```text
File header:
  magic: b"PYDISPRAW"
  format_version: uint16
  created_unix_ns: uint64
  reserved...

Repeated records:
  record_type: uint8
    1 = raw_serial_chunk
    2 = valid_raw_frame
    3 = bad_frame_fragment
  timestamp_ns: uint64
  length: uint32
  payload: bytes
```

如果最终选择只记录完整 raw frame，也必须在 `docs/data_format.md` 中说明限制。

#### `csv_writer.py`

写入 `decoded.csv`。

要求：

* 只包含解码后的可读数据；
* 包含相对时间；
* 包含帧序号或采样序号；
* 适合 Excel / Origin / MATLAB 使用；
* 使用标准 csv writer 或批量文本写入；
* 不要每帧 pandas append。

#### `metadata.py`

生成 metadata。

---

### E.4 `pydisplay.replay`

负责回放模式。

#### `raw_bin_reader.py`

读取 `raw_frames.bin`，并按时间戳模拟数据流。

#### `decoded_csv_reader.py`

读取 `decoded.csv`，直接生成 `DecodedSample`。

#### `replay_worker.py`

回放线程。

要求：

* 支持暂停；
* 支持继续；
* 支持倍速；
* 支持慢速；
* 尽量模拟 100 Hz；
* 回放不能阻塞 GUI；
* 回放数据应能进入同一套 GUI 绘图和 health monitor。

---

### E.5 `pydisplay.gui`

负责 PySide6 GUI。

#### `main_window.py`

主窗口，组合所有区域。

界面分区：

```text
串口连接区
下位机控制区
记录设置区
链路健康监控区
实时绘图区
回放区
```

#### `widgets/serial_panel.py`

串口选择与连接控件。

#### `widgets/control_panel.py`

控制参数输入和发送控件。

至少包含：

```text
PPG mode
LED 亮度
PPG 量程
脉宽
IMU 量程
k 值
```

k 值用于 UD 解算。

#### `widgets/recorder_panel.py`

记录路径、文件名、开始记录、停止记录。

#### `widgets/health_panel.py`

显示：

```text
bytes/s
有效帧率
坏帧率
resync 次数
串口缓冲区字节数
解析缓冲字节数
绘图 FPS
记录队列长度
串口连接状态
记录状态
```

刷新频率 1–5 Hz，不要每帧更新 QLabel。

#### `widgets/replay_panel.py`

回放文件选择、开始、暂停、继续、倍速、慢速。

#### `widgets/plot_panel.py`

PyQtGraph 绘图区域。

绘制：

```text
3 色 PPG
3 轴加速度计
3 轴陀螺仪
4 路 Uh
4 路 Uc
2 路 UD
```

要求：

* 每个曲线窗口只显示最近 N 秒；
* 默认绘图刷新率 20 Hz；
* 可配置 10–30 FPS；
* 支持暂停绘图但继续记录；
* 支持隐藏部分曲线；
* 坐标轴、单位、标题清楚；
* 中文标签不乱码。

---

### E.6 `pydisplay.services`

负责数据流编排和健康监控。

#### `pipeline.py`

把串口、parser、decoder、recorder、GUI 绘图、health monitor 串起来。

#### `health_monitor.py`

统计链路状态和性能指标：

```text
bytes/s
valid_frame_rate
bad_frame_rate
bad_frame_count
bad_frame_ratio
resync_count
serial_buffer_bytes
parser_buffer_bytes
plot_fps
record_queue_size
serial_state
recording_state
```

#### `data_bus.py`

封装 queue 或 Qt signal 传输方式。

---

## F. 推荐的数据流架构

### F.1 实时串口模式

推荐数据流：

```text
HJ380 串口
  ↓
SerialReader 线程
  ↓ raw bytes chunks
Parser 状态机
  ↓ ParsedFrame
Decoder
  ↓ DecodedSample
  ├── RecorderWorker queue
  ├── GUI Plot RingBuffer
  └── HealthMonitor
```

### F.2 控制命令流

```text
GUI ControlPanel
  ↓ 参数合法性检查
protocol.commands
  ↓ CommandFrame bytes
SerialWriter
  ↓
HJ380 串口
  ↓
HJ131 / STM32 下位机
```

### F.3 记录数据流

```text
Raw serial chunk / raw frame
  ↓
RecorderWorker raw queue
  ↓
raw_frames.bin

DecodedSample
  ↓
RecorderWorker decoded queue
  ↓
decoded.csv

Session metadata
  ↓
metadata.json
```

### F.4 回放数据流

raw bin 回放：

```text
raw_frames.bin
  ↓
ReplayWorker
  ↓ raw bytes / raw frames
Parser
  ↓
Decoder
  ↓
GUI Plot + HealthMonitor
```

decoded csv 回放：

```text
decoded.csv
  ↓
ReplayWorker
  ↓ DecodedSample
  ↓
GUI Plot + HealthMonitor
```

---

## G. 协议解析状态机要求

Parser 必须实现异常恢复状态机。

### G.1 状态设计

推荐状态：

```text
FIND_HEADER
READ_BODY
READ_CHECKSUM_OR_TAIL
VERIFY
EMIT_FRAME
RESYNC
```

如果固件协议更适合其他状态划分，可以调整，但必须覆盖以下逻辑：

1. 正常同步；
2. 找帧头；
3. 收帧体；
4. 校验；
5. 找帧尾；
6. resync；
7. 坏帧统计。

### G.2 状态机基本要求

1. 输入是连续 bytes，不假设一次 read 正好是一帧。
2. 必须支持半包。
3. 必须支持粘包。
4. 必须支持帧头前噪声。
5. 必须支持帧内损坏。
6. 坏帧只统计，不丢弃整段数据流。
7. resync 应尽量从已有 buffer 中寻找下一个 `0xAA 0xBB`。
8. 需要统计：

   * 总帧数；
   * 有效帧数；
   * 坏帧数；
   * 坏帧比例；
   * resync 次数；
   * 当前 parser buffer 字节数。

### G.3 已知帧头帧尾

用户已确认：

```text
FRAME_HEADER = b"\xAA\xBB"
FRAME_TAIL = b"\xCC"
```

但禁止假设固定帧长、checksum 规则和 payload 字段。

### G.4 单元测试要求

至少覆盖：

1. 单帧完整输入；
2. 一次输入多个完整帧；
3. 一帧拆成多次输入；
4. 帧头前有噪声；
5. 坏 checksum；
6. 错误帧尾；
7. 中间坏帧后恢复；
8. parser buffer 不无限增长。

---

## H. GUI 线程、串口线程、记录线程的并发设计

### H.1 GUI 主线程

GUI 主线程只负责：

1. 用户交互；
2. 状态显示；
3. 定时刷新图表；
4. 向 worker 发出控制信号。

GUI 主线程禁止：

1. 阻塞串口读取；
2. 大量协议解析；
3. 文件写入；
4. 每帧刷新 QLabel；
5. 每帧重建 PlotDataItem；
6. 每帧 pandas append。

### H.2 SerialReader 线程

负责：

1. 串口阻塞或半阻塞读取；
2. 捕获串口异常；
3. 产出 raw bytes；
4. 更新串口状态。

串口异常包括：

```text
端口占用
端口不存在
HJ380 被拔掉
蓝牙断连
读取超时
权限错误
串口写入失败
```

异常必须传给 GUI 状态区，不能导致 GUI 卡死。

### H.3 Parser / Decoder

可在 SerialReader 线程中轻量执行，也可放入独立 worker。

如果解析负载较低，可以：

```text
SerialReader -> Parser -> Decoder -> queues/signals
```

如果解析负载较高，应拆成：

```text
SerialReader -> raw queue -> ParserWorker -> decoded queue
```

无论采用哪种方式，都必须保证 GUI 主线程不直接处理连续 byte stream。

### H.4 RecorderWorker 线程

负责批量写入：

```text
raw_frames.bin
decoded.csv
metadata.json
```

要求：

1. 使用 queue；
2. 批量写入；
3. 定期 flush；
4. 停止记录时 final flush；
5. 队列过长时 health panel 显示；
6. 写入异常要通知 GUI；
7. 停止记录后 metadata 写入记录结束时间。

### H.5 ReplayWorker 线程

负责回放节奏控制，不阻塞 GUI。

---

## I. 数据记录格式设计

### I.1 记录目录

每次记录建议生成一个 session 目录：

```text
records/
  20260510_013000_experiment_name/
    raw_frames.bin
    decoded.csv
    metadata.json
```

如果用户指定完整路径和文件名，则尊重用户设置。

### I.2 `raw_frames.bin`

必须记录，便于复盘协议问题。

推荐记录内容：

1. 文件头；
2. 格式版本；
3. 创建时间；
4. 原始串口 chunk 或原始帧；
5. 每条记录的 PC 时间戳；
6. record type；
7. payload length；
8. payload bytes。

推荐二进制布局：

```text
FileHeader:
  magic: 9 bytes = "PYDISPRAW"
  format_version: uint16
  created_unix_ns: uint64
  header_length: uint32
  reserved: bytes

Record:
  record_type: uint8
  timestamp_ns: uint64
  payload_length: uint32
  payload: bytes[payload_length]
```

`record_type` 推荐：

```text
1 = raw_serial_chunk
2 = valid_raw_frame
3 = bad_frame_fragment
```

如果实现时简化，必须在 `docs/data_format.md` 中说明实际格式。

### I.3 `decoded.csv`

必须包含解码后的可读数据和相对时间。

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

如果固件中字段名不同，以协议分析报告为准。

### I.4 写入频率

要求：

```text
100 Hz 全量记录
```

不得为了绘图降采样而减少记录数据。

绘图可以降帧，记录不能降帧。

---

## J. metadata.json 字段设计

`metadata.json` 至少包含以下字段：

```json
{
  "software": {
    "name": "Pydisplay",
    "version": "0.1.0"
  },
  "firmware": {
    "repo": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
    "commit": null,
    "branch": "Single",
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
  "csv_fields": {
    "relative_time_s": "Relative time from recording start, seconds",
    "timestamp_pc_ns": "PC monotonic or wall-clock timestamp in ns",
    "frame_seq": "Frame sequence if available",
    "sample_seq": "Sample sequence if available",
    "PPG_G": "Green PPG decoded value",
    "PPG_R": "Red PPG decoded value",
    "PPG_IR": "Infrared PPG decoded value",
    "ACC_X": "Acceleration X",
    "ACC_Y": "Acceleration Y",
    "ACC_Z": "Acceleration Z",
    "GYRO_X": "Gyroscope X",
    "GYRO_Y": "Gyroscope Y",
    "GYRO_Z": "Gyroscope Z",
    "Uh1": "Sensor high-level voltage channel 1",
    "Uh2": "Sensor high-level voltage channel 2",
    "Uh3": "Sensor high-level voltage channel 3",
    "Uh4": "Sensor high-level voltage channel 4",
    "Uc1": "Sensor low-level voltage channel 1",
    "Uc2": "Sensor low-level voltage channel 2",
    "Uc3": "Sensor low-level voltage channel 3",
    "Uc4": "Sensor low-level voltage channel 4",
    "UD1": "Decoded UD signal channel 1",
    "UD2": "Decoded UD signal channel 2"
  }
}
```

实际字段需要根据协议分析结果修正。

---

## K. 回放模式设计

### K.1 raw bin 回放

从 `raw_frames.bin` 读取原始数据，尽量复用真实数据链路：

```text
raw_frames.bin -> ReplayWorker -> Parser -> Decoder -> GUI/Recorder/Health
```

要求：

1. 支持原始串口 chunk；
2. 支持有效 raw frame；
3. 支持按原始时间戳节奏回放；
4. 支持 0.25x、0.5x、1x、2x、5x；
5. 支持暂停 / 继续；
6. 支持停止；
7. 支持回放过程中观察 parser stats。

### K.2 decoded csv 回放

从 `decoded.csv` 读取已解码数据：

```text
decoded.csv -> ReplayWorker -> DecodedSample -> GUI/Health
```

要求：

1. 不经过 parser；
2. 用于 UI 和算法调试；
3. 支持 100 Hz 模拟节奏；
4. 支持倍速和慢速。

### K.3 回放状态

GUI 需要显示：

```text
回放文件
回放类型
回放进度
回放速度
暂停/运行状态
当前样本时间
```

---

## L. 性能限制与防卡顿要求

### L.1 刷新频率

要求：

```text
数据记录：100 Hz 全量记录
绘图刷新：默认 20 Hz，可配置 10–30 Hz
状态刷新：1–5 Hz
```

### L.2 绘图性能

PyQtGraph 绘图要求：

1. 使用 ring buffer；
2. 不要每次重建曲线；
3. 初始化时创建 PlotDataItem；
4. 刷新时只调用 `setData()`；
5. 只显示最近 N 秒；
6. 支持隐藏曲线；
7. 支持暂停绘图；
8. 暂停绘图时仍继续记录。

### L.3 队列控制

需要避免内存无限增长。

建议：

1. 记录队列设置合理上限；
2. GUI 绘图只保留最近窗口；
3. health panel 显示队列长度；
4. 队列积压时提示用户；
5. 不要静默丢弃记录数据；
6. 如必须丢弃绘图数据，只能丢弃 GUI 显示层数据，不得丢弃记录数据。

### L.4 QLabel 更新限制

禁止每帧更新 QLabel。

状态栏使用 QTimer 以 1–5 Hz 刷新。

---

## M. 异常处理要求

必须处理并在 GUI 中明确提示：

### M.1 串口异常

```text
串口打开失败
串口被占用
串口不存在
HJ380 被拔出
蓝牙断连
读取超时
写入失败
关闭串口失败
重连失败
```

### M.2 协议异常

```text
找不到帧头
帧尾错误
帧长度错误
checksum / CRC 错误
payload 长度不符
字段解码失败
resync 频繁
坏帧比例过高
```

### M.3 记录异常

```text
路径不存在
没有写权限
磁盘空间不足
raw bin 写入失败
csv 写入失败
metadata 写入失败
记录队列积压
停止记录 flush 失败
```

### M.4 GUI 异常

```text
非法 k 值
非法控制参数
发送命令时串口未连接
回放文件不存在
回放文件格式错误
decoded.csv 字段缺失
```

异常处理原则：

1. GUI 不能崩溃；
2. 状态区必须显示明确原因；
3. 日志必须记录 traceback；
4. 对用户可恢复的异常应提供重试入口；
5. 不要吞掉异常。

---

## N. 代码风格要求

### N.1 总体风格

1. Python 代码使用英文命名；
2. GUI 文案使用中文；
3. 关键逻辑写中文注释；
4. 协议字段、单位、缩放系数必须写清楚来源；
5. 不要写巨型单文件；
6. 不要把 GUI、串口、parser、recorder 全塞到一个文件里。

### N.2 类型与结构

推荐：

```text
dataclasses
type hints
Enum
Queue
QObject + Signal/Slot
QThread or Python threading
```

### N.3 日志

需要使用 logging。

建议日志文件：

```text
logs/pydisplay.log
```

日志内容至少包括：

```text
串口连接状态
协议解析异常
坏帧统计
记录开始/停止
命令发送
回放状态
未捕获异常
```

### N.4 文档

必须维护：

```text
docs/protocol_analysis.md
docs/data_format.md
README.md
```

---

## O. 阶段性开发步骤

### 阶段 0：协议分析

任务：

1. 搜索固件源码；
2. 搜索 sensorlist；
3. 确认帧结构；
4. 确认控制命令；
5. 输出 `docs/protocol_analysis.md`；
6. 如果不完整，输出 `docs/protocol_questions.md` 并暂停。

验收：

```text
docs/protocol_analysis.md 中有明确协议表格。
没有未确认字段时，才进入 parser 实现。
```

### 阶段 1：项目骨架

任务：

1. 建立目录结构；
2. 创建 `pydisplay/__main__.py`；
3. 创建基础 logging；
4. 创建 README；
5. 创建空 GUI 主窗口入口。

验收：

```bash
python -m pydisplay
```

能打开基础窗口或打印明确启动信息。

### 阶段 2：Parser / Decoder

任务：

1. 实现 parser 状态机；
2. 实现 decoder；
3. 实现 parser stats；
4. 实现测试。

验收：

```bash
pytest tests/test_protocol_parser.py tests/test_decoder.py
```

通过。

### 阶段 3：串口 IO

任务：

1. 串口列表；
2. 打开/关闭/重连；
3. reader worker；
4. writer worker；
5. 异常状态上报。

验收：

1. 无硬件时 GUI 不崩溃；
2. 串口占用/不存在有明确提示；
3. 有硬件时可以接收 bytes。

### 阶段 4：记录系统

任务：

1. raw bin writer；
2. decoded csv writer；
3. metadata writer；
4. 记录线程；
5. 批量写入。

验收：

1. 能生成三个文件；
2. csv 可被 Excel / MATLAB 读取；
3. metadata 字段完整；
4. GUI 主线程无文件写入。

### 阶段 5：GUI 控件

任务：

1. 串口连接区；
2. 控制区；
3. 记录区；
4. 健康监控区；
5. 回放区；
6. 绘图区基本布局。

验收：

1. 中文显示正常；
2. 按钮语义清楚；
3. 窗口分区合理；
4. 不连接硬件也能打开。

### 阶段 6：实时绘图

任务：

1. Ring buffer；
2. 20 Hz 刷新；
3. 最近 N 秒窗口；
4. 曲线隐藏；
5. 暂停绘图但继续记录。

验收：

1. 100 Hz 数据输入时 GUI 不明显卡顿；
2. 曲线更新正常；
3. 隐藏曲线可降低负载。

### 阶段 7：回放

任务：

1. raw bin 回放；
2. decoded csv 回放；
3. 暂停/继续；
4. 倍速/慢速。

验收：

1. 无硬件时可以调试 UI；
2. 回放节奏接近真实采样；
3. 回放状态显示正确。

### 阶段 8：集成与清理

任务：

1. 全流程测试；
2. README 使用说明；
3. 协议文档修订；
4. 数据格式文档修订；
5. 日志检查；
6. git 保存。

验收：

```text
Pydisplay 项目可运行，可记录，可回放，可查看健康状态。
```

---

## P. 验收标准

### P.1 基础运行

```bash
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

应能启动 GUI。

### P.2 串口功能

1. 能列出串口；
2. 能选择波特率；
3. 能打开串口；
4. 能关闭串口；
5. 能重连；
6. 端口异常时 GUI 不死锁；
7. 状态区显示明确错误。

### P.3 协议解析

1. 使用固件真实协议；
2. 识别 `0xAA 0xBB` 帧头和 `0xCC` 帧尾；
3. 正确处理半包、粘包、坏帧；
4. 坏帧数量、坏帧比例、resync 次数可见；
5. 不因单个坏帧丢弃整段数据流。

### P.4 数据解算

能输出：

```text
PPG_G
PPG_R
PPG_IR
ACC_X
ACC_Y
ACC_Z
GYRO_X
GYRO_Y
GYRO_Z
Uh1-Uh4
Uc1-Uc4
UD1-UD2
```

并保留：

```text
timestamp
relative_time_s
frame_seq or sample_seq
```

### P.5 实时绘图

1. PPG 三色曲线正常；
2. ACC 三轴正常；
3. GYRO 三轴正常；
4. Uh 四路正常；
5. Uc 四路正常；
6. UD 两路正常；
7. 最近 N 秒窗口；
8. 默认 20 Hz 刷新；
9. 支持暂停绘图；
10. 支持隐藏曲线；
11. 中文不乱码。

### P.6 控制命令

1. 控制命令格式来自固件；
2. 参数合法性检查；
3. 支持：

   * PPG mode；
   * LED 亮度；
   * PPG 量程；
   * 脉宽；
   * IMU 量程。
4. 发送失败有明确提示。

### P.7 数据记录

每次记录生成：

```text
raw_frames.bin
decoded.csv
metadata.json
```

要求：

1. raw bin 必须包含原始数据和时间戳；
2. decoded csv 可读；
3. metadata 字段完整；
4. 100 Hz 全量记录；
5. GUI 主线程不写文件；
6. 不每帧 flush；
7. 不每帧 pandas append。

### P.8 健康监控

状态区显示：

```text
bytes/s
有效帧率
坏帧率
resync 次数
串口缓冲区字节数
解析缓冲字节数
绘图 FPS
记录队列长度
串口连接状态
记录状态
```

刷新频率 1–5 Hz。

### P.9 回放

1. raw bin 可回放；
2. decoded csv 可回放；
3. 支持暂停；
4. 支持继续；
5. 支持倍速；
6. 支持慢速；
7. 无硬件时可调试 GUI。

---

## Q. 不确定时必须暂停并报告的问题清单

遇到以下情况时，不要继续编造实现，必须暂停并向用户报告。

### Q.1 协议相关

1. 找不到完整帧长度；
2. 找不到 payload 字段顺序；
3. 找不到字节序；
4. 找不到 checksum / CRC 规则；
5. 找不到 PPG 缩放系数；
6. 找不到 IMU 缩放系数；
7. 找不到电压缩放系数；
8. Uh / Uc 原始单位不明确；
9. UD 的两个通道来源不明确；
10. 帧序号或采样序号是否存在不明确；
11. 下位机是否发送时间戳不明确；
12. 采样率是否固定 100 Hz 不明确。

### Q.2 控制命令相关

1. 找不到上位机控制命令格式；
2. 找不到 PPG mode 枚举；
3. 找不到 LED 亮度范围；
4. 找不到 PPG 量程枚举；
5. 找不到脉宽枚举；
6. 找不到 IMU 量程枚举；
7. 命令是否需要 checksum 不明确；
8. 命令是否有 ACK 不明确。

### Q.3 数据记录相关

1. raw bin 应记录 raw chunk 还是完整 raw frame 不明确；
2. 是否需要记录坏帧 fragment 不明确；
3. metadata 中固件 commit 无法获取；
4. CSV 字段单位无法确认。

### Q.4 工程相关

1. 固件仓库无法访问；
2. 本地没有固件源码；
3. sensorlist 不存在或内容不足；
4. 当前目录已有代码且结构不清楚；
5. 当前目录有未提交用户修改，可能被覆盖；
6. 虚拟串口方案在 Windows 上不可用。

### Q.5 报告格式

暂停时输出：

```text
当前已确认内容：
- ...

当前无法确认内容：
- ...

已检查的文件：
- ...

建议用户确认的问题：
1. ...
2. ...

在用户确认前，不继续实现相关 parser / command 编码。
```

---

## 附录：MCP 使用建议

Codex 可以使用已经安装的 MCP：

```text
Context7 MCP
OpenAI Developer Docs MCP
```

建议用途：

1. 查询 PySide6 官方 API 用法；
2. 查询 PyQtGraph 实时绘图最佳实践；
3. 查询 pyserial 串口异常处理；
4. 查询 Python packaging / pytest 用法；
5. 查询 Qt Signal/Slot 和 QThread 推荐模式。

注意：

MCP 只能用于查库和工程实现方式，不能替代固件源码中的协议确认。通信协议必须以 STM32 固件源码、sensorlist 和项目文档为准。

---

## 附录：开发底线

1. 不编造协议。
2. 不让 GUI 主线程阻塞。
3. 不每帧写文件 flush。
4. 不每帧更新 QLabel。
5. 不一次性重写全部工程。
6. 不把模拟协议当真实协议。
7. 不忽略坏帧统计。
8. 不忽略 raw 数据记录。
9. 不在协议不清楚时继续硬写 parser。
10. 每阶段测试成功后再进入下一阶段。
