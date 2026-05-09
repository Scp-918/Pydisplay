# Protocol Questions

## 协议分析暂停报告

### 已确认内容

- 固件仓库 `https://github.com/Scp-918/PulseTIMR2/tree/Single` 已检查，当前分析提交为 `3714333572dc985c407dbb680183785cc0b92b66`。
- 数据帧为固定 49 字节，帧头 `0xAA 0xBB`，帧尾 `0xCC`。
- 数据帧 payload 为 byte 2 到 byte 46。
- checksum 为 byte 2 到 byte 46 的逐字节 XOR，帧头和帧尾不参与。
- 数据帧字段顺序为 4 路 ADC early/late、PPG Green/Red/IR、IMU Gx/Gy/Gz/Ax/Ay/Az。
- 发送链路为 USART1 / BLE 透明串口，目标波特率 460800。
- 上位机参数控制帧为 13 字节：`AB CD ... EF FA`，字段包含 PPG mode、Multi sub-mode、三路 LED 亮度、PPG ADC range、PPG pulse width、gyro range、accel range。
- 控制参数范围已从固件确认。

### 无法确认内容

- ADC `early_code` / `late_code` 是否分别对应 `Uh` / `Uc`。
- 4 路 ADC phase/channel 与 `Uh1..Uh4`、`Uc1..Uc4` 的映射。
- `UD1` 和 `UD2` 分别使用哪些 `Uh` / `Uc` 通道。
- AD4007 raw code 到电压的完整换算公式，尤其是外部模拟前端增益、偏置、极性和校准参数。
- PPG 是否需要除固件 already-aligned raw count 以外的物理量缩放。
- 协议版本字段未找到。
- 控制参数帧 ACK/NACK 未找到，当前源码只发现内部错误标志 `g_sensor_cfg_apply_error`。

### 已检查文件

- `README.md`
- `Core/Inc/ble_comm.h`
- `Core/Src/ble_comm.c`
- `Core/Src/main.c`
- `Core/Inc/sensor_ringbuffer.h`
- `Core/Inc/AD4007.h`
- `Core/Src/AD4007.c`
- `Core/Inc/MAX30101.h`
- `Core/Src/MAX30101.c`
- `Core/Inc/LSM9DS1.h`
- `Core/Src/LSM9DS1.c`
- `Core/Inc/ble.h`
- `Core/Src/ble.c`
- `Core/Src/usart.c`
- `Sensorlist/AD4007.md`
- `Sensorlist/MAX30101.md`
- `Sensorlist/LSM9DS1.md`
- `Sensorlist/TMUX1108.md`
- `Sensorlist/HJ131IMH.md`

### 阻塞问题

1. 不能确认 `Uh` / `Uc` 与 ADC early/late 的关系。
2. 不能确认 `UD1` / `UD2` 的输入通道来源。
3. 不能确认 PC 端电压缩放和校准公式。
4. 因上述内容缺失，无法可靠实现项目要求中的 decoder 输出字段和 UD 解算。

### 建议用户确认

1. 请确认 `adc_data[ch].early_code` 和 `adc_data[ch].late_code` 是否就是 `Uh` 和 `Uc`，以及 early/late 分别对应哪一个。
2. 请确认 4 个 ADC 通道与实验通道 `1..4` 的物理对应关系。
3. 请确认 `UD1` / `UD2` 分别使用哪一路 `Uh` / `Uc`。
4. 请提供 AD4007 原始码到电压的换算公式，包括 VREF、满量程定义、外部增益、偏置、极性和校准方式。
5. 请确认 PPG 是否只记录固件输出的 raw count，还是需要进一步转换为物理单位。
6. 请确认控制帧是否设计为无 ACK/NACK；如果有 ACK，请提供格式。

在这些问题确认前，我不会继续实现真实 parser / decoder / command encoder。
