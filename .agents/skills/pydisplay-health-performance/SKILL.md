# Skill: pydisplay-health-performance

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 实现链路健康监控；
- 统计 bytes/s；
- 统计有效帧率；
- 统计坏帧率；
- 统计 resync 次数；
- 统计串口缓冲区字节数；
- 统计 parser buffer 字节数；
- 统计绘图 FPS；
- 统计记录队列长度；
- 优化 GUI 卡顿；
- 优化 PyQtGraph 性能；
- 排查长时间运行稳定性问题。

---

## 2. 核心目标

上位机需要长期运行，因此必须可观测、可诊断、不卡顿。

健康监控区至少显示：

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

状态栏刷新频率：

```text
1–5 Hz
```

禁止每帧更新 QLabel。

---

## 3. 推荐文件位置

```text
pydisplay/
  services/
    __init__.py
    health_monitor.py
    pipeline.py
    data_bus.py

  gui/
    widgets/
      health_panel.py
```

---

## 4. HealthMonitor 设计

### 4.1 输入数据来源

HealthMonitor 从以下模块收集指标：

```text
SerialReader
Parser
Decoder
RecorderWorker
ReplayWorker
PlotManager
GUI state
```

### 4.2 推荐数据结构

```python
@dataclass
class HealthSnapshot:
    timestamp_ns: int

    serial_state: str
    recording_state: str
    replay_state: str

    bytes_per_second: float
    total_bytes: int
    serial_buffer_bytes: int

    valid_frame_rate: float
    bad_frame_rate: float
    valid_frames: int
    bad_frames: int
    bad_frame_ratio: float
    resync_count: int
    parser_buffer_bytes: int

    decoded_sample_rate: float
    decode_error_count: int

    plot_fps: float
    plot_queue_size: int

    record_queue_size: int
    record_dropped_count: int
    record_error_count: int

    last_error: str | None
```

字段可以按实际项目调整，但 GUI 要能显示用户要求的核心指标。

---

## 5. 速率统计方法

### 5.1 bytes/s

每次收到 raw chunk 时累加：

```text
total_bytes += len(chunk)
```

每 1 秒或 health refresh interval 计算：

```text
bytes_per_second = delta_bytes / delta_time
```

### 5.2 有效帧率

Parser 每输出有效帧时累加：

```text
valid_frames += 1
```

计算：

```text
valid_frame_rate = delta_valid_frames / delta_time
```

### 5.3 坏帧率

Parser 发现坏帧时累加：

```text
bad_frames += 1
```

计算：

```text
bad_frame_rate = delta_bad_frames / delta_time
```

### 5.4 坏帧比例

```text
bad_frame_ratio = bad_frames / max(valid_frames + bad_frames, 1)
```

### 5.5 绘图 FPS

PlotManager 每次实际刷新曲线后累加：

```text
plot_frame_count += 1
```

计算：

```text
plot_fps = delta_plot_frame_count / delta_time
```

---

## 6. 状态刷新要求

HealthPanel 使用 QTimer 刷新：

```text
默认 2 Hz
允许 1–5 Hz
```

禁止：

1. 每收到一个 sample 就更新 QLabel；
2. 每收到一个 raw chunk 就更新 QLabel；
3. 在 health panel 中做重型统计；
4. 高频弹窗。

---

## 7. 卡顿预防要求

### 7.1 GUI 主线程禁止

GUI 主线程禁止：

```text
串口阻塞读取
协议连续字节解析重负载
文件写入
每帧 flush
pandas append
无限 list append
高频 QLabel setText
高频创建曲线对象
```

### 7.2 绘图限制

绘图刷新：

```text
10–30 FPS
默认 20 FPS
```

状态刷新：

```text
1–5 Hz
```

记录：

```text
100 Hz 全量
```

三者必须解耦。

---

## 8. 队列监控

需要监控：

```text
raw_queue_size
decoded_queue_size
record_queue_size
plot_queue_size
```

如果队列过长：

1. health panel 显示警告；
2. 写日志；
3. 不静默丢弃记录数据；
4. 可以丢弃过期 GUI 绘图数据；
5. 必要时提示用户降低绘图曲线数量或刷新率。

---

## 9. 绘图性能建议

1. 使用 ring buffer；
2. 只保留最近 N 秒；
3. 每个曲线只创建一次；
4. 刷新时调用 `setData()`；
5. 隐藏曲线时跳过 setData；
6. 暂停绘图时不更新曲线；
7. 不要在绘图函数中格式化大量字符串；
8. 不要在绘图函数中写日志；
9. 不要在绘图函数中做协议解码。

---

## 10. 记录性能建议

1. 使用独立 RecorderWorker；
2. 批量写入 raw bin；
3. 批量写入 csv；
4. 定期 flush；
5. 停止时 final flush；
6. 不要每帧 open / close；
7. 不要每帧 pandas append；
8. health monitor 显示记录队列长度。

---

## 11. 串口性能建议

1. 串口读取 timeout 不宜过长；
2. 避免 busy loop；
3. 使用 `in_waiting` 读取已有数据；
4. 每次 read 限制最大 chunk；
5. 异常时不要疯狂重试；
6. 重连要有状态和间隔；
7. 长时间无数据应显示提示。

---

## 12. 长时间运行稳定性

需要关注：

1. 内存是否持续增长；
2. queue 是否持续增长；
3. raw bin 文件是否正常增长；
4. csv 是否正常写入；
5. GUI 是否逐渐变慢；
6. bad frame ratio 是否异常升高；
7. reconnect 后旧线程是否退出；
8. replay 后资源是否释放。

建议添加 debug 日志：

```text
每隔 60 秒记录一次 HealthSnapshot 摘要
```

---

## 13. 错误等级建议

### 13.1 信息

```text
串口已连接
开始记录
停止记录
开始回放
```

### 13.2 警告

```text
坏帧率偏高
记录队列积压
长时间无数据
绘图 FPS 低于目标
```

### 13.3 错误

```text
串口断开
写文件失败
parser buffer 异常增长
回放文件格式错误
```

---

## 14. HealthPanel 显示建议

以表格形式显示：

| 指标        | 当前值      |
| --------- | -------- |
| 串口状态      | 已连接      |
| 记录状态      | 记录中      |
| bytes/s   | 12345    |
| 有效帧率      | 100.0 Hz |
| 坏帧率       | 0.0 Hz   |
| 坏帧比例      | 0.01%    |
| resync 次数 | 2        |
| 串口缓冲区     | 0 bytes  |
| 解析缓冲区     | 12 bytes |
| 绘图 FPS    | 20.0     |
| 记录队列      | 4        |

---

## 15. Pipeline 设计要求

`pipeline.py` 负责把数据流串起来：

```text
SerialReader
  ↓
Parser
  ↓
Decoder
  ↓
RecorderWorker
  ↓
GUI RingBuffer
  ↓
HealthMonitor
```

Pipeline 需要：

1. 明确启动顺序；
2. 明确停止顺序；
3. 防止线程泄漏；
4. 支持实时串口模式；
5. 支持回放模式；
6. 实时模式和回放模式初版建议互斥。

---

## 16. 性能测试建议

### 16.1 模拟 100 Hz decoded sample

生成 100 Hz 数据输入 GUI，测试：

1. plot FPS；
2. GUI 响应；
3. 内存增长；
4. health panel 更新。

### 16.2 模拟坏帧

输入包含坏帧的数据，测试：

1. bad frame count；
2. bad frame ratio；
3. resync count；
4. GUI 是否卡顿。

### 16.3 模拟记录压力

连续写入 10 分钟，观察：

1. record_queue_size；
2. 文件大小；
3. GUI 响应；
4. 是否丢数据。

---

## 17. 禁止事项

禁止：

1. 每帧 QLabel 更新；
2. 每帧 pandas append；
3. 每帧 flush；
4. GUI 主线程阻塞；
5. 队列无限增长无提示；
6. 绘图数据无限增长；
7. 线程异常静默退出；
8. 旧 reader 线程未停止就重连；
9. 回放和实时串口同时抢占同一 pipeline。

---

## 18. 推荐开发步骤

### Step 1：定义 HealthSnapshot

实现数据结构。

### Step 2：实现 HealthMonitor

支持计数器和速率统计。

### Step 3：接入 parser stats

显示有效帧、坏帧、resync。

### Step 4：接入 serial stats

显示 bytes/s 和串口状态。

### Step 5：接入 recorder stats

显示记录队列长度和记录状态。

### Step 6：接入 plot stats

显示绘图 FPS。

### Step 7：实现 HealthPanel 定时刷新

QTimer 1–5 Hz。

### Step 8：做 100 Hz 模拟压力测试

观察 GUI 是否卡顿。

---

## 19. 验收标准

1. health panel 显示全部要求指标；
2. 状态刷新 1–5 Hz；
3. 100 Hz 数据输入时 GUI 不明显卡顿；
4. 绘图 FPS 接近设置值；
5. 记录队列长度可见；
6. 串口异常可见；
7. 坏帧率和 resync 可见；
8. parser buffer 字节数可见；
9. 没有每帧 QLabel 更新；
10. 长时间运行无明显内存无限增长。

完成后建议：

```bash
git status
git diff
git add pydisplay/services pydisplay/gui/widgets/health_panel.py
git commit -m "feat: add health monitor and performance safeguards"
```