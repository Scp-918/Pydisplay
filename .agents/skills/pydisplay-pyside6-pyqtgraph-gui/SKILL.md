# Skill: pydisplay-pyside6-pyqtgraph-gui

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 实现 PySide6 GUI；
- 实现 PyQtGraph 实时绘图；
- 设计中文界面；
- 实现串口连接区；
- 实现下位机控制区；
- 实现记录设置区；
- 实现健康监控区；
- 实现回放区；
- 实现曲线隐藏、暂停绘图、刷新率控制；
- 修改 `pydisplay/gui/` 下的代码。

---

## 2. 项目目标

构建一个适合实验室长期运行的中文 Python 上位机 GUI，实现：

1. 串口连接；
2. 下位机控制；
3. 数据记录；
4. 链路健康监控；
5. 实时绘图；
6. 回放控制；
7. 异常状态提示。

技术栈：

```text
PySide6
PyQtGraph
```

可使用 Context7 MCP 查询 PySide6 / PyQtGraph API，但 GUI 架构必须服从本项目线程和数据流设计。

---

## 3. 推荐文件结构

```text
pydisplay/
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
```

入口文件：

```text
pydisplay/app.py
pydisplay/__main__.py
scripts/run_app.py
```

---

## 4. GUI 总体布局

主窗口建议使用：

```text
QMainWindow
  centralWidget: QWidget
    QVBoxLayout or QHBoxLayout
```

推荐分区：

```text
顶部：串口连接区 + 记录设置区
中部左侧：下位机控制区 + 回放区 + 健康监控区
中部右侧：实时绘图区
底部：状态栏 / 日志提示
```

或使用：

```text
QSplitter
QTabWidget
QGroupBox
```

界面分区必须清楚，中文按钮不能乱码。

---

## 5. 中文界面要求

按钮和标签使用中文，例如：

```text
刷新串口
打开串口
关闭串口
重连
开始记录
停止记录
选择路径
发送控制命令
暂停绘图
恢复绘图
开始回放
暂停回放
继续回放
停止回放
```

状态文本示例：

```text
未连接
已连接
正在重连
串口异常
正在记录
记录已停止
回放中
回放暂停
```

注意：

1. Python 源文件使用 UTF-8；
2. 避免使用系统不支持的字体；
3. 如需设置字体，优先使用常见中文字体或 Qt 默认字体；
4. 不要硬编码只适配某一台电脑的字体路径。

---

## 6. 各 Widget 职责

### 6.1 `serial_panel.py`

负责：

```text
串口刷新
串口选择
波特率选择
打开串口
关闭串口
重连
串口状态显示
```

不直接读写串口，由 signal 通知 controller / pipeline。

建议 signal：

```python
refresh_ports_requested
open_requested(port: str, baudrate: int)
close_requested
reconnect_requested
```

---

### 6.2 `control_panel.py`

负责：

```text
k 值输入
PPG mode
LED 亮度
PPG 量程
脉宽
IMU 量程
发送控制命令
```

要求：

1. 输入合法性检查；
2. 非法值用中文提示；
3. 发送前构造 ControlMetadata；
4. 不直接拼 bytes；
5. 命令 bytes 必须由 `pydisplay.protocol.commands` 生成。

建议 signal：

```python
control_command_requested(metadata)
k_value_changed(k: float)
```

---

### 6.3 `recorder_panel.py`

负责：

```text
记录目录选择
文件名前缀
开始记录
停止记录
记录状态显示
```

不直接写文件。

建议 signal：

```python
start_recording_requested(record_config)
stop_recording_requested
```

---

### 6.4 `health_panel.py`

负责显示：

```text
bytes/s
有效帧率
坏帧率
坏帧数量
坏帧比例
resync 次数
串口缓冲区字节数
解析缓冲字节数
绘图 FPS
记录队列长度
串口连接状态
记录状态
```

要求：

1. 使用 QTimer 以 1–5 Hz 刷新；
2. 不要每帧更新 QLabel；
3. 指标缺失时显示 `--`；
4. 坏帧率过高可用文字提示；
5. 不在这里做复杂计算，指标来自 health monitor。

---

### 6.5 `replay_panel.py`

负责：

```text
选择 raw_frames.bin
选择 decoded.csv
选择回放类型
开始回放
暂停回放
继续回放
停止回放
倍速选择
回放进度
```

建议速度选项：

```text
0.25x
0.5x
1x
2x
5x
```

不直接读文件，由 ReplayWorker 处理。

---

### 6.6 `plot_panel.py`

负责实时绘图区域。

绘图内容：

```text
3 色 PPG
3 轴加速度计
3 轴陀螺仪
4 路 Uh
4 路 Uc
2 路 UD
```

建议分成多个 PlotWidget：

```text
PPG 曲线
加速度计
陀螺仪
Uh 电压
Uc 电压
UD 解算信号
```

每个 plot 需要：

1. 标题；
2. x 轴：时间 / s；
3. y 轴：单位；
4. legend；
5. 自动 y range 或合理自适应；
6. 曲线显示 / 隐藏选项。

---

## 7. PyQtGraph 绘图性能要求

### 7.1 禁止做法

禁止：

1. 每帧创建新的 PlotWidget；
2. 每帧创建新的 PlotDataItem；
3. 每帧 append 到 Python list 且无限增长；
4. 每帧 setLabel / setTitle；
5. 每帧更新所有 QLabel；
6. 绘图和记录使用同一个低效数据结构；
7. pandas 参与实时绘图。

---

### 7.2 推荐做法

1. 初始化时创建所有曲线；
2. 使用 ring buffer 保存最近 N 秒数据；
3. 使用 QTimer 以 10–30 Hz 刷新；
4. 默认刷新率 20 Hz；
5. 每次刷新调用 `curve.setData(x, y)`；
6. 隐藏曲线时跳过 setData；
7. 暂停绘图时停止更新曲线，但继续接收和记录数据。

---

## 8. Ring Buffer 要求

`plots/ring_buffer.py` 负责保存最近 N 秒数据。

输入数据频率约 100 Hz。

如果显示最近 10 秒：

```text
buffer_size >= 100 Hz * 10 s
```

建议加冗余：

```text
buffer_size = sample_rate * window_seconds * 2
```

Ring buffer 保存：

```text
relative_time_s
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

---

## 9. 曲线配置

`curve_config.py` 可定义曲线组：

```python
CurveConfig(
    key="ppg_g",
    label="PPG_G",
    unit="raw or a.u.",
    group="PPG"
)
```

单位必须根据协议分析结果填写；未确认时使用：

```text
a.u.
```

并在协议分析中标记待确认。

---

## 10. GUI 与后台线程通信

后台线程不得直接操作 GUI 控件。

允许：

1. Qt Signal/Slot；
2. queue + QTimer polling；
3. 封装 DataBus。

推荐：

```text
SerialReader / Parser / Decoder
  ↓
thread-safe queue
  ↓
GUI QTimer 批量取数据
  ↓
RingBuffer
  ↓
PlotManager 定时刷新
```

高频 decoded sample 不建议每帧发 Qt signal 更新图表，避免事件队列积压。

---

## 11. GUI 状态管理

建议 MainWindow 维护当前状态：

```text
serial_state
recording_state
replay_state
plot_paused
current_k
current_control_metadata
```

按钮启用/禁用示例：

```text
未连接：打开可用，关闭不可用，发送命令不可用
已连接：打开不可用，关闭可用，发送命令可用
记录中：开始记录不可用，停止记录可用
回放中：开始回放不可用，暂停/停止可用
```

---

## 12. 控制参数合法性检查

GUI 层先做基础检查：

```text
k 必须是有效数字
LED 亮度必须在协议允许范围
PPG mode 必须在协议允许枚举内
PPG range 必须在协议允许枚举内
脉宽必须在协议允许枚举内
IMU range 必须在协议允许枚举内
```

最终检查仍由 `protocol.commands` 执行。

---

## 13. 错误提示

建议使用：

```text
状态栏
QMessageBox
health panel 文本
日志文件
```

原则：

1. 常规状态变化放状态栏；
2. 阻塞操作失败用 QMessageBox；
3. 高频异常不要弹窗刷屏；
4. 详细 traceback 写日志；
5. 用户可理解的信息用中文。

---

## 14. GUI 启动入口

`pydisplay/__main__.py`：

```text
python -m pydisplay
```

应启动 GUI。

`scripts/run_app.py` 可作为开发入口。

---

## 15. 推荐开发步骤

### Step 1：创建 MainWindow 空窗口

确认：

```bash
python -m pydisplay
```

能启动窗口。

### Step 2：实现各 panel 静态布局

先不接真实串口，只完成 UI。

### Step 3：接入 serial panel signal

和 SerialManager 连接。

### Step 4：实现 health panel 定时刷新

使用 mock health snapshot 测试。

### Step 5：实现 plot panel 和 ring buffer

使用模拟 decoded sample 测试 100 Hz 输入和 20 Hz 刷新。

### Step 6：接入真实 decoded sample

从 pipeline 输入数据。

### Step 7：实现曲线隐藏、暂停绘图、窗口秒数设置

### Step 8：接入 recorder panel 和 replay panel

### Step 9：整理中文文案和 README 截图说明

---

## 16. 验收标准

1. `python -m pydisplay` 可启动；
2. 中文按钮和标签正常显示；
3. 串口区、控制区、记录区、健康区、回放区、绘图区分区明确；
4. 100 Hz decoded sample 输入时 GUI 不明显卡顿；
5. 绘图默认 20 Hz；
6. 可暂停绘图但后台继续接收和记录；
7. 可隐藏部分曲线；
8. 健康状态 1–5 Hz 刷新；
9. 不每帧更新 QLabel；
10. 不在 GUI 主线程写文件；
11. 不在 GUI 主线程阻塞读串口。

完成后建议：

```bash
git status
git diff
git add pydisplay/gui pydisplay/app.py pydisplay/__main__.py
git commit -m "feat: implement PySide6 PyQtGraph GUI"
```