# AGENTS.md — STM32G474 Python 上位机迁移项目

本文件用于指导 Codex CLI 在 VS Code 终端中开发 Python GUI 上位机项目。  
当前工作目录建议为：

`D:\Desktop\STM32G474\Pydisplay`

Python 解释器固定使用：

`D:\Code\anaconda24\envs\Pydisplay_env\python`

项目目标：在现有文件夹中实现一个基于 PySide6 + PyQtGraph 的 Python 上位机子项目，用于替代现有 LabVIEW 上位机，完成 STM32G474 通过 HJ131/HJ380 蓝牙串口链路发送的数据接收、协议解析、实时绘图、控制命令发送、数据记录、链路健康监控和回放模式。

---

## 1. 总体工作原则

1. 不要一次性盲目重写全部工程。
2. 每个阶段必须先阅读现有源码、文档和项目结构，再小步实现。
3. 每个阶段完成后必须运行可执行的最小测试或验证命令。
4. 每个阶段测试通过后，使用 git 提交保存。
5. 对通信协议、控制命令、字节序、校验方式、字段含义、缩放系数等内容禁止臆造。
6. 若协议定义不清楚，必须先输出“协议分析报告”和“待用户确认问题清单”，暂停后续协议相关实现。
7. GUI 主线程只能做界面更新和绘图，禁止在主线程中进行串口阻塞读取、协议解析重负载、文件写入。
8. 所有文件写入必须由记录线程批量写入，禁止每帧 flush，禁止每帧 pandas append。
9. 优先保证长时间运行稳定性，再优化界面美观。
10. 所有中文按钮、标签、状态提示不得乱码。

---

## 2. 已知项目背景

- MCU：STM32G474
- 固件仓库：`https://github.com/Scp-918/PulseTIMR2/tree/Single`
- 构建系统：CMake
- 下位机蓝牙发送模块：HJ131
- 上位机蓝牙接收模块：HJ380，表现为串口数据源
- 传感器手册或说明位于工程的 `sensorlist` 部分
- 目标 Python GUI 技术栈：PySide6 + PyQtGraph
- 目标开发目录：`D:\Desktop\STM32G474\Pydisplay`
- Python 环境：`Pydisplay_env`，Python 3.11
- 解释器路径：`D:\Code\anaconda24\envs\Pydisplay_env\python`

已安装包包括：

- pyside6
- pyqtgraph
- pyserial
- numpy
- pandas
- scipy
- matplotlib
- psutil
- packaging
- pyyaml
- pytest
- pytest-qt
- pytest-cov
- pytest-timeout
- ruff
- black
- mypy
- isort
- ipykernel
- pyinstaller
- git
- ripgrep
- nodejs

Codex 已安装：

- Context7 MCP
- OpenAI Developer Docs MCP

---

## 3. 修改代码前必须先检查的文件和内容

在写任何 Python GUI 代码前，必须先完成源码和文档调查。至少检查以下内容：

### 3.1 固件源码

在固件仓库或本地工程中搜索：

- 串口 / BLE 发送相关源码
- HJ131 / HJ380 相关通信代码
- `UART`
- `USART`
- `HAL_UART_Transmit`
- `HAL_UART_Transmit_DMA`
- `printf`
- `BLE`
- `HJ131`
- `HJ380`
- `frame`
- `packet`
- `header`
- `tail`
- `checksum`
- `crc`
- `metadata`
- `PPG`
- `IMU`
- `acc`
- `gyro`
- `Uh`
- `Uc`
- `UD`
- `mode`
- `LED`
- `range`
- `pulse`
- `command`
- `cmd`

优先使用：

```powershell
rg -n "AA|BB|CC|frame|packet|checksum|crc|UART|USART|HAL_UART|BLE|HJ131|HJ380|PPG|IMU|gyro|acc|Uh|Uc|UD|command|cmd|LED|mode|range|pulse" .
```

### 3.2 sensorlist

必须检查 sensorlist 中的：

* 传感器型号
* PPG 通道定义
* IMU 数据格式
* 电压通道定义
* 原始 ADC / 寄存器数据与物理量的缩放关系
* LED 亮度、PPG mode、PPG 量程、脉宽、IMU 量程的合法范围

### 3.3 LabVIEW 文件或导出信息

若可读取 LabVIEW 文件、前面板截图、控件名称、常量、公式或导出文档，必须检查：

* 原 LabVIEW 的串口配置
* 波特率默认值
* 控制按钮对应的命令
* 字段解析顺序
* 缩放系数
* UD 公式
* 曲线名称和单位
* 坏帧统计逻辑
* 记录文件格式

### 3.4 协议确认项目

必须明确记录以下协议项：

* 帧头：用户说明当前为 `0xAA 0xBB`，仍需在源码中定位依据
* 帧尾：用户说明当前为 `0xCC`，仍需在源码中定位依据
* 帧总长度
* payload 长度
* 字段顺序
* 字段类型：uint8 / int16 / uint16 / int32 / float / fixed-point 等
* 字节序：little-endian / big-endian
* 采样序号或帧序号
* 时间戳是否由下位机发送
* PPG_G / PPG_R / PPG_IR 的原始字段和缩放系数
* 加速度计三轴字段和缩放系数
* 陀螺仪三轴字段和缩放系数
* 4 路 Uh 字段和缩放系数
* 4 路 Uc 字段和缩放系数
* 2 路 UD 是否下位机发送，还是上位机计算
* 校验方式：sum / xor / CRC8 / CRC16 / 其他
* 校验覆盖范围
* 控制命令格式
* 控制命令 ACK / NACK 是否存在
* 协议版本号是否存在

---

## 4. 禁止假设的内容

以下内容不得猜测，不得用“常见写法”代替源码确认：

1. 帧头、帧尾、帧长度。
2. checksum / CRC 算法。
3. 字节序。
4. payload 字段顺序。
5. PPG / IMU / 电压缩放系数。
6. 控制命令格式。
7. 控制命令参数合法范围。
8. 下位机是否发送 ACK。
9. 采样率是否严格为 100 Hz。用户需求为 100 Hz 全量记录，但实际帧率必须通过源码或实测统计确认。
10. `UD = (Uh - Uc) / (k - Uc)` 中 k 的单位和与 Uc 的量纲关系。必须在 UI 中提示 k 与 Uc 使用同一电压单位，除非源码或文档另有定义。

当以上内容不明确时，必须先输出：

* 已确认内容
* 证据文件与行号
* 未确认内容
* 建议用户确认的问题
* 临时不可继续实现的模块

---

## 5. 推荐目录结构

建议在 `D:\Desktop\STM32G474\Pydisplay` 下形成如下结构：

```text
Pydisplay/
  AGENTS.md
  README.md
  pyproject.toml
  requirements.txt
  run_pydisplay.ps1
  src/
    pydisplay/
      __init__.py
      __main__.py
      app.py
      config/
        __init__.py
        defaults.yaml
        protocol.yaml
      core/
        __init__.py
        models.py
        constants.py
        ring_buffer.py
        metrics.py
      protocol/
        __init__.py
        frame_parser.py
        checksum.py
        decoder.py
        commands.py
        protocol_report.md
      io/
        __init__.py
        serial_reader.py
        recorder.py
        replay.py
      gui/
        __init__.py
        main_window.py
        widgets_serial.py
        widgets_control.py
        widgets_record.py
        widgets_health.py
        widgets_replay.py
        plots.py
        styles.py
      utils/
        __init__.py
        paths.py
        timebase.py
        logging.py
        version.py
  tests/
    test_parser.py
    test_decoder.py
    test_recorder.py
    test_replay.py
    test_commands.py
  docs/
    protocol_analysis.md
    data_format.md
    user_guide.md
  sample_data/
    README.md
  records/
    .gitkeep
```

说明：

* `protocol_report.md` / `docs/protocol_analysis.md` 必须先于完整 GUI 实现产出。
* `config/protocol.yaml` 只允许写入已从源码或文档确认的协议定义。
* `records/` 用于默认记录输出，但实际记录路径应允许用户在 GUI 中选择。
* `sample_data/` 可放入模拟数据或脱敏测试数据，不要提交大体积实验原始数据。
* 不要把固件仓库完整复制进 Pydisplay，除非用户明确要求。只引用路径、commit、关键证据。

---

## 6. 模块职责

### 6.1 `protocol/frame_parser.py`

负责字节流同步和拆帧：

* 输入连续 bytes 流。
* 根据已确认帧头 `0xAA 0xBB` 和帧尾 `0xCC` 找帧。
* 维护状态机。
* 输出 RawFrame 对象。
* 统计坏帧、resync 次数、缓冲区长度。
* 坏帧只统计，不导致整段数据流丢失。
* 解析器不得依赖 GUI。

### 6.2 `protocol/checksum.py`

负责校验算法：

* 只实现源码或文档确认过的校验算法。
* 单独测试 checksum 正确性。
* 对坏帧返回校验失败原因，不直接丢弃所有后续数据。

### 6.3 `protocol/decoder.py`

负责 payload 解码：

* 输入 RawFrame。
* 输出 DecodedSample。
* 处理字段类型、字节序、缩放系数。
* 计算 UD：
  `UD = (Uh - Uc) / (k - Uc)`
* 避免除零或接近零导致异常。
* 保留 PC 接收时间戳、相对时间、帧序号或采样序号。

### 6.4 `protocol/commands.py`

负责控制命令：

* PPG mode
* LED 亮度
* PPG 量程
* 脉宽
* IMU 量程

命令格式必须从固件源码确认。发送前必须做合法性检查。

### 6.5 `io/serial_reader.py`

负责串口读取线程：

* 使用 pyserial。
* 支持串口号、波特率配置。
* 支持打开、关闭、重连。
* 串口异常不允许卡死 GUI。
* 识别端口占用、HJ380 拔出、蓝牙断连、读取超时。
* 将读取到的 bytes 通过 Queue 或 Qt Signal 传递给 Parser。

### 6.6 `io/recorder.py`

负责记录线程：

* 批量写入 raw_frames.bin。
* 批量写入 decoded.csv。
* 写 metadata.json。
* 不允许 GUI 主线程写文件。
* 不允许每帧 flush。
* 不允许每帧 pandas append。
* 记录 100 Hz 全量数据。
* 支持安全停止，停止时 flush 并关闭文件。

### 6.7 `io/replay.py`

负责回放：

* 支持 raw_frames.bin 回放。
* 支持 decoded.csv 回放。
* 模拟真实 100 Hz 数据节奏。
* 支持暂停、继续、倍速、慢速。
* 回放时复用 Parser / Decoder / Plot 管线，尽量避免另写一套逻辑。

### 6.8 `gui/main_window.py`

负责主窗口组合：

* 串口连接区
* 下位机控制区
* 记录设置区
* 链路健康监控区
* 实时绘图区
* 回放区

### 6.9 `gui/plots.py`

负责 PyQtGraph 曲线管理：

* 3 色 PPG
* 3 轴加速度计
* 3 轴陀螺仪
* 4 路 Uh
* 4 路 Uc
* 2 路 UD

要求：

* 每个曲线窗口只显示最近 N 秒。
* 默认绘图刷新率 20 Hz，可配置 10–30 Hz。
* 支持暂停绘图但继续记录。
* 支持隐藏部分曲线降低负载。
* 坐标轴、单位、标题清楚。
* 避免每帧重建曲线对象。
* 使用 ring buffer 或 deque 保存最近窗口数据。

### 6.10 `core/metrics.py`

负责链路健康统计：

* bytes/s
* 有效帧率
* 坏帧率
* resync 次数
* 串口缓冲区字节数
* 解析缓冲字节数
* 绘图 FPS
* 记录队列长度
* 串口连接状态
* 记录状态

状态栏刷新频率 1–5 Hz，禁止每帧更新 QLabel。

---

## 7. 推荐数据流架构

实时采集数据流：

```text
HJ380 串口
  -> SerialReader 线程
  -> byte_queue
  -> Parser / FrameParser
  -> RawFrame
  -> Checksum
  -> Decoder
  -> DecodedSample
  -> plot_queue / recorder_queue / metrics
  -> GUI 定时刷新绘图
  -> RecorderWorker 批量写入
```

控制命令数据流：

```text
GUI 控件输入
  -> 参数合法性检查
  -> commands.py 组包
  -> SerialWriter / SerialReader 线程安全发送
  -> 状态栏提示发送结果
```

回放数据流：

```text
raw_frames.bin 或 decoded.csv
  -> ReplayWorker
  -> 模拟 100 Hz 节奏
  -> Parser / Decoder 或 DecodedSample
  -> plot_queue / metrics
```

---

## 8. 协议解析状态机要求

必须实现清晰的解析状态机，至少包括：

1. `FIND_HEADER`

   * 在连续 bytes 中搜索帧头 `0xAA 0xBB`。
   * 丢弃帧头之前的噪声字节，并计入 resync 或 noise 统计。

2. `READ_BODY`

   * 根据已确认帧长度读取完整帧体。
   * 若采用变长帧，则必须从协议字段确认 payload length 的位置。

3. `READ_TAIL`

   * 确认帧尾 `0xCC`。
   * 若帧尾不匹配，进入 resync。

4. `CHECKSUM`

   * 根据确认的校验算法计算并比较。
   * 校验失败计入坏帧。
   * 校验失败帧仍可选择记录 raw，但 decoded 需标记 invalid，不可误当有效数据。

5. `RESYNC`

   * 从当前缓冲区中重新查找下一个帧头。
   * 避免一次坏帧导致后续所有数据失步。

统计项至少包括：

* total_frames
* valid_frames
* bad_frames
* bad_frame_ratio
* checksum_fail_count
* tail_mismatch_count
* length_error_count
* resync_count
* parser_buffer_bytes

---

## 9. 并发设计要求

### 9.1 GUI 主线程

GUI 主线程只允许：

* 响应按钮点击
* 更新控件状态
* 定时刷新图表
* 定时刷新健康监控显示
* 发送线程安全请求

禁止：

* 串口阻塞读取
* 大量 bytes 解析
* CSV / bin 文件写入
* pandas append
* 长时间 for 循环处理历史数据

### 9.2 串口线程

串口读取线程负责：

* 打开串口
* 读取 bytes
* 捕获串口异常
* 向 parser 投递 bytes
* 提供连接状态
* 支持关闭和重连

异常必须转换为状态信息，不允许未捕获异常导致程序退出。

### 9.3 解析与解码

解析和解码可以在串口线程中做轻量处理，也可以独立 Parser Worker。若实时负载较高，优先解耦为独立 worker。

要求：

* Parser 不依赖 Qt GUI 控件。
* Decoder 不依赖 Qt GUI 控件。
* 解析结果通过 Queue 或 Signal 传递。

### 9.4 记录线程

RecorderWorker 必须独立：

* 接收 raw frame 队列
* 接收 decoded sample 队列
* 批量写入
* 停止时 flush
* 暴露记录队列长度和错误状态

### 9.5 回放线程

ReplayWorker 必须独立：

* 不阻塞 GUI。
* 可暂停、继续、停止。
* 可调节倍速。
* 可使用 QThread 或 Python thread，但与 GUI 通信必须线程安全。

---

## 10. 数据记录格式

每次记录建议创建一个独立目录：

```text
records/
  2026-05-10_实验名/
    raw_frames.bin
    decoded.csv
    metadata.json
    run.log
```

### 10.1 `raw_frames.bin`

必须记录原始帧与时间戳，便于复盘协议问题。

推荐格式：

```text
MAGIC: 8 bytes，例如 PYDSPRAW
VERSION: uint16
RECORD_COUNT: 可选，停止时回填；若不回填，则 metadata 记录数量
然后重复：
  pc_timestamp_ns: uint64
  frame_len: uint16 或 uint32
  flags: uint16
  raw_frame_bytes: frame_len bytes
```

注意：

* 具体二进制头格式可以先在 `docs/data_format.md` 中定义。
* 若尚未实现回填 record_count，不要破坏可顺序读取能力。
* raw 记录应尽量包含坏帧原始内容，用于调试协议。

### 10.2 `decoded.csv`

用于 Excel / Origin / MATLAB。

建议字段：

```text
pc_time_iso
pc_time_ns
t_rel_s
frame_index
sample_index
valid
checksum_ok
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
k
parser_state
error_code
```

若字段无法从协议确认，先不要写死最终字段名；在协议分析报告中列为待确认。

### 10.3 `metadata.json`

至少包含：

```json
{
  "serial": {
    "port": "",
    "baudrate": 0
  },
  "experiment": {
    "record_start_time": "",
    "record_end_time": "",
    "operator": "",
    "notes": ""
  },
  "parameters": {
    "k": null,
    "ppg_mode": null,
    "led_brightness": null,
    "ppg_range": null,
    "pulse_width": null,
    "imu_range": null
  },
  "software": {
    "name": "Pydisplay",
    "version": "",
    "python_version": "",
    "pyside6_version": "",
    "pyqtgraph_version": "",
    "platform": ""
  },
  "firmware": {
    "repository": "https://github.com/Scp-918/PulseTIMR2/tree/Single",
    "commit": "",
    "branch": "Single"
  },
  "protocol": {
    "version": "",
    "frame_header": "AA BB",
    "frame_tail": "CC",
    "frame_length": null,
    "endianness": "",
    "checksum": "",
    "source_evidence": []
  },
  "csv_schema": [],
  "recording": {
    "raw_frames_file": "raw_frames.bin",
    "decoded_csv_file": "decoded.csv",
    "sample_rate_target_hz": 100,
    "flush_policy": "batch"
  }
}
```

---

## 11. GUI 功能要求

界面必须中文化，分区合理：

1. 串口连接区

   * 串口号
   * 波特率
   * 刷新端口
   * 打开
   * 关闭
   * 重连
   * 连接状态提示

2. 下位机控制区

   * PPG mode
   * LED 亮度
   * PPG 量程
   * 脉宽
   * IMU 量程
   * 发送控制命令
   * 命令发送状态

3. 记录设置区

   * 记录路径
   * 文件名前缀或实验名
   * 开始记录
   * 停止记录
   * 当前记录状态

4. 链路健康监控区

   * bytes/s
   * 有效帧率
   * 坏帧率
   * resync 次数
   * 串口缓冲区字节数
   * 解析缓冲区字节数
   * 绘图 FPS
   * 记录队列长度
   * 串口连接状态
   * 记录状态

5. 实时绘图区

   * PPG 三色曲线
   * 加速度计三轴
   * 陀螺仪三轴
   * 4 路 Uh
   * 4 路 Uc
   * 2 路 UD
   * 最近 N 秒窗口
   * 暂停绘图
   * 隐藏曲线
   * 刷新率设置，默认 20 Hz

6. 回放区

   * 选择 raw_frames.bin
   * 选择 decoded.csv
   * 开始回放
   * 暂停
   * 继续
   * 停止
   * 倍速 / 慢速

---

## 12. 性能和防卡顿要求

1. 记录频率：100 Hz 全量。
2. 绘图刷新率：默认 20 Hz，可选 10–30 Hz。
3. 状态显示刷新率：1–5 Hz。
4. 不要每帧更新 QLabel。
5. 不要每帧重建 PlotDataItem。
6. 不要每帧全量重绘历史数据。
7. 使用 ring buffer / deque 保存最近 N 秒数据。
8. 记录使用批量写入。
9. CSV 写入使用 csv.writer 或缓冲文本写入，不使用 pandas append。
10. raw bin 使用二进制缓冲写入。
11. 队列需要设置合理上限或高水位报警。
12. 队列积压时 GUI 显示警告，不要无声丢数据。
13. 串口异常、蓝牙断连、设备拔出时 GUI 不应卡死。

---

## 13. 异常处理要求

必须处理并显示明确状态：

* 串口不存在
* 串口被占用
* 打开串口失败
* 读取超时
* HJ380 拔出
* 蓝牙断连
* 帧头丢失
* 帧尾不匹配
* 校验失败
* payload 长度错误
* 字段解码失败
* UD 分母接近 0
* 记录路径不存在或不可写
* 磁盘空间不足
* 记录线程异常
* 回放文件格式错误
* 回放文件版本不兼容

异常提示必须包含：

* 用户可理解的中文提示
* 内部错误日志
* 是否可重试
* 建议操作

---

## 14. 代码风格要求

1. Python 3.11。
2. 使用 type hints。
3. 核心数据结构优先使用 dataclass。
4. 协议、解析、解码、记录逻辑必须可单元测试。
5. GUI 层与核心逻辑分离。
6. 避免全局可变状态。
7. 日志使用 logging，不要散落 print。
8. 中文 UI 文案集中管理或至少保持一致。
9. 复杂模块写清楚中文注释和 docstring。
10. 不要引入未安装的新依赖；若确需新增依赖，先报告原因并等待用户确认。
11. 格式化和检查命令：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m black .
D:\Code\anaconda24\envs\Pydisplay_env\python -m isort .
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest -q
```

12. 可选 mypy：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m mypy src
```

若 mypy 初期噪声过多，可先报告，不强行一次性解决所有类型问题。

---

## 15. 阶段性开发步骤

### Phase 0 — 项目探查

目标：

* 确认当前目录结构。
* 确认是否为 git 仓库。
* 确认 Python 解释器可用。
* 确认已安装依赖可导入。
* 搜索固件源码和文档中的协议定义。

输出：

* `docs/protocol_analysis.md`
* 待确认问题清单
* 初始项目结构建议

验证：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python --version
D:\Code\anaconda24\envs\Pydisplay_env\python -c "import PySide6, pyqtgraph, serial, numpy, pandas; print('ok')"
```

通过后 git commit。

### Phase 1 — 协议模型与解析器骨架

目标：

* 定义 RawFrame、DecodedSample、ProtocolStats。
* 实现 frame parser 状态机。
* 实现 checksum 占位接口，但只填入已确认算法。
* 加入 parser 单元测试。

验证：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest tests/test_parser.py -q
```

通过后 git commit。

### Phase 2 — Decoder 与命令格式

目标：

* 根据已确认字段顺序和缩放系数实现 decoder。
* 实现 UD 计算。
* 实现 commands.py。
* 加入 decoder 和 command 单元测试。

前提：

* 协议和控制命令已确认。
* 若未确认，停止并报告。

通过后 git commit。

### Phase 3 — 串口读取与最小 CLI 验证

目标：

* 实现 SerialReader。
* 实现串口打开、关闭、重连。
* 实现异常捕获。
* 可以在无 GUI 状态下打印帧率和坏帧率。

通过后 git commit。

### Phase 4 — 数据记录

目标：

* 实现 raw_frames.bin。
* 实现 decoded.csv。
* 实现 metadata.json。
* 实现批量写入。
* 实现记录停止时 flush 和关闭。

验证：

* 写入一段模拟数据。
* 回读 raw 和 csv。
* 检查 metadata 字段完整性。

通过后 git commit。

### Phase 5 — GUI 框架

目标：

* 实现主窗口。
* 实现串口连接区。
* 实现控制区。
* 实现记录区。
* 实现健康监控区。
* 实现空数据绘图布局。

验证：

* GUI 可启动。
* 中文不乱码。
* 关闭窗口无线程残留。

通过后 git commit。

### Phase 6 — 实时绘图

目标：

* 使用 PyQtGraph 绘制所有曲线。
* 实现最近 N 秒窗口。
* 实现暂停绘图但继续记录。
* 实现隐藏曲线。
* 显示绘图 FPS。

验证：

* 使用模拟 100 Hz 数据源运行 5–10 分钟不卡顿。
* 记录仍完整。

通过后 git commit。

### Phase 7 — 回放模式

目标：

* raw_frames.bin 回放。
* decoded.csv 回放。
* 100 Hz 节奏模拟。
* 暂停、继续、停止、倍速、慢速。

通过后 git commit。

### Phase 8 — 集成验收与打包准备

目标：

* README 使用说明。
* docs/data_format.md。
* docs/user_guide.md。
* 可选 PyInstaller 打包脚本。
* 全量测试。

验证：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest -q
D:\Code\anaconda24\envs\Pydisplay_env\python -m pydisplay
```

通过后 git commit。

---

## 16. 验收标准

最终项目至少满足：

1. 能启动中文 PySide6 GUI。
2. 能选择串口号和波特率。
3. 能打开、关闭、重连串口。
4. 串口异常时 GUI 不死锁、不崩溃。
5. 能基于源码确认过的协议解析数据。
6. 能显示坏帧数量、坏帧比例、resync 次数。
7. 能解算 PPG、IMU、Uh、Uc、UD。
8. 能实时绘图，默认 20 Hz 刷新。
9. 能暂停绘图但继续记录。
10. 能隐藏部分曲线。
11. 能发送已确认格式的下位机控制命令。
12. 能记录 raw_frames.bin、decoded.csv、metadata.json。
13. 记录线程独立，不阻塞 GUI。
14. 能从 raw_frames.bin 回放。
15. 能从 decoded.csv 回放。
16. 回放支持暂停、继续、倍速或慢速。
17. 健康监控区 1–5 Hz 刷新。
18. 模拟 100 Hz 数据至少运行 10 分钟无明显卡顿。
19. 单元测试覆盖 parser、decoder、recorder、replay、commands 的关键逻辑。
20. README 说明如何运行、如何记录、如何回放、如何排查串口问题。

---

## 17. 不确定时必须暂停并报告的问题清单

遇到以下问题，Codex 必须暂停实现相关模块并报告：

1. 找不到固件中的发送帧定义。
2. 找不到 checksum / CRC 算法。
3. 帧头、帧尾、帧长与用户描述不一致。
4. payload 字段顺序无法确认。
5. 字节序无法确认。
6. PPG / IMU / 电压缩放系数无法确认。
7. 控制命令格式无法确认。
8. 控制命令参数合法范围无法确认。
9. LabVIEW 与固件协议不一致。
10. sensorlist 与固件实现不一致。
11. 下位机是否发送帧序号无法确认。
12. 100 Hz 是否为真实帧率无法确认。
13. UD 公式中的 k 单位无法确认。
14. raw bin 格式需要兼容现有文件但现有格式未知。
15. 需要新增未安装依赖。
16. 需要修改固件源码。
17. 需要访问硬件但当前环境无硬件。
18. 需要解析 LabVIEW 专有文件但缺少可读导出信息。
19. 出现协议证据互相矛盾。
20. 用户需求与源码现实不一致。

报告格式：

```text
## 暂停原因
说明为什么不能继续。

## 已确认内容
列出证据文件、函数名、行号。

## 未确认内容
列出缺失信息。

## 风险
说明若强行实现可能造成的问题。

## 需要用户确认
列出明确问题，尽量是可回答的问题。
```

---

## 18. Git 工作要求

每个阶段成功后执行：

```powershell
git status
git add .
git commit -m "阶段说明"
```

提交信息建议：

* `init pydisplay project scaffold`
* `add protocol analysis report`
* `add frame parser state machine`
* `add decoder and command builder`
* `add serial reader worker`
* `add recorder worker`
* `add pyqtgraph main gui`
* `add replay mode`
* `add docs and validation tests`

若当前目录不是 git 仓库，先报告并询问是否初始化，不要擅自覆盖已有 git 结构。

---

## 19. 运行命令约定

从 PowerShell 进入项目目录：

```powershell
cd D:\Desktop\STM32G474\Pydisplay
```

运行 GUI：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m pydisplay
```

运行测试：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m pytest -q
```

运行格式化：

```powershell
D:\Code\anaconda24\envs\Pydisplay_env\python -m black .
D:\Code\anaconda24\envs\Pydisplay_env\python -m isort .
D:\Code\anaconda24\envs\Pydisplay_env\python -m ruff check .
```

---

## 20. MCP 使用建议

Codex 已配置 Context7 MCP 和 OpenAI Developer Docs MCP。

使用原则：

1. 对 PySide6、PyQtGraph、pyserial、pytest-qt 等库 API 不确定时，优先用 Context7 MCP 查当前文档。
2. 对 Codex CLI、AGENTS.md、skills、MCP 使用方式不确定时，使用 OpenAI Developer Docs MCP。
3. 不要用 MCP 查询代替本地源码协议确认。通信协议必须以固件源码、sensorlist、LabVIEW 或项目文档为准。
4. 查询外部文档后，仍需在代码注释或文档中说明本项目采用的具体实现选择。

---

## 21. 本项目的最高优先级

优先级从高到低：

1. 不臆造协议。
2. 不阻塞 GUI。
3. 不丢失 raw 数据。
4. 长时间运行稳定。
5. 数据记录可复盘。
6. 实时绘图不卡顿。
7. 中文界面清晰。
8. 代码模块化、可测试、可维护。
