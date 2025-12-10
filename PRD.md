# Mac 系统监控 TUI 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
Mac System Monitor TUI（暂定名称：macmon-tui）

### 1.2 项目目标
开发一个功能强大的 macOS Terminal UI (TUI) 系统监控工具，结合 bashtop 的历史图表功能和 MacMon 的 Apple Silicon 深度监控能力，为 Mac 用户提供实时和历史系统性能监控。

### 1.3 目标用户
- macOS 开发者
- 系统管理员
- 性能调优工程师
- 对系统性能监控有需求的 Mac 用户

## 2. 功能需求

### 2.1 核心监控指标

#### 2.1.1 CPU 监控
- **每核心 CPU 占用率**：显示每个 CPU 核心的实时占用率
- **E-Core 和 P-Core 区分**：针对 Apple Silicon，区分效率核心和性能核心
- **CPU 总占用率**：整体 CPU 使用情况
- **CPU 功耗**：实时 CPU 功耗（瓦特）
- **CPU 温度**：CPU 温度监控
- **历史图表**：显示每个核心的历史占用率趋势图

#### 2.1.2 内存监控
- **内存使用率**：已用/总内存
- **内存详情**：可用内存、已缓存、已使用
- **Swap 使用情况**：Swap 总量和使用量
- **历史图表**：内存使用历史趋势图

#### 2.1.3 网络监控
- **上行流量**：实时上传速度（KB/s, MB/s）
- **下行流量**：实时下载速度（KB/s, MB/s）
- **网络接口**：支持多个网络接口监控
- **历史图表**：上行/下行流量历史趋势图

#### 2.1.4 功耗监控
- **CPU 功耗**：CPU 功耗（瓦特）
- **GPU 功耗**：GPU 功耗（瓦特）
- **ANE 功耗**：Apple Neural Engine 功耗（瓦特）
- **DRAM 功耗**：内存功耗（瓦特）
- **系统总功耗**：整体系统功耗
- **历史图表**：各组件功耗历史趋势图

#### 2.1.5 GPU 监控
- **GPU 占用率**：GPU 使用百分比
- **GPU 频率**：当前 GPU 频率（MHz）
- **GPU 温度**：GPU 温度
- **GPU 功耗**：GPU 功耗（瓦特）
- **历史图表**：GPU 占用率和频率历史趋势图

#### 2.1.6 ANE (Apple Neural Engine) 监控
- **ANE 占用率**：Neural Engine 使用百分比（如果可获取）
- **ANE 功耗**：ANE 功耗（瓦特）
- **历史图表**：ANE 占用率和功耗历史趋势图

### 2.2 UI 功能

#### 2.2.1 布局设计
- **多面板布局**：支持多种布局模式（类似 bashtop）
  - 默认布局：主要指标 + 历史图表
  - 紧凑布局：最小化空间占用
  - 详细布局：显示所有详细信息
  - 垂直布局：适合宽屏显示器
- **实时更新**：可配置的更新间隔（默认 1 秒）
- **响应式设计**：自动适应终端窗口大小

#### 2.2.2 历史图表
- **图表类型**：ASCII 字符绘制的实时图表
- **时间范围**：可配置的历史数据保留时间（默认 60 秒）
- **多指标图表**：每个指标独立的历史图表
- **图表样式**：支持多种图表样式（线条图、柱状图等）

#### 2.2.3 交互功能
- **键盘快捷键**：
  - `q`：退出程序
  - `h`：显示帮助
  - `c`：切换颜色主题
  - `l`：切换布局模式
  - `+/-`：调整更新间隔
  - `r`：手动刷新
  - `s`：暂停/继续更新
- **颜色主题**：支持多种颜色主题（绿色、红色、蓝色、青色、品红、黄色、白色）
- **自动主题**：根据终端背景自动调整（亮色/暗色）

### 2.3 进程管理（可选功能）
- **进程列表**：显示运行中的进程
- **进程排序**：按 CPU、内存等排序
- **进程筛选**：搜索和筛选进程
- **进程操作**：终止进程（需要权限）

## 3. 技术实现方案

### 3.1 技术栈选择

#### 3.1.1 编程语言
- **Python 3.10+**：主要开发语言
  - 优势：丰富的库生态、快速开发
  - 考虑：性能可能不如 Go/C，但足够满足需求

#### 3.1.2 TUI 框架
- **Textual**（推荐）：现代化 Python TUI 框架
  - 优势：功能强大、文档完善、支持复杂布局
  - 备选：Rich（更简单但功能较少）、Blessed（底层但灵活）

#### 3.1.3 系统监控库
- **psutil**：跨平台系统监控库
  - CPU、内存、网络、磁盘基础监控
- **原生 macOS API**（通过 Python C 扩展或 ctypes）：
  - **IOReport API**：获取 CPU、GPU、ANE、DRAM 功耗（无需 sudo）
  - **SMC (System Management Controller)**：获取温度传感器和系统功耗
  - **IOKit**：获取 GPU 频率
  - **Mach Kernel API**：获取 CPU 核心详细指标（E-Core/P-Core）
  - **IOHIDEventSystemClient**：温度传感器备用方案
  - **NSProcessInfo.thermalState**：系统热状态

#### 3.1.4 数据存储
- **内存缓存**：使用 Python 列表/队列存储历史数据
- **可选持久化**：支持导出 JSON/CSV 格式数据

### 3.2 数据获取方案

#### 3.2.1 CPU 指标
```python
# 基础指标（psutil）
- psutil.cpu_percent(percpu=True)  # 每核心占用率
- psutil.cpu_count(logical=True)   # 核心数量

# Apple Silicon 特定（需要原生 API）
- Mach Kernel API: host_processor_info()  # E-Core/P-Core 区分
- IOReport API: CPU 功耗
- SMC: CPU 温度
```

#### 3.2.2 GPU 指标
```python
# 需要原生 API
- IOReport API: GPU 占用率、功耗
- IOKit: GPU 频率（从 pmgr 设备）
- SMC: GPU 温度
```

#### 3.2.3 ANE 指标
```python
# 需要原生 API
- IOReport API: ANE 功耗
- IOReport API: ANE 占用率（如果可用）
```

#### 3.2.4 内存指标
```python
# psutil
- psutil.virtual_memory()  # 内存使用情况
- psutil.swap_memory()     # Swap 使用情况
```

#### 3.2.5 网络指标
```python
# psutil
- psutil.net_io_counters(pernic=True)  # 网络接口统计
# 需要计算速率（当前值 - 上次值）/ 时间间隔
```

#### 3.2.6 功耗指标
```python
# 需要原生 API
- IOReport API: CPU/GPU/ANE/DRAM 功耗
- SMC: 系统总功耗（PSTR）
```

### 3.3 参考项目

#### 3.3.1 mactop
- **语言**：Go + CGO
- **特点**：无需 sudo，使用原生 Apple API
- **参考点**：API 使用方式、数据获取方法

#### 3.3.2 bashtop/bpytop
- **语言**：Bash/Python
- **特点**：历史图表、美观的 UI
- **参考点**：UI 设计、图表绘制方式

#### 3.3.3 asitop
- **语言**：Python
- **特点**：Apple Silicon 监控
- **参考点**：powermetrics 使用方式（需要 sudo）

### 3.4 技术挑战与解决方案

#### 3.4.1 挑战：访问 Apple 私有 API
- **解决方案**：
  - 使用 Python C 扩展调用 C/Objective-C 代码
  - 或使用 ctypes 直接调用 C 函数
  - 参考 mactop 的实现方式

#### 3.4.2 挑战：性能优化
- **解决方案**：
  - 使用多线程/异步更新不同指标
  - 优化历史数据存储（使用 deque 限制大小）
  - 图表渲染优化（只更新变化部分）

#### 3.4.3 挑战：兼容性
- **解决方案**：
  - 检测 Apple Silicon vs Intel Mac
  - 对于 Intel Mac，降级到基础功能（psutil）
  - 版本检测和功能降级

## 4. 项目结构

```
macmon-tui/
├── README.md
├── requirements.txt
├── setup.py
├── macmon_tui/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py           # Textual 应用主类
│   │   ├── widgets/         # UI 组件
│   │   │   ├── cpu_widget.py
│   │   │   ├── memory_widget.py
│   │   │   ├── network_widget.py
│   │   │   ├── power_widget.py
│   │   │   ├── gpu_widget.py
│   │   │   └── ane_widget.py
│   │   └── layouts/         # 布局定义
│   ├── collectors/          # 数据收集器
│   │   ├── __init__.py
│   │   ├── base.py          # 基础收集器接口
│   │   ├── psutil_collector.py
│   │   └── apple_api_collector.py  # Apple API 收集器
│   ├── native/              # 原生 API 绑定
│   │   ├── __init__.py
│   │   ├── ioreport.py      # IOReport API
│   │   ├── smc.py           # SMC API
│   │   ├── iokit.py         # IOKit API
│   │   └── mach.py          # Mach Kernel API
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── history.py       # 历史数据管理
│   │   ├── chart.py         # 图表绘制
│   │   └── config.py        # 配置管理
│   └── config/
│       └── default.yaml     # 默认配置
└── tests/
    └── ...
```

## 5. 开发计划

### 5.1 第一阶段：基础功能（MVP）
- [ ] 项目初始化和依赖管理
- [ ] Textual UI 框架集成
- [ ] psutil 基础监控（CPU、内存、网络）
- [ ] 基础 UI 布局
- [ ] 简单的历史图表显示

### 5.2 第二阶段：Apple Silicon 支持
- [ ] 原生 API 绑定开发（IOReport、SMC、IOKit）
- [ ] GPU 监控实现
- [ ] ANE 监控实现
- [ ] 功耗监控实现
- [ ] E-Core/P-Core 区分

### 5.3 第三阶段：UI 增强
- [ ] 多种布局模式
- [ ] 颜色主题支持
- [ ] 交互功能完善
- [ ] 图表样式优化

### 5.4 第四阶段：高级功能
- [ ] 进程管理
- [ ] 配置持久化
- [ ] 数据导出功能
- [ ] 性能优化

## 6. 非功能需求

### 6.1 性能要求
- 更新间隔：默认 1 秒，可配置
- CPU 占用：< 5%（空闲时）
- 内存占用：< 50MB

### 6.2 兼容性要求
- macOS 12.3+ (Monterey)
- Python 3.10+
- Apple Silicon (M1/M2/M3/M4) 完整支持
- Intel Mac 基础支持

### 6.3 用户体验要求
- 启动时间：< 2 秒
- 响应流畅：UI 更新无卡顿
- 易用性：清晰的快捷键提示

### 6.4 安全性要求
- 无需 sudo 权限运行（使用公开 API）
- 不收集用户数据
- 本地运行，无网络请求

## 7. 成功指标

### 7.1 功能完整性
- 所有核心监控指标正常工作
- 历史图表正确显示
- UI 交互流畅

### 7.2 性能指标
- 满足性能要求
- 资源占用低

### 7.3 用户体验
- 界面美观易用
- 文档完善
- 易于安装和使用

## 8. 风险评估

### 8.1 技术风险
- **风险**：Apple 私有 API 可能在未来版本中变更
- **缓解**：使用公开 API 优先，私有 API 作为补充

### 8.2 开发风险
- **风险**：原生 API 绑定开发复杂度高
- **缓解**：参考现有项目（mactop），逐步实现

### 8.3 兼容性风险
- **风险**：不同 macOS 版本 API 差异
- **缓解**：版本检测和功能降级

## 9. 参考资料

### 9.1 相关项目
- [mactop](https://github.com/context-labs/mactop)：Apple Silicon 监控工具（Go）
- [bashtop](https://github.com/aristocratos/bashtop)：终端系统监控工具
- [bpytop](https://github.com/aristocratos/bpytop)：bashtop 的 Python 版本
- [asitop](https://github.com/tlkh/asitop)：Apple Silicon 监控工具（Python，需要 sudo）

### 9.2 技术文档
- [Textual 文档](https://textual.textualize.io/)
- [psutil 文档](https://psutil.readthedocs.io/)
- [Apple IOReport Framework](https://developer.apple.com/documentation/iokit/iokit_frameworks)
- [Apple SMC](https://developer.apple.com/documentation/iokit/iokit_frameworks)

### 9.3 macOS 系统工具
- `powermetrics`：系统性能监控工具（需要 sudo）
- `top`：进程监控
- `iostat`：I/O 统计
- `system_profiler`：系统信息

## 10. 附录

### 10.1 术语表
- **TUI**：Terminal User Interface，终端用户界面
- **E-Core**：Efficiency Core，效率核心（Apple Silicon）
- **P-Core**：Performance Core，性能核心（Apple Silicon）
- **ANE**：Apple Neural Engine，苹果神经网络引擎
- **SMC**：System Management Controller，系统管理控制器
- **IOReport**：macOS I/O 报告框架
- **IOKit**：macOS I/O Kit 框架

### 10.2 待定事项
- [ ] 项目名称最终确定
- [ ] 图标和品牌设计
- [ ] 发布渠道（Homebrew、PyPI）
- [ ] 许可证选择（MIT/Apache）

