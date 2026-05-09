# Skill: pydisplay-firmware-protocol-analysis

## 1. 适用场景

当任务涉及以下内容时，必须优先使用本 skill：

- 分析 STM32G474 固件通信协议；
- 从固件源码中确认上位机接收帧格式；
- 从固件源码中确认上位机控制命令格式；
- 从 sensorlist 或传感器配置中确认 PPG / IMU / 电压缩放系数；
- 编写或更新 `docs/protocol_analysis.md`；
- 判断当前协议信息是否足够支持 Python 上位机开发。

本 skill 的核心原则是：

> 先确认协议，再写解析器。禁止臆造协议。

---

## 2. 项目上下文

Python 上位机项目目录：

```text
D:\Desktop\STM32G474\Pydisplay
```

STM32 固件仓库：

```text
https://github.com/Scp-918/PulseTIMR2/tree/Single
```

STM32 型号：

```text
STM32G474
```

下位机发送模块：

```text
HJ131 蓝牙模块
```

上位机接收模块：

```text
HJ380 蓝牙串口模块
```

已知且可直接使用的协议事实：

```text
帧头：0xAA 0xBB
帧尾：0xCC
```

除上述帧头和帧尾外，任何协议细节都必须从固件源码、sensorlist 或项目文档中确认。

---

## 3. 主要目标

完成协议分析，输出：

```text
docs/protocol_analysis.md
docs/protocol_questions.md
```

其中 `docs/protocol_analysis.md` 必须说明：

1. 帧头；
2. 帧尾；
3. 固定帧长或变长规则；
4. payload 长度；
5. 字段顺序；
6. 每个字段的数据类型；
7. 每个字段字节数；
8. 有符号 / 无符号；
9. 字节序；
10. 校验方式；
11. PPG_G / PPG_R / PPG_IR 原始值与缩放方式；
12. 加速度计三轴原始值与缩放方式；
13. 陀螺仪三轴原始值与缩放方式；
14. 4 路 Uh 原始值与缩放方式；
15. 4 路 Uc 原始值与缩放方式；
16. UD 两路信号来源；
17. 帧序号或采样序号是否存在；
18. 下位机是否发送时间戳；
19. 上位机控制命令格式；
20. PPG mode 参数含义；
21. LED 亮度参数范围；
22. PPG 量程参数范围；
23. 脉宽参数范围；
24. IMU 量程参数范围；
25. 协议版本；
26. 未确认问题清单；
27. 信息来源文件和行号。

---

## 4. 必须优先检查的文件和目录

如果固件仓库已存在于本地，优先检查本地文件。

如果本地不存在固件源码，再根据可用方式获取仓库内容。

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

需要重点关注：

```text
UART
USART
BLE
HJ131
HJ380
DMA
HAL_UART_Transmit
HAL_UART_Receive
HAL_UART_Transmit_DMA
HAL_UARTEx_ReceiveToIdle_DMA
printf
frame
packet
protocol
checksum
crc
crc8
crc16
sum
cmd
command
control
metadata
PPG
IMU
ACC
GYRO
Uh
Uc
UD
sensorlist
```

---

## 5. 推荐搜索命令

在 Windows PowerShell 或 Git Bash 中，可使用类似命令：

```bash
rg -n "0xAA|0xBB|0xCC|AA|BB|CC" .
rg -n "UART|USART|HAL_UART|DMA|Transmit|Receive" .
rg -n "BLE|HJ131|HJ380|bluetooth|bt" .
rg -n "frame|packet|protocol|header|tail|checksum|crc|sum" .
rg -n "PPG|LED|IR|GREEN|RED|IMU|ACC|GYRO" .
rg -n "Uh|Uc|UD|ADC|voltage|sensor" .
rg -n "cmd|command|control|mode|range|pulse|brightness" .
```

如果 `rg` 不可用，可使用：

```bash
findstr /S /N /I "0xAA 0xBB 0xCC UART USART HAL_UART" *.*
```

---

## 6. 协议分析步骤

### Step 1：定位发送入口

查找下位机发送数据的位置：

* 是否使用 UART；
* 是否使用 DMA；
* 是否通过 printf 重定向；
* 是否通过 BLE 模块透明串口发送；
* 是否定时 100 Hz 发送；
* 是否存在发送结构体或 buffer 拼包逻辑。

需要记录：

```text
发送函数名
发送所在文件
发送调用周期
发送 buffer 构造方式
发送字节数
```

---

### Step 2：定位帧结构

确认帧格式，例如：

```text
header
length
payload
checksum
tail
```

必须确认：

```text
header = 0xAA 0xBB
tail = 0xCC
```

并继续确认：

```text
frame_length
payload_length
checksum_position
tail_position
```

不要根据经验假设帧长。

---

### Step 3：确认字段布局

必须列出 payload 字段表。

字段表建议格式：

| Offset | 字段名 | 字节数 | 类型 | 字节序 | 缩放系数 | 单位 | 来源 |
| ------ | --: | --: | -- | --- | ---: | -- | -- |

字段至少覆盖：

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
Uh1
Uh2
Uh3
Uh4
Uc1
Uc2
Uc3
Uc4
```

如果存在：

```text
frame_seq
sample_seq
timestamp
status
battery
temperature
```

也必须记录。

---

### Step 4：确认校验方式

必须从固件中确认校验算法：

* 无校验；
* 累加和；
* XOR；
* CRC8；
* CRC16；
* 自定义 checksum。

如果是 CRC，必须确认：

```text
多项式
初值
输入范围
大小端
是否反转
输出异或值
```

如果找不到校验方式，必须在 `docs/protocol_questions.md` 中列为阻塞问题。

---

### Step 5：确认缩放系数

必须确认：

```text
PPG 原始值是否需要缩放
IMU 加速度计量程和 LSB/g
IMU 陀螺仪量程和 LSB/dps
ADC / 电压换算系数
Uh / Uc 单位
UD 两路来源
```

需要优先从 sensorlist、传感器驱动、寄存器配置、注释、手册引用中确认。

---

### Step 6：确认控制命令

查找下位机是否接收上位机命令。

必须确认：

```text
命令帧头
命令帧尾
命令长度
命令 ID
参数字段
checksum
ACK / NACK
超时处理
```

至少确认以下控制参数：

```text
PPG mode
LED brightness
PPG range
pulse width
IMU range
```

如果固件没有实现某个命令，需要在报告中明确说明：

```text
固件中未发现对应命令实现。
```

禁止在 Python 端自行发明命令格式。

---

## 7. `docs/protocol_analysis.md` 推荐模板

````markdown
# Pydisplay Protocol Analysis

## 1. 固件来源

- Repo:
- Branch:
- Commit:
- Local path:
- Analysis date:

## 2. 已确认结论摘要

| 项目 | 结论 | 来源 |
|---|---|---|
| Frame header | 0xAA 0xBB | 用户确认 / 源码位置 |
| Frame tail | 0xCC | 用户确认 / 源码位置 |
| Frame length | 待确认 | - |
| Byte order | 待确认 | - |
| Checksum | 待确认 | - |

## 3. 数据发送链路

说明 UART / BLE / DMA / 发送周期。

## 4. 数据帧格式

```text
待填写真实格式
````

## 5. Payload 字段布局

| Offset | 字段名 | 字节数 | 类型 | 字节序 | 缩放 | 单位 | 来源 |
| ------ | --: | --: | -- | --- | -: | -- | -- |

## 6. 校验方式

说明 checksum / CRC 规则。

## 7. PPG 解码

说明 PPG_G / PPG_R / PPG_IR 的来源、单位和缩放。

## 8. IMU 解码

说明 ACC / GYRO 的来源、量程、单位和缩放。

## 9. 电压类数据解码

说明 Uh / Uc 的来源、单位和缩放。

## 10. UD 解算

```text
UD = (Uh - Uc) / (k - Uc)
```

说明 UD1 / UD2 分别使用哪些 Uh / Uc 通道。

## 11. 上位机控制命令

说明命令格式、命令 ID、参数范围、ACK。

## 12. 未确认问题

| 编号 | 问题 | 是否阻塞开发 | 建议确认方式 |
| -- | -- | ------ | ------ |

## 13. 可进入 Python 实现的条件

列出 parser / decoder / command 实现是否具备足够信息。

````

---

## 8. 不确定时必须暂停

以下情况必须暂停并报告，不得继续写 parser 或 commands：

1. 找不到帧长度；
2. 找不到 payload 字段布局；
3. 找不到 checksum 规则；
4. 找不到字节序；
5. 找不到 Uh / Uc 缩放；
6. 找不到 IMU 量程；
7. 找不到控制命令格式；
8. 找不到 PPG mode / LED / range / pulse / IMU range 对应关系；
9. 固件中存在多个疑似协议版本，无法判断当前使用哪个；
10. sensorlist 与源码冲突。

暂停报告格式：

```markdown
## 协议分析暂停报告

### 已确认内容

- ...

### 无法确认内容

- ...

### 已检查文件

- ...

### 阻塞问题

1. ...
2. ...

### 建议用户确认

1. ...
2. ...

在这些问题确认前，不继续实现 parser / decoder / command encoder。
````

---

## 9. 允许的临时实现

允许为了 GUI 开发做模拟数据，但必须满足：

1. 文件名明确带有 `simulated` 或 `mock`；
2. 注释中写明 `simulation only, not firmware protocol`；
3. 不得把模拟协议写入 `protocol/constants.py` 当作真实协议；
4. 不得让测试误以为模拟协议就是固件协议。

---

## 10. 禁止事项

禁止：

1. 编造帧长；
2. 编造 payload 字段顺序；
3. 编造 checksum；
4. 编造控制命令；
5. 编造缩放系数；
6. 编造协议版本；
7. 只根据用户需求文档直接写 parser；
8. 把模拟数据格式当作真实通信协议；
9. 在协议不完整时继续实现核心 parser；
10. 删除或覆盖用户已有代码而不说明。

---

## 11. 完成标准

本 skill 完成时，应满足：

1. `docs/protocol_analysis.md` 已创建或更新；
2. `docs/protocol_questions.md` 已创建或更新；
3. 所有已确认字段均带来源；
4. 未确认字段明确列出；
5. 明确判断是否可以进入 parser / decoder / command 实现；
6. 没有编造协议内容。

阶段完成后，建议执行：

```bash
git status
git diff
```

若当前目录是 git 仓库且阶段结果可靠，再提交：

```bash
git add docs/protocol_analysis.md docs/protocol_questions.md
git commit -m "docs: analyze firmware communication protocol"
```