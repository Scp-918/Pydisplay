# Skill: pydisplay-protocol-parser-state-machine

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 实现二进制协议解析器；
- 实现帧头同步和 resync；
- 实现坏帧统计；
- 实现 PPG / IMU / Uh / Uc / UD 解码；
- 编写 parser / decoder 单元测试；
- 修改 `pydisplay/protocol/` 下的代码。

使用本 skill 之前，必须已经完成协议分析，并存在：

```text
docs/protocol_analysis.md
```

如果协议分析文档不存在，或者其中关键字段仍为待确认，不得继续实现真实 parser。

---

## 2. 依赖前置条件

必须已经确认：

```text
帧头：0xAA 0xBB
帧尾：0xCC
帧长或变长规则
payload 字段顺序
字段类型
字段字节数
字节序
校验方式
PPG 缩放系数
IMU 缩放系数
电压缩放系数
控制命令是否独立于数据帧
```

如果任一核心信息缺失，必须暂停并报告。

---

## 3. 推荐文件位置

```text
pydisplay/
  protocol/
    __init__.py
    constants.py
    models.py
    parser.py
    decoder.py
    commands.py
    errors.py

tests/
  test_protocol_parser.py
  test_decoder.py
  test_commands.py
```

---

## 4. 模块职责

### 4.1 `constants.py`

只放真实协议常量。

允许直接写入：

```python
FRAME_HEADER = b"\xAA\xBB"
FRAME_TAIL = b"\xCC"
```

其他常量必须来自 `docs/protocol_analysis.md`。

例如：

```python
FRAME_LENGTH = ...
PAYLOAD_LENGTH = ...
BYTE_ORDER = "little"
PROTOCOL_VERSION = ...
```

禁止将模拟协议常量写入这里。

---

### 4.2 `models.py`

推荐使用 `dataclasses` 定义数据模型。

建议包含：

```python
RawFrame
ParsedFrame
DecodedSample
ParserStats
DecodeConfig
ControlMetadata
CommandFrame
```

字段建议：

```python
RawFrame:
    timestamp_ns: int
    data: bytes
    source: str

ParsedFrame:
    timestamp_ns: int
    raw: bytes
    payload: bytes
    frame_seq: int | None
    checksum_ok: bool

DecodedSample:
    timestamp_pc_ns: int
    relative_time_s: float
    frame_seq: int | None
    sample_seq: int | None
    ppg_g: float
    ppg_r: float
    ppg_ir: float
    acc_x: float
    acc_y: float
    acc_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    uh1: float
    uh2: float
    uh3: float
    uh4: float
    uc1: float
    uc2: float
    uc3: float
    uc4: float
    ud1: float
    ud2: float
```

字段名称可以根据协议分析报告调整，但必须保持 CSV 输出和 GUI 绘图一致。

---

### 4.3 `parser.py`

实现纯 Python parser，不依赖 GUI。

Parser 输入：

```python
feed(data: bytes, timestamp_ns: int | None = None) -> list[ParsedFrame]
```

Parser 输出：

```python
list[ParsedFrame]
```

Parser 必须保存内部 buffer，支持连续 byte stream。

---

### 4.4 `decoder.py`

将 `ParsedFrame` 转换为 `DecodedSample`。

核心函数建议：

```python
decode_frame(frame: ParsedFrame, config: DecodeConfig) -> DecodedSample
```

UD 公式：

```text
UD = (Uh - Uc) / (k - Uc)
```

k 来自 GUI 输入或配置。

需要处理：

```text
k - Uc 接近 0
字段缺失
数值越界
缩放异常
```

---

### 4.5 `commands.py`

实现控制命令编码，但必须基于固件真实协议。

如果控制命令格式未确认，此文件只能包含占位异常：

```python
raise ProtocolNotConfirmedError("Control command format is not confirmed.")
```

禁止编造命令帧。

---

## 5. 状态机设计要求

Parser 必须覆盖以下状态：

```text
FIND_HEADER
READ_BODY
VERIFY
EMIT_FRAME
RESYNC
```

也可以细分为：

```text
FIND_HEADER
READ_LENGTH
READ_PAYLOAD
READ_CHECKSUM
READ_TAIL
VERIFY
RESYNC
```

具体状态取决于真实协议。

---

## 6. 状态机行为要求

### 6.1 输入特性

输入是连续串口 byte stream，不允许假设一次串口 read 正好是一帧。

必须支持：

1. 半包；
2. 粘包；
3. 帧头前噪声；
4. 帧中损坏；
5. 错误帧尾；
6. 错误 checksum；
7. 多个连续坏帧；
8. 重新同步。

---

### 6.2 找帧头

已知帧头：

```text
0xAA 0xBB
```

查找逻辑：

1. 在 buffer 中搜索 `b"\xAA\xBB"`；
2. 丢弃帧头前噪声，但需要统计噪声字节数；
3. 保留可能的半个帧头，例如 buffer 末尾为 `0xAA` 时不能直接丢弃。

---

### 6.3 收帧体

根据协议分析结果处理：

* 固定长度协议：等待完整 `FRAME_LENGTH`；
* 变长协议：先读取 length 字段，再等待完整帧。

不得硬编码未确认长度。

---

### 6.4 校验

根据真实协议校验。

如果 checksum 失败：

1. `bad_frame_count += 1`；
2. 记录坏帧原因；
3. 进入 resync；
4. 不清空整个 buffer；
5. 从当前 buffer 中继续寻找下一个帧头。

---

### 6.5 帧尾检查

已知帧尾：

```text
0xCC
```

如果帧尾错误：

1. 统计坏帧；
2. 记录错误原因；
3. 执行 resync。

---

### 6.6 Resync

Resync 要求：

1. 不丢弃整段数据流；
2. 在已有 buffer 中查找下一个 `0xAA 0xBB`；
3. 找到后从该位置继续；
4. 找不到时只保留可能的半个帧头；
5. 统计 `resync_count`。

---

## 7. ParserStats 要求

必须统计：

```python
total_bytes: int
total_frames: int
valid_frames: int
bad_frames: int
bad_frame_ratio: float
resync_count: int
noise_bytes: int
buffer_bytes: int
checksum_errors: int
tail_errors: int
length_errors: int
decode_errors: int
last_error: str | None
```

这些统计需要提供给 health monitor 和 GUI 状态区。

---

## 8. Decoder 要求

Decoder 必须：

1. 使用协议分析中确认的字段 offset；
2. 使用确认的字节序；
3. 使用确认的 signed / unsigned 类型；
4. 使用确认的缩放系数；
5. 保留 PC 时间戳；
6. 保留帧序号或采样序号；
7. 计算相对时间；
8. 计算 UD1 / UD2；
9. 对异常数值做明确处理。

---

## 9. UD 解算要求

公式：

```text
UD = (Uh - Uc) / (k - Uc)
```

要求：

1. k 来自 GUI 输入；
2. k 必须转换为 float；
3. k 非法时禁止开始解算；
4. 当 `abs(k - Uc) < eps` 时：

   * 不得崩溃；
   * UD 设置为 NaN 或 None；
   * 记录 decode warning；
   * health monitor 可统计。
5. UD1 / UD2 使用哪些通道必须来自协议分析报告。

---

## 10. 单元测试要求

至少创建：

```text
tests/test_protocol_parser.py
tests/test_decoder.py
tests/test_commands.py
```

### 10.1 Parser 测试

必须覆盖：

1. 完整单帧；
2. 一次输入多个完整帧；
3. 一帧拆成多次输入；
4. 粘包；
5. 帧头前噪声；
6. buffer 末尾半个帧头；
7. checksum 错误；
8. 帧尾错误；
9. 坏帧后恢复；
10. buffer 不无限增长；
11. bad frame 统计正确；
12. resync 统计正确。

---

### 10.2 Decoder 测试

必须覆盖：

1. 正常字段解码；
2. 字节序正确；
3. signed / unsigned 正确；
4. 缩放系数正确；
5. UD 计算正确；
6. `k - Uc` 接近 0 时不崩溃；
7. 缺失字段或 payload 长度错误时明确报错。

---

### 10.3 Commands 测试

如果控制命令已确认，测试：

1. PPG mode 编码；
2. LED 亮度编码；
3. PPG range 编码；
4. pulse width 编码；
5. IMU range 编码；
6. 非法参数拒绝；
7. checksum 正确；
8. 帧头帧尾正确。

如果控制命令未确认，测试应确认：

```python
ProtocolNotConfirmedError
```

---

## 11. 禁止事项

禁止：

1. 在 parser 中访问 GUI；
2. 在 decoder 中访问串口；
3. 在 parser 中写文件；
4. 在 decoder 中写文件；
5. 假设一次 read 是一帧；
6. checksum 失败后清空全部 buffer；
7. 隐式吞掉解码错误；
8. 用 pandas 参与逐帧解码；
9. 编造控制命令；
10. 编造字段缩放。

---

## 12. 推荐开发步骤

### Step 1：读取协议分析文档

确认 `docs/protocol_analysis.md` 中所有必需项已明确。

### Step 2：定义模型

实现 `models.py`。

### Step 3：定义常量

实现 `constants.py`，只写已确认常量。

### Step 4：实现 checksum

在 `parser.py` 或单独 helper 中实现校验算法。

### Step 5：实现状态机

先支持正常帧，再支持异常恢复。

### Step 6：实现 decoder

根据字段表逐项解码。

### Step 7：实现 tests

优先写 parser tests，再写 decoder tests。

### Step 8：运行测试

```bash
pytest tests/test_protocol_parser.py tests/test_decoder.py
```

### Step 9：阶段性提交

```bash
git status
git diff
git add pydisplay/protocol tests/test_protocol_parser.py tests/test_decoder.py
git commit -m "feat: implement firmware protocol parser and decoder"
```

如果当前不是 git 仓库，不要强行初始化，只报告状态。

---

## 13. 完成标准

本 skill 完成时必须满足：

1. parser 可处理连续 bytes；
2. parser 可处理半包、粘包、噪声、坏帧；
3. parser 有完整统计；
4. decoder 可输出 GUI 和 CSV 所需字段；
5. UD 解算稳定；
6. 单元测试覆盖核心异常；
7. 无协议臆造；
8. 所有协议常量均可追溯到 `docs/protocol_analysis.md`。
