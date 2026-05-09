# Skill: pydisplay-testing-packaging

## 1. 适用场景

当任务涉及以下内容时，使用本 skill：

- 添加 pytest 测试；
- 设计无硬件测试；
- 设计回放测试；
- 编写模拟数据；
- 配置项目入口；
- 配置 `pyproject.toml`；
- 整理 README；
- 做阶段性验收；
- 打包或提供运行脚本；
- 检查代码结构是否适合 Codex 后续维护。

---

## 2. 项目环境

用户已说明：

```text
Conda 虚拟环境：Pydisplay_env
依赖包：已经安装
```

因此不要把“检查依赖是否安装”作为阻塞项。

可以在 README 中写运行方式：

```bash
conda activate Pydisplay_env
cd D:\Desktop\STM32G474\Pydisplay
python -m pydisplay
```

---

## 3. 推荐测试目录

```text
tests/
  test_protocol_parser.py
  test_decoder.py
  test_commands.py
  test_raw_bin_format.py
  test_replay.py
  test_metadata.py
  test_ring_buffer.py
  test_health_monitor.py
```

不必一次性完成所有测试，但 parser / decoder / raw bin / replay 是核心测试。

---

## 4. 测试分层

### 4.1 单元测试

覆盖：

```text
protocol parser
decoder
command encoder
raw bin writer/reader
csv writer
metadata writer
ring buffer
health monitor
```

### 4.2 集成测试

覆盖：

```text
raw bytes -> parser -> decoder
decoded sample -> recorder -> csv
raw chunk -> recorder -> raw bin -> replay -> parser
decoded csv -> replay -> GUI-like consumer
```

### 4.3 GUI 手工测试

GUI 自动化不是第一优先级。

必须提供手工测试清单：

```text
docs/manual_test_checklist.md
```

---

## 5. 无硬件测试策略

无硬件时，优先使用以下方式测试：

1. `decoded.csv` 回放；
2. `raw_frames.bin` 回放；
3. 内存模拟 decoded sample；
4. 如果真实协议已确认，可生成真实协议模拟帧；
5. 虚拟串口 + 模拟下位机作为可选项。

注意：

```text
虚拟串口方案失败时，不阻塞主项目。
```

---

## 6. 模拟数据原则

如果创建模拟数据：

1. 文件名必须包含 `simulated` 或 `mock`；
2. 注释中写明 `simulation only`；
3. 不得冒充真实固件协议；
4. 如果协议未确认，不得生成所谓真实 raw frame；
5. 如果协议已确认，可生成符合协议的测试帧。

---

## 7. pytest 要求

### 7.1 运行命令

```bash
pytest
```

或分模块：

```bash
pytest tests/test_protocol_parser.py
pytest tests/test_raw_bin_format.py
pytest tests/test_replay.py
```

### 7.2 测试要求

测试应：

1. 不依赖真实串口；
2. 不依赖真实硬件；
3. 不写入工程根目录污染文件；
4. 使用临时目录；
5. 可重复运行；
6. 不依赖测试执行顺序。

pytest 中使用：

```python
tmp_path
monkeypatch
```

---

## 8. Parser 测试最低要求

必须覆盖：

1. 完整单帧；
2. 多帧粘包；
3. 半包；
4. 噪声；
5. 坏 checksum；
6. 错误帧尾；
7. 坏帧后 resync；
8. parser buffer 不无限增长。

---

## 9. Recorder / Replay 测试最低要求

必须覆盖：

1. raw bin 写入；
2. raw bin 读取；
3. magic 错误；
4. version 不兼容；
5. decoded csv 写入；
6. decoded csv 字段检查；
7. replay pause / resume 基础逻辑；
8. metadata 开始和结束时间。

---

## 10. GUI 手工验收清单

创建：

```text
docs/manual_test_checklist.md
```

建议内容：

```markdown
# Pydisplay Manual Test Checklist

## 1. 启动

- [ ] conda activate Pydisplay_env
- [ ] python -m pydisplay
- [ ] GUI 正常启动
- [ ] 中文显示正常

## 2. 串口

- [ ] 刷新串口
- [ ] 选择串口
- [ ] 选择波特率
- [ ] 打开串口
- [ ] 关闭串口
- [ ] 重连串口
- [ ] 拔出 HJ380 后 GUI 不崩溃

## 3. 协议

- [ ] 有效帧率显示
- [ ] 坏帧率显示
- [ ] resync 次数显示
- [ ] parser buffer 显示

## 4. 绘图

- [ ] PPG 曲线显示
- [ ] ACC 曲线显示
- [ ] GYRO 曲线显示
- [ ] Uh 曲线显示
- [ ] Uc 曲线显示
- [ ] UD 曲线显示
- [ ] 暂停绘图后记录继续
- [ ] 隐藏曲线正常

## 5. 记录

- [ ] 开始记录
- [ ] 停止记录
- [ ] raw_frames.bin 生成
- [ ] decoded.csv 生成
- [ ] metadata.json 生成
- [ ] metadata 字段完整

## 6. 回放

- [ ] raw bin 回放
- [ ] decoded csv 回放
- [ ] 暂停回放
- [ ] 继续回放
- [ ] 倍速回放
```

---

## 11. 项目入口

必须支持：

```bash
python -m pydisplay
```

推荐：

```text
pydisplay/__main__.py
pydisplay/app.py
scripts/run_app.py
```

`__main__.py` 应调用 app 入口，而不是包含大量 GUI 逻辑。

---

## 12. `pyproject.toml` 建议

可创建简单配置：

```toml
[project]
name = "pydisplay"
version = "0.1.0"
description = "Python GUI upper computer for STM32G474 BLE serial data display"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

依赖包可记录但不要强迫用户重装。

---

## 13. README 要求

`README.md` 至少说明：

1. 项目用途；
2. 运行环境；
3. 启动方式；
4. 串口连接方式；
5. 数据记录文件；
6. 回放方式；
7. 协议分析文件位置；
8. 常见问题；
9. 当前未确认事项。

推荐结构：

```markdown
# Pydisplay

## 1. 项目简介

## 2. 运行环境

## 3. 启动

## 4. 串口连接

## 5. 数据记录

## 6. 回放模式

## 7. 协议文档

## 8. 开发与测试

## 9. 常见问题
```

---

## 14. 日志要求

推荐：

```text
logs/pydisplay.log
```

日志应记录：

1. 启动；
2. 串口连接 / 断开；
3. 解析异常；
4. 记录开始 / 停止；
5. 回放开始 / 停止；
6. 控制命令发送；
7. 未捕获异常。

测试中不要污染真实 logs 目录，使用临时目录或关闭文件日志。

---

## 15. 阶段性提交要求

每个阶段完成后：

```bash
git status
git diff
pytest
```

如果测试通过且当前是 git 仓库：

```bash
git add .
git commit -m "..."
```

如果测试暂时无法全部通过，提交前必须说明：

```text
哪些测试通过
哪些测试失败
失败原因
是否阻塞下一阶段
```

不要为了通过测试而删除关键测试。

---

## 16. 不允许的测试行为

禁止：

1. 测试依赖真实串口；
2. 测试依赖真实蓝牙模块；
3. 测试写死用户电脑 COM 口；
4. 测试写死绝对路径；
5. 测试污染工程根目录；
6. 为了测试通过修改真实协议常量；
7. 将模拟协议当真实协议；
8. 删除失败测试而不说明；
9. GUI 测试阻塞 pytest。

---

## 17. 打包与分发

当前优先目标是源码运行：

```bash
python -m pydisplay
```

打包为 exe 不是第一阶段目标。

如果后续需要 Windows exe，可再考虑：

```text
PyInstaller
Nuitka
```

但不要在核心功能未稳定前引入复杂打包。

---

## 18. 推荐开发步骤

### Step 1：建立 pytest 基础配置

创建 `pyproject.toml` 或 pytest 配置。

### Step 2：添加 parser / decoder 测试

确保协议核心可靠。

### Step 3：添加 recorder / replay 测试

确保数据可复盘。

### Step 4：添加 ring buffer / health monitor 测试

确保 GUI 性能基础稳定。

### Step 5：整理 README

说明如何运行。

### Step 6：创建 manual test checklist

支持人工验收。

### Step 7：运行全量测试

```bash
pytest
```

### Step 8：阶段性 git 保存

---

## 19. 验收标准

1. `python -m pydisplay` 可启动；
2. `pytest` 至少覆盖核心非 GUI 模块；
3. 测试不依赖硬件；
4. README 可指导运行；
5. manual test checklist 完整；
6. raw bin / csv / metadata 有测试；
7. parser 异常恢复有测试；
8. 回放有测试；
9. 当前不支持或未确认内容被清楚记录；
10. 没有为了测试通过而编造协议。

完成后建议：

```bash
pytest
git status
git diff
git add pyproject.toml README.md docs/manual_test_checklist.md tests
git commit -m "test: add validation and packaging scaffolding"
```