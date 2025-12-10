# yamon

Mac 系统监控 TUI 工具 - 实时显示 CPU、内存、网络、GPU、ANE 和功耗等系统指标

## 安装

```bash
# 使用 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

## 运行

```bash
python -m yamon
```

## 功能

### 基础监控（无需特殊权限）
- CPU 占用率（每核心）
- 内存使用情况
- 网络流量（上行/下行）
- 实时更新（1秒刷新）

### Apple Silicon 监控（需要 sudo）
- GPU 占用率
- GPU 频率
- ANE (Apple Neural Engine) 占用率
- CPU 功耗
- GPU 功耗
- ANE 功耗
- DRAM 功耗
- 系统总功耗

**注意**：GPU、ANE 和功耗监控需要使用 `powermetrics` 命令，该命令需要 sudo 权限。如果未提供 sudo 权限，这些指标将显示为 "N/A"。

## 快捷键

- `q` - 退出程序
- `r` - 手动刷新

## 技术实现

- **基础监控**：使用 `psutil` 库获取 CPU、内存、网络指标
- **Apple Silicon 监控**：使用 `powermetrics` 命令获取 GPU、ANE 和功耗数据
  - 未来计划：实现无需 sudo 的原生 IOReport API 绑定

