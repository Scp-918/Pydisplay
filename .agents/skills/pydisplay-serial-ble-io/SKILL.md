# Skill: pydisplay-serial-ble-io

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 实现串口列表刷新；
- 打开 / 关闭 / 重连 HJ380 串口；
- 从 HJ380 连续读取 HJ131 转发的数据；
- 处理串口异常；
- 发送上位机控制命令；
- 实现无硬件测试用的模拟设备；
- 修改 `pydisplay/io/` 下的代码。

---

## 2. 项目上下文

下位机：

```text
STM32G474 + HJ131 蓝牙模块
```

上位机：

```text
PC + HJ380 蓝牙串口模块
```

Python GUI 通过串口读取 HJ380 数据。

用户要求：

1. 支持选择串口号；
2. 支持选择波特率；
3. 支持打开、关闭、重连；
4. 串口异常时 GUI 不应卡死；
5. 支持端口占用、拔掉 HJ380、蓝牙断连后的明确状态提示和重连；
6. 支持控制命令发送；
7. 可选支持虚拟串口 + 模拟下位机。

---

## 3. 推荐文件位置

```text
pydisplay/
  io/
    __init__.py
    port_discovery.py
    serial_manager.py
    serial_reader.py
    serial_writer.py
    simulated_device.py
```

测试文件：

```text
tests/
  test_serial_state.py
```

---

## 4. 设计原则

1. GUI 主线程不得阻塞读取串口。
2. 串口读写必须与 GUI 解耦。
3. 串口异常必须被捕获并上报。
4. 串口状态必须可观测。
5. 发送命令前必须确认命令格式已由固件协议分析确认。
6. 不得在串口层做 GUI 绘图。
7. 不得在串口层写 decoded.csv。
8. 原始 bytes 应进入 parser 和 recorder。

---

## 5. 串口状态模型

建议定义串口状态枚举：

```python
class SerialState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    RECONNECTING = "reconnecting"
    ERROR = "error"
```

建议定义错误类型：

```python
class SerialErrorKind(Enum):
    PORT_NOT_FOUND = "port_not_found"
    PORT_BUSY = "port_busy"
    PERMISSION_DENIED = "permission_denied"
    DEVICE_REMOVED = "device_removed"
    BLUETOOTH_DISCONNECTED = "bluetooth_disconnected"
    READ_TIMEOUT = "read_timeout"
    WRITE_FAILED = "write_failed"
    UNKNOWN = "unknown"
```

---

## 6. `port_discovery.py`

负责枚举串口。

建议使用：

```python
serial.tools.list_ports.comports()
```

返回信息建议包含：

```python
PortInfo:
    device: str
    description: str
    hwid: str
    manufacturer: str | None
    serial_number: str | None
```

GUI 应显示：

```text
COM3 - USB Serial Device
COM5 - HJ380 / Bluetooth Serial Port
```

如果无法识别 HJ380，也不要阻塞用户手动选择。

---

## 7. `serial_manager.py`

负责串口生命周期管理。

职责：

1. 打开串口；
2. 关闭串口；
3. 重连串口；
4. 保存当前 port 和 baudrate；
5. 管理 SerialReader 和 SerialWriter；
6. 向 GUI / health monitor 报告状态。

推荐接口：

```python
class SerialManager:
    def list_ports(self) -> list[PortInfo]: ...
    def open(self, port: str, baudrate: int) -> None: ...
    def close(self) -> None: ...
    def reconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    def write(self, data: bytes) -> None: ...
```

---

## 8. `serial_reader.py`

负责独立读取串口。

可以使用：

1. `threading.Thread + queue.Queue`
2. 或 `QObject + QThread + Signal`

若 GUI 使用 PySide6，推荐 Qt worker 模式或清晰封装的 Python thread。

### 8.1 读取要求

SerialReader 必须：

1. 连续读取 bytes；
2. 不阻塞 GUI；
3. 支持 stop event；
4. 支持超时；
5. 捕获异常；
6. 记录 bytes/s；
7. 将 raw bytes 送入 parser；
8. 将 raw bytes 或 raw chunks 送入 recorder；
9. 报告串口缓冲区字节数。

### 8.2 pyserial 参数建议

实际参数应可配置：

```python
serial.Serial(
    port=port,
    baudrate=baudrate,
    timeout=0.05,
    write_timeout=0.2,
)
```

读取时可使用：

```python
n_waiting = ser.in_waiting
chunk = ser.read(max(1, n_waiting))
```

避免无休止 busy loop。

---

## 9. `serial_writer.py`

负责发送命令。

职责：

1. 检查串口是否连接；
2. 检查 data 是否为 bytes；
3. 使用锁保护写操作；
4. 捕获 write 异常；
5. flush 可选；
6. 返回发送结果；
7. 将错误上报 GUI。

推荐接口：

```python
class SerialWriter:
    def write(self, data: bytes) -> WriteResult: ...
```

发送命令前必须由 `pydisplay.protocol.commands` 完成编码和参数合法性检查。

---

## 10. 异常处理要求

必须处理：

```text
串口不存在
端口被占用
权限不足
打开失败
读取失败
写入失败
设备拔出
蓝牙断连
关闭失败
重连失败
```

常见 pyserial 异常：

```python
serial.SerialException
serial.SerialTimeoutException
PermissionError
OSError
```

错误处理要求：

1. 不能导致 GUI 崩溃；
2. 不能让线程静默死亡；
3. 必须更新 serial state；
4. 必须写入日志；
5. 必须让 GUI 状态栏显示明确中文提示。

---

## 11. 蓝牙断连处理

HJ380 / HJ131 蓝牙链路可能出现：

1. 串口仍存在，但没有数据；
2. 串口 read 超时；
3. 串口设备消失；
4. 写命令失败；
5. 数据突然变成乱码或坏帧率升高。

处理策略：

1. 串口设备消失：状态变为 `ERROR` 或 `DISCONNECTED`；
2. 长时间无数据：状态提示“已连接但无数据”；
3. 坏帧率升高：由 parser / health monitor 提示；
4. 支持用户点击“重连”。

---

## 12. 重连设计

重连流程：

```text
用户点击重连
  ↓
停止 SerialReader
  ↓
关闭旧 serial object
  ↓
等待短暂间隔
  ↓
重新打开 port
  ↓
重新启动 SerialReader
  ↓
更新 GUI 状态
```

要求：

1. 重连过程中按钮状态要明确；
2. 重连失败要恢复可操作状态；
3. 不能出现多个 reader 线程同时读取同一个串口；
4. close 时要 join 线程或安全停止。

---

## 13. 原始数据流输出

SerialReader 输出 raw bytes chunk：

```python
RawChunk:
    timestamp_ns: int
    data: bytes
    port: str
```

RawChunk 应进入：

```text
Parser
Recorder raw queue
HealthMonitor
```

注意：

1. raw chunk 是串口原始数据；
2. parser 输出的是 parsed frame；
3. decoded sample 是 decoder 输出；
4. 三者不要混淆。

---

## 14. 模拟设备 `simulated_device.py`

虚拟串口 + 模拟下位机是可选项。

实现优先级低于真实 parser 和 GUI。

允许提供独立脚本：

```text
scripts/simulate_device.py
```

要求：

1. 明确标注 simulation only；
2. 不得伪装成真实固件协议；
3. 如果真实协议已经确认，可以生成符合真实协议的模拟帧；
4. 如果真实协议未确认，只能生成 decoded sample 或 mock stream 用于 GUI，不得进入真实 parser；
5. Windows 虚拟串口可能依赖 com0com、tty0tty 或其他工具，如果不可用则跳过。

---

## 15. GUI 交互要求

串口面板至少支持：

```text
刷新串口
选择串口号
选择波特率
打开串口
关闭串口
重连
连接状态显示
错误提示
```

常见状态中文提示：

```text
未连接
正在连接
已连接
正在断开
正在重连
串口不存在
串口被占用
设备已拔出
蓝牙可能断连
发送失败
```

---

## 16. 健康监控指标

Serial IO 层需要提供：

```text
bytes_received_total
bytes_per_second
last_rx_time
serial_buffer_bytes
serial_state
read_error_count
write_error_count
last_error
```

health monitor 每 1–5 Hz 读取一次，不要每帧更新 QLabel。

---

## 17. 禁止事项

禁止：

1. GUI 主线程阻塞读取串口；
2. 在按钮回调中 while True 读串口；
3. 串口异常导致程序崩溃；
4. 发送命令时绕过 `protocol.commands`；
5. 串口线程直接操作 GUI 控件；
6. 多个 reader 同时读同一个 serial object；
7. close 时不停止线程；
8. 为了测试编造固件协议；
9. 没有日志的异常吞掉。

---

## 18. 推荐开发步骤

### Step 1：实现 port discovery

完成串口枚举。

### Step 2：实现 SerialManager 基础 open / close

不接入 GUI，先用简单脚本测试。

### Step 3：实现 SerialReader

能输出 raw chunks。

### Step 4：接入 parser

SerialReader 输出数据给 parser。

### Step 5：实现 SerialWriter

能发送 bytes。

### Step 6：接入 commands

从 GUI 控制参数生成命令 bytes 并发送。

### Step 7：异常测试

测试不存在端口、端口占用、拔出设备。

### Step 8：集成 GUI

接入 serial panel 和 health panel。

---

## 19. 验收标准

1. 可列出串口；
2. 可打开用户选择串口；
3. 可关闭串口；
4. 可重连；
5. 读取不阻塞 GUI；
6. 串口异常有中文提示；
7. bytes/s 正常显示；
8. 控制命令通过 `protocol.commands` 编码；
9. 发送失败能提示；
10. 无硬件时 GUI 仍可启动；
11. 没有多个 reader 线程残留。

阶段完成后建议：

```bash
pytest tests/test_serial_state.py
git status
git diff
git add pydisplay/io tests/test_serial_state.py
git commit -m "feat: implement serial BLE IO layer"
```