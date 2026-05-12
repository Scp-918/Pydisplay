# Pydisplay 中文说明文档

这份文档面向刚开始接触 Python 上位机、串口通信和 GUI 的同学。它会用尽量直白的语言说明：这个项目做什么、目录怎么分工、数据怎么流动、每个功能模块在哪里、以后应该从哪些文件开始读。

## 1. 项目一句话说明

Pydisplay 是一个运行在电脑上的 Python 上位机程序。它通过电脑端的 HJ380 蓝牙串口模块接收 STM32G474 下位机经 HJ131 蓝牙模块发来的数据，然后完成：

1. 打开和关闭串口；
2. 持续接收原始 bytes；
3. 按固件真实协议解析 51 字节数据帧；
4. 解码 PPG、IMU、Uh、Uc、UD；
5. 用 PySide6 + PyQtGraph 实时绘图；
6. 把数据记录成 `raw_frames.bin`、`decoded.csv`、`metadata.json`；
7. 支持用记录文件回放，方便无硬件时调试界面；
8. 显示链路健康状态，比如 bytes/s、有效帧率、坏帧率、resync 次数等。

## 2. 硬件和数据流关系

实际硬件链路可以理解成下面这样：

```text
STM32G474 下位机
  -> HJ131 蓝牙发送模块
  -> 空中蓝牙链路
  -> HJ380 蓝牙接收模块
  -> 电脑 COM 串口
  -> Pydisplay Python 程序
```

Pydisplay 只直接操作电脑上的串口，也就是 HJ380 对应的 COM 口。它不会直接控制 HJ131，也不会直接访问 STM32 的内存。

## 3. 如何启动

在 Windows + VS Code 终端中运行：

```powershell
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

如果你不熟悉命令行，也可以直接在项目根目录中双击：

```text
Start_Pydisplay.bat
```

这个文件会自动进入当前项目目录，并通过 `conda run -n Pydisplay_env python -m pydisplay` 启动上位机。也就是说，平时使用时可以把它当作“启动按钮”。如果双击后提示找不到 `conda`，说明当前 Windows 环境变量里没有 conda，此时请改用 Anaconda Prompt 或 VS Code 终端执行上面的命令行启动方式。

如果只是想确认程序能不能创建 GUI 主窗口，但不想真正打开长期运行窗口，可以运行：

```powershell
conda run -n Pydisplay_env python -m pydisplay --smoke-test
```

它应该输出：

```text
Pydisplay 上位机
```

## 4. 推荐先读哪些文件

如果你是第一次看这个项目，推荐按下面顺序阅读：

1. `readme_Chinese.md`：当前这份中文总览。
2. `docs/protocol_analysis.md`：真实固件协议来源，所有 parser/decoder 常量都要能追溯到这里。
3. `pydisplay/protocol/constants.py`：协议常量，如帧头、帧尾、帧长、字段 offset。
4. `pydisplay/protocol/parser.py`：如何从连续 bytes 中找出完整合法帧。
5. `pydisplay/protocol/decoder.py`：如何把一帧二进制数据变成 PPG、IMU、Uh、Uc、UD。
6. `pydisplay/gui/main_window.py`：GUI 主窗口如何把串口、记录、回放、绘图和健康监控串起来。
7. `tests/`：每个核心功能都有无硬件测试，适合边看边运行。

## 5. 项目目录结构说明

```text
Pydisplay/
  README.md                  英文/简明项目说明
  readme_Chinese.md          当前中文详细说明
  Start_Pydisplay.bat        Windows 双击启动脚本
  pyproject.toml             Python 项目和 pytest 配置
  AGENTS.md                  Codex 开发规则，不是运行代码

  docs/
    protocol_analysis.md     固件协议分析结论
    protocol_questions.md    已解决和未解决的协议问题
    data_format.md           raw bin、CSV、metadata 格式
    manual_test_checklist.md 人工验收清单
    user_manual.md           简短用户手册

  pydisplay/
    app.py                   程序启动入口逻辑
    __main__.py              支持 python -m pydisplay
    config.py                全局配置
    logging_config.py        日志配置

    protocol/                协议解析和命令编码
    io/                      串口发现、打开、读取、写入
    recorder/                raw/csv/metadata 数据记录
    replay/                  raw/csv 文件回放
    gui/                     PySide6 图形界面
    services/                pipeline、health monitor、data bus

  tests/                     pytest 自动化测试
  scripts/                   辅助脚本
```

## 6. 协议模块如何工作

协议模块在 `pydisplay/protocol/` 下。

### 6.1 `constants.py`

这里保存固件已经确认的协议常量，例如：

- 数据帧帧头：`AA BB`
- 数据帧帧尾：`CC`
- 数据帧长度：51 字节
- payload 长度：45 字节
- checksum：payload 字节 2..46 的 XOR
- 各字段 offset，如 `PPG_G` 从 byte 26 开始

这个文件不能随便加“猜测值”。如果协议有变化，要先更新 `docs/protocol_analysis.md`，再改这里。

### 6.2 `parser.py`

串口读出来的是连续 bytes，不会保证“一次 read 正好一帧”。parser 的任务是：

1. 在 byte stream 中寻找帧头 `AA BB`；
2. 等待足够的 51 字节；
3. 检查帧尾 `CC`；
4. 计算并检查 XOR checksum；
5. 输出 `ParsedFrame`；
6. 遇到坏帧时 resync，不让后续好帧被整段丢弃。

它支持半包、粘包、噪声、坏 checksum、坏帧尾和 buffer 限制。

### 6.3 `decoder.py`

decoder 把 `ParsedFrame` 变成 `DecodedSample`。主要转换规则：

- PPG：固件输出 raw count，不再做物理量换算；
- ACC：按 IMU 量程换算成 g；
- GYRO：按 IMU 量程换算成 dps；
- Uc/Uh：AD4007 int24 原始码换算成电压；
- UD：

```text
UD = (Uh - Uc) / (k - Uc)
```

其中：

- `UD1` 使用通道 2 的 `Uh2 / Uc2`；
- `UD2` 使用通道 3 的 `Uh3 / Uc3`；
- 如果 `k - Uc` 接近 0，返回 `NaN`，避免程序崩溃。

### 6.4 `commands.py`

这里负责把 GUI 里的控制参数编码成固件确认的 13 字节控制帧：

```text
AB CD mode submode led_g led_r led_ir ppg_range pulse gyro_range accel_range EF FA
```

这个控制帧没有 ACK/NACK。GUI 不直接拼 bytes，而是调用这里的 `build_control_command()`。

## 7. 串口 IO 模块如何工作

串口模块在 `pydisplay/io/` 下。

- `port_discovery.py`：列出电脑上的 COM 口；
- `serial_manager.py`：统一管理打开、关闭、重连和状态；
- `serial_reader.py`：后台线程持续读取 bytes；
- `serial_writer.py`：线程安全地发送 bytes 或控制命令；
- `simulated_device.py`：无硬件调试用模拟 decoded sample，明确标注为 simulation only。

GUI 主线程不会阻塞读串口。串口读取由 `SerialReader` 后台线程处理，读到的数据以 `RawChunk` 形式交给 pipeline。

串口连接区现在包含下面几个常用按钮：

1. `刷新串口`：重新扫描电脑上的 COM 口；
2. `打开串口`：打开选中的 HJ380 串口，并默认开始后台接收；
3. `暂停接收`：暂停 `SerialReader` 后台读取循环，但不关闭串口；
4. `开始接收`：从暂停状态恢复读取；
5. `关闭串口`：停止读取并关闭串口；
6. `重连`：关闭后重新打开上一次使用的串口。

`暂停接收` 和 `暂停绘图` 是两件不同的事：`暂停接收` 会让程序暂时不再从串口读新数据；`暂停绘图` 只是不刷新曲线，后台接收和记录仍可继续。

还有一个容易混淆的点：如果当前没有打开串口，但正在进行文件回放，那么串口区的 `暂停接收` 也会同步暂停回放，`开始接收` 会继续回放。这样你不需要专门去回放区找暂停按钮，也能快速停住当前正在进入绘图窗口的数据。

## 8. Pipeline 数据流

实时串口模式的数据流是：

```text
SerialReader
  -> RawChunk
  -> DataPipeline
  -> FrameParser
  -> ParsedFrame
  -> decode_frame()
  -> DecodedSample
  -> RecorderWorker
  -> PlotPanel/RingBuffer
  -> HealthMonitor
```

这个设计的目的：

- 串口读取不阻塞 GUI；
- 记录线程不阻塞 GUI；
- 绘图只保留最近一段数据，防止内存无限增长；
- 健康监控低频刷新，避免每帧更新 QLabel。

## 9. 数据记录文件

点击 GUI 中的 `开始记录` 后，会创建类似目录：

```text
records/
  20260510_033000_experiment/
    raw_frames.bin
    decoded.csv
    metadata.json
```

### 9.1 `raw_frames.bin`

保存原始串口 bytes 或原始帧，适合以后复盘协议问题。即使 decoder 出错，也可以用 raw 文件重新分析。

### 9.2 `decoded.csv`

保存已经解码好的数据，适合 Excel、Origin、MATLAB、Python 后处理。

字段包括：

```text
frame_seq, absolute_seq_u64, segment_id, sample_seq,
PPG_G, PPG_R, PPG_IR, ACC_X/Y/Z, GYRO_X/Y/Z,
Uh1..Uh4, Uc1..Uc4, UD1, UD2, parser_valid
```

为了让 CSV 更适合后处理表格，当前版本不再写入
`relative_time_s`、`timestamp_pc_ns`、`seq_gap`、`lost_before` 和 `source`。
如果用 `decoded.csv` 回放，程序会按照行号自动生成 100 Hz 的回放时间；
如果要分析丢包，可以使用 `frame_seq` 和 `absolute_seq_u64` 重新计算。

### 9.3 `metadata.json`

保存本次记录的上下文，例如：

- 软件版本；
- 固件 repo、branch、commit；
- 串口号、波特率；
- k 值；
- 协议字段布局；
- CSV 字段说明；
- 记录开始和结束时间。

## 10. 回放模式

回放模块在 `pydisplay/replay/` 下。

支持两类文件：

1. `raw_frames.bin`：重新走 parser/decoder，更接近真实链路。程序会先读取 bin 文件里的 `raw_serial_chunk`，用真实 parser 从这些原始 bytes 中提取有效固件帧，然后按固件 `frame_seq` 重建 100 Hz 帧节拍，再把完整 raw frame 重新送进 parser/decoder。这样做的原因是：串口线程的一次 read 不一定正好是一帧，可能只读到单独的 `AA`，也可能一次读到两帧；如果直接使用 chunk 的 PC 时间戳回放，就会出现成组投递和速度偏慢，看起来可能只有约 50 Hz。现在默认回放不修改原始 bin 文件，只修正上位机对回放时间轴的解释；
2. `decoded.csv`：直接恢复 decoded sample，适合无硬件调试界面。因为当前 CSV 不再保存时间戳，回放时会按 100 Hz 用行号生成时间。

支持速度：

```text
0.25x, 0.5x, 1x, 2x, 5x
```

也支持暂停、继续、停止。

回放结束不依赖“文件末尾结束标志”。程序在读入 raw bin 时已经知道可回放记录数量，ReplayWorker 播放完这些记录后会自动进入 `FINISHED` 状态。这样设计的好处是：如果实验中途正常暂停记录、稍后继续记录，不会因为额外插入的“结束标志”干扰后续回放。

如果你发现 raw bin 回放速度和原始采集不一致，可以先用下面的命令检查文件内容：

```powershell
python scripts\inspect_raw_bin.py D:\你的记录目录\raw_frames.bin
```

如果里面有很多 1 字节或一次包含多帧的 `raw_serial_chunk`，这是正常现象，不表示 bin 文件损坏。当前 GUI 默认使用 100 Hz 帧节拍重建来消除这种串口 chunk 抖动。

还有一个容易误判的地方：`有效帧率` 才是回放数据进入 parser/decoder 的速率；`绘图 FPS` 只是界面曲线刷新速率，默认大约 20 FPS。也就是说，数据可以按 100 Hz 回放和记录到缓冲区，但界面不会每来一帧就重画一次，否则 GUI 会更容易卡顿。在 Windows 上，回放线程运行期间还会临时请求 1 ms 计时器精度，避免 10 ms 帧节拍被系统 sleep 精度拖慢。

## 11. GUI 结构

GUI 主窗口在 `pydisplay/gui/main_window.py`。

界面分成：

- 串口连接区；
- 下位机控制区；
- 数据记录区；
- 回放区；
- 链路健康区；
- 实时绘图区。

串口连接区里除了 `打开串口`、`关闭串口`、`重连`，还提供 `开始接收` 和 `暂停接收`。这两个按钮只控制后台串口读取线程，不会修改协议解析规则，也不会直接操作绘图曲线。

左侧控制栏已经做了瘦身：输入框和按钮不会无限撑宽，整体顺序调整为：

```text
串口连接
下位机控制
数据记录
链路健康
回放
```

这样平时更容易看到串口、记录和链路健康状态；回放区放在健康区下面，需要回放时在左侧栏向下滚动即可。

右侧实时绘图区顶部现在只保留三个常用控件：

1. `暂停绘图`：只暂停曲线刷新，不影响串口接收和记录；
2. `清空图表`：一键清空当前屏幕上的曲线缓存，只影响显示，不会停止串口接收，也不会停止后台记录；
3. `X轴长度`：输入最近显示多少秒数据，默认是 5 s，也可以改成 10 s、20 s。

下位机控制区的初始值已经和固件 `Single` 分支 `Core/Src/main.c` 里的 `g_sensor_param_array` 对齐：`k` 默认是 24；PPG mode 默认 `MultiLED`；Multi sub-mode 默认 `G-R-IR`；绿光/红光/IR 亮度默认是 `5/1/1`；PPG 量程默认 `3`；脉宽默认 `3`；陀螺仪量程默认 `500 dps`；加速度计量程默认 `2 g`。这样程序刚启动时，GUI 显示的控制参数和单片机初始化后正在使用的参数一致。

原来挤在顶部的大量曲线勾选框，已经进一步放到绘图区滚动内容的底部。平时首屏尽量留给实时曲线；要隐藏某些曲线时，向下滚动到 `曲线显示选项` 区域勾选即可。

绘图窗口采用 3x3 九宫格逻辑：

```text
a, b, c
a, b, d
f, g, e
```

每个字母表示一个图形区域：

```text
a = 3色 PPG，只绘制 PPG_G / PPG_R / PPG_IR 独立子图，不再绘制合并总图
b = 2/3号传感器 Uh，只绘制 Uh2 / Uh3 独立子图，不再绘制合并总图
c = 2/3号传感器 Uc，只绘制 Uc2 / Uc3 独立子图，不再绘制合并总图
d = UD1 / UD2，只绘制 UD1 / UD2 独立子图，不再绘制合并总图
e = 1/4号传感器 Uh/Uc，分成两个子图：1号传感器 Uh/Uc 一个子图，4号传感器 Uh/Uc 一个子图
f = 3轴 ACC，总图
g = 3轴 GYRO，总图
```

其中 a 和 b 跨两行，占更大的显示空间，因为 PPG 和 2/3 号传感器 Uh 是更常看的信号。a/b/c/d/e 区域内部的独立子图共享 x 轴，便于压缩空间并对齐时间；每个子图的 y 轴保持自适应。e 图中每个子图包含同一传感器的 Uh/Uc 两条曲线，便于直接比较高低电平。大图标题不带 a/b/c/d 字母编号，避免标题显得杂乱。

曲线颜色也按信号含义做了区分，并尽量使用低饱和度颜色：

```text
PPG_G = 绿色，PPG_R = 红色，PPG_IR = 紫色
Uh2 / Uh3 = 红色 / 橙色
Uc2 / Uc3 = 蓝色 / 青色
UD1 / UD2 = 黄色 / 橙色
ACC 三轴 = 蓝色 / 绿色 / 紫色
GYRO 三轴 = 蓝紫色 / 玫红色 / 橄榄色
```

各区域对应文件：

```text
pydisplay/gui/widgets/serial_panel.py
pydisplay/gui/widgets/control_panel.py
pydisplay/gui/widgets/recorder_panel.py
pydisplay/gui/widgets/replay_panel.py
pydisplay/gui/widgets/health_panel.py
pydisplay/gui/widgets/plot_panel.py
```

绘图相关文件在：

```text
pydisplay/gui/plots/
```

其中 `ring_buffer.py` 只保存最近 N 个样本，`plot_manager.py` 初始化 PyQtGraph 曲线并在刷新时调用 `setData()`。

如果曲线只显示成一条竖线，通常说明所有点的 x 坐标都一样。当前版本已经修正了这个问题：实时串口和 raw 回放会把第一条成功解码的数据帧作为时间零点，后续样本的 `relative_time_s` 会随时间递增，因此曲线会沿 x 轴展开。

## 12. 健康监控

健康监控由 `pydisplay/services/health_monitor.py` 实现。

它统计：

- bytes/s；
- total bytes；
- 有效帧率；
- 坏帧率；
- 坏帧比例；
- resync 次数；
- parser buffer 字节数；
- decoded sample rate；
- plot FPS；
- record queue 长度；
- 串口、记录、回放状态；
- 最近错误。

GUI 的健康区定时读取 `HealthSnapshot`，不会每来一帧就刷新 QLabel。

## 13. 如何运行测试

```powershell
pytest
```

当前测试不需要真实串口和硬件，主要覆盖：

- parser 半包、粘包、坏帧恢复；
- decoder 缩放和 UD；
- control command 编码；
- serial IO 状态；
- raw bin 格式；
- metadata；
- replay；
- ring buffer；
- health monitor。

## 14. 常见问题

### 14.1 为什么不能直接编造协议？

因为上位机解析必须和 STM32 固件完全一致。帧长、字段顺序、checksum、缩放公式如果猜错，GUI 看起来可能有曲线，但数据是错的。

### 14.2 为什么保存 raw_frames.bin？

`decoded.csv` 是解码后的结果。如果以后发现 decoder 有 bug，只有 CSV 无法恢复原始数据。`raw_frames.bin` 保留原始 bytes，可以重新解析。

### 14.3 为什么 GUI 不直接读串口？

串口读取可能阻塞。如果放在 GUI 主线程，界面会卡死。项目中用后台线程读串口，GUI 只负责显示和用户操作。

### 14.4 为什么绘图不用 pandas？

pandas 适合离线分析，不适合每帧实时 append 和绘图。实时绘图使用 ring buffer + PyQtGraph。

## 15. 当前已知限制

- 还没有做 HJ380/HJ131 实机验收，需要按 `docs/manual_test_checklist.md` 测试；
- 固件没有协议版本字段，metadata 中记录为 `null`；
- AD4007/PPG 没有额外校准表，当前只使用已确认公式和 raw count。

## 16. 后续开发建议

如果你要继续开发，建议每次只改一个小模块：

1. 先写或更新测试；
2. 修改代码；
3. 运行 `pytest`；
4. 用 GUI smoke test 检查启动；
5. 再提交 git commit。

不要一次性大改 parser、GUI、串口和记录模块。这样出问题时更容易定位。
