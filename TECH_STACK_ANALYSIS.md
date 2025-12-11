# 技术栈设计文档：FastAPI + Vite + React

## 技术栈选择

### 最终方案
- **后端**：Python FastAPI
- **前端**：Vite + React + TypeScript
- **部署方式**：前端编译为静态文件，由 FastAPI serve

### 为什么选择这个方案？

#### 1. 最大化代码复用
- ✅ 保留现有 Python 代码（`collector.py`, `apple_api.py`, `history.py`）
- ✅ 只需添加 FastAPI 包装层，无需重写数据收集逻辑

#### 2. 开发体验优秀
- ✅ **Vite HMR**：极快的热更新，修改代码立即看到效果
- ✅ **React 生态**：丰富的组件库和工具
- ✅ **TypeScript**：类型安全，减少错误

#### 3. 部署简单高效
- ✅ **静态文件部署**：前端编译后是纯静态文件（HTML/CSS/JS）
- ✅ **单一服务**：FastAPI 同时 serve 静态文件和 API
- ✅ **无需 Nginx**：开发和生产环境一致，简化部署
- ✅ **资源占用低**：静态文件由 FastAPI 直接 serve，无需额外服务器

#### 4. 架构清晰
- ✅ **前后端分离**：开发时独立运行，生产时统一部署
- ✅ **API 优先**：REST API + WebSocket，易于扩展和测试

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────┐
│                  用户浏览器                        │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────────┐
│              FastAPI Server                      │
│  ┌──────────────────────────────────────────┐   │
│  │  Static Files (生产环境)                  │   │
│  │  - index.html                           │   │
│  │  - assets/*.js, *.css                   │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  API Endpoints                           │   │
│  │  - GET /api/metrics                     │   │
│  │  - GET /api/history                     │   │
│  │  - WS /ws/metrics (实时推送)             │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Data Collectors (复用现有代码)            │   │
│  │  - MetricsCollector                      │   │
│  │  - AppleAPICollector                     │   │
│  │  - MetricsHistory                        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 开发环境架构

```
开发时：
┌──────────────┐         ┌──────────────┐
│  Vite Dev    │  ────►  │  FastAPI     │
│  Server      │  Proxy  │  Server      │
│  :5173       │         │  :8000       │
└──────────────┘         └──────────────┘
     │                         │
     └─────────► Browser ◄────┘
              :5173 (前端)
              :8000 (API)
```

**开发流程**：
1. Vite Dev Server 运行在 `:5173`，提供前端 HMR
2. FastAPI 运行在 `:8000`，提供 API
3. Vite 配置 proxy，将 `/api/*` 请求转发到 FastAPI
4. 浏览器访问 `http://localhost:5173`

### 生产环境架构

```
生产时：
┌──────────────┐
│  FastAPI     │
│  Server      │
│  :8000       │
│              │
│  ├─ /        │ → serve static/index.html
│  ├─ /assets/ │ → serve static/assets/*
│  └─ /api/*   │ → API endpoints
└──────────────┘
```

**生产流程**：
1. 前端执行 `npm run build`，生成 `dist/` 目录
2. `dist/` 目录复制到 FastAPI 项目的 `static/` 目录
3. FastAPI 配置静态文件服务
4. 用户访问 `http://localhost:8000`，FastAPI 同时 serve 静态文件和 API

---

## 项目结构

```
yamon/
├── backend/                          # FastAPI 后端
│   ├── main.py                      # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   ├── metrics.py               # 指标 API 端点
│   │   └── websocket.py             # WebSocket 实时推送
│   ├── collectors/                   # 数据收集器（复用现有代码）
│   │   ├── __init__.py
│   │   ├── collector.py             # MetricsCollector
│   │   └── apple_api.py             # AppleAPICollector
│   ├── history.py                    # MetricsHistory（复用）
│   ├── static/                       # 静态文件目录（生产环境）
│   │   ├── index.html
│   │   └── assets/
│   │       ├── index-xxx.js
│   │       └── index-xxx.css
│   ├── requirements.txt
│   └── .env                          # 环境变量（可选）
│
├── frontend/                         # React + Vite 前端
│   ├── index.html                    # HTML 入口
│   ├── vite.config.ts                # Vite 配置
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx                  # React 入口
│   │   ├── App.tsx                   # 主应用组件
│   │   ├── components/
│   │   │   ├── CpuChart.tsx         # CPU 图表组件
│   │   │   ├── MemoryChart.tsx     # 内存图表组件
│   │   │   ├── NetworkChart.tsx     # 网络图表组件
│   │   │   ├── PowerChart.tsx      # 功耗图表组件
│   │   │   ├── GpuChart.tsx         # GPU 图表组件
│   │   │   └── AneChart.tsx         # ANE 图表组件
│   │   ├── hooks/
│   │   │   ├── useMetrics.ts        # 指标数据 hook
│   │   │   └── useWebSocket.ts      # WebSocket hook
│   │   ├── services/
│   │   │   └── api.ts               # API 客户端
│   │   ├── types/
│   │   │   └── metrics.ts            # TypeScript 类型定义
│   │   └── styles/
│   │       └── index.css            # 全局样式
│   └── dist/                         # 构建输出（.gitignore）
│
├── scripts/                          # 部署脚本
│   ├── build.sh                      # 构建脚本
│   └── deploy.sh                     # 部署脚本
│
├── README.md
├── .gitignore
└── PRD.md
```

---

## 详细实现方案

### 1. 后端实现（FastAPI）

#### 1.1 FastAPI 主应用 (`backend/main.py`)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os

from backend.api import metrics, websocket

app = FastAPI(title="Yamon API", version="1.0.0")

# CORS 配置（开发环境需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# 静态文件服务（生产环境）
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    # 如果存在静态文件，serve 它们
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA - 所有非 API 路由都返回 index.html"""
        if full_path.startswith("api") or full_path.startswith("ws"):
            return {"error": "Not found"}
        
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"error": "Static files not found"}

@app.get("/")
async def root():
    """根路径"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Yamon API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 1.2 指标 API (`backend/api/metrics.py`)

```python
from fastapi import APIRouter
from backend.collectors.collector import MetricsCollector
from backend.history import MetricsHistory
from typing import Optional

router = APIRouter()
collector = MetricsCollector()
history = MetricsHistory(max_size=60)

@router.get("/metrics")
async def get_metrics():
    """获取当前系统指标"""
    metrics = collector.collect()
    history.add_metrics(metrics)
    return {
        "cpu_percent": metrics.cpu_percent,
        "cpu_per_core": metrics.cpu_per_core,
        "memory_percent": metrics.memory_percent,
        "network_sent_rate": metrics.network_sent_rate,
        "network_recv_rate": metrics.network_recv_rate,
        "cpu_power": metrics.cpu_power,
        "gpu_power": metrics.gpu_power,
        "ane_power": metrics.ane_power,
        "system_power": metrics.system_power,
        "gpu_usage": metrics.gpu_usage,
        "ane_usage": metrics.ane_usage,
    }

@router.get("/history")
async def get_history():
    """获取历史数据"""
    return {
        "cpu_percent": history.cpu_percent.get_values(),
        "memory_percent": history.memory_percent.get_values(),
        "network_sent_rate": history.network_sent_rate.get_values(),
        "network_recv_rate": history.network_recv_rate.get_values(),
        "cpu_power": history.cpu_power.get_values(),
        "gpu_power": history.gpu_power.get_values(),
        "ane_power": history.ane_power.get_values(),
        "system_power": history.system_power.get_values(),
        "gpu_usage": history.gpu_usage.get_values(),
        "ane_usage": history.ane_usage.get_values(),
    }
```

#### 1.3 WebSocket 实时推送 (`backend/api/websocket.py`)

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.collectors.collector import MetricsCollector
from backend.history import MetricsHistory
import asyncio
import json

router = APIRouter()
collector = MetricsCollector()
history = MetricsHistory(max_size=60)

@router.websocket("/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket 实时推送系统指标"""
    await websocket.accept()
    
    try:
        while True:
            # 收集指标
            metrics = collector.collect()
            history.add_metrics(metrics)
            
            # 发送数据
            await websocket.send_json({
                "cpu_percent": metrics.cpu_percent,
                "cpu_per_core": metrics.cpu_per_core,
                "memory_percent": metrics.memory_percent,
                "network_sent_rate": metrics.network_sent_rate,
                "network_recv_rate": metrics.network_recv_rate,
                "cpu_power": metrics.cpu_power,
                "gpu_power": metrics.gpu_power,
                "ane_power": metrics.ane_power,
                "system_power": metrics.system_power,
                "gpu_usage": metrics.gpu_usage,
                "ane_usage": metrics.ane_usage,
            })
            
            # 等待 1 秒
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
```

---

### 2. 前端实现（Vite + React + TypeScript）

#### 2.1 Vite 配置 (`frontend/vite.config.ts`)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
})
```

#### 2.2 TypeScript 类型定义 (`frontend/src/types/metrics.ts`)

```typescript
export interface SystemMetrics {
  cpu_percent: number
  cpu_per_core: number[]
  memory_percent: number
  network_sent_rate: number
  network_recv_rate: number
  cpu_power: number | null
  gpu_power: number | null
  ane_power: number | null
  system_power: number | null
  gpu_usage: number | null
  ane_usage: number | null
}

export interface HistoryData {
  cpu_percent: number[]
  memory_percent: number[]
  network_sent_rate: number[]
  network_recv_rate: number[]
  cpu_power: number[]
  gpu_power: number[]
  ane_power: number[]
  system_power: number[]
  gpu_usage: number[]
  ane_usage: number[]
}
```

#### 2.3 WebSocket Hook (`frontend/src/hooks/useWebSocket.ts`)

```typescript
import { useEffect, useState, useRef } from 'react'
import { SystemMetrics } from '../types/metrics'

export function useWebSocket() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // 确定 WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.DEV 
      ? 'localhost:8000'  // 开发环境
      : window.location.host  // 生产环境
    const wsUrl = `${protocol}//${host}/ws/metrics`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as SystemMetrics
      setMetrics(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
      // 自动重连
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // 重新连接逻辑可以在这里实现
        }
      }, 3000)
    }

    return () => {
      ws.close()
    }
  }, [])

  return { metrics, connected }
}
```

#### 2.4 CPU 图表组件示例 (`frontend/src/components/CpuChart.tsx`)

```typescript
import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import { SystemMetrics } from '../types/metrics'

interface CpuChartProps {
  metrics: SystemMetrics | null
  history: number[]
}

export function CpuChart({ metrics, history }: CpuChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return

    // 初始化图表
    chartInstance.current = echarts.init(chartRef.current)

    // 响应式调整
    const resizeHandler = () => {
      chartInstance.current?.resize()
    }
    window.addEventListener('resize', resizeHandler)

    return () => {
      window.removeEventListener('resize', resizeHandler)
      chartInstance.current?.dispose()
    }
  }, [])

  useEffect(() => {
    if (!chartInstance.current || !metrics) return

    // 更新历史数据
    const updatedHistory = [...history, metrics.cpu_percent].slice(-60)

    chartInstance.current.setOption({
      title: {
        text: `CPU Usage: ${metrics.cpu_percent.toFixed(1)}%`,
        left: 'center',
        textStyle: { fontSize: 16 },
      },
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: updatedHistory.map((_, i) => i),
        show: false,
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        name: 'Usage %',
      },
      series: [
        {
          data: updatedHistory,
          type: 'line',
          smooth: true,
          areaStyle: {},
          lineStyle: { color: '#5470c6' },
          itemStyle: { color: '#5470c6' },
        },
      ],
      grid: {
        left: '10%',
        right: '10%',
        top: '20%',
        bottom: '10%',
      },
    })
  }, [metrics, history])

  return (
    <div className="chart-container">
      <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
    </div>
  )
}
```

#### 2.5 主应用组件 (`frontend/src/App.tsx`)

```typescript
import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { CpuChart } from './components/CpuChart'
import { MemoryChart } from './components/MemoryChart'
import { NetworkChart } from './components/NetworkChart'
import { PowerChart } from './components/PowerChart'
import { GpuChart } from './components/GpuChart'
import { AneChart } from './components/AneChart'
import { HistoryData } from './types/metrics'
import './styles/index.css'

function App() {
  const { metrics, connected } = useWebSocket()
  const [history, setHistory] = useState<HistoryData>({
    cpu_percent: [],
    memory_percent: [],
    network_sent_rate: [],
    network_recv_rate: [],
    cpu_power: [],
    gpu_power: [],
    ane_power: [],
    system_power: [],
    gpu_usage: [],
    ane_usage: [],
  })

  // 更新历史数据
  useEffect(() => {
    if (!metrics) return

    setHistory((prev) => ({
      cpu_percent: [...prev.cpu_percent, metrics.cpu_percent].slice(-60),
      memory_percent: [...prev.memory_percent, metrics.memory_percent].slice(-60),
      network_sent_rate: [...prev.network_sent_rate, metrics.network_sent_rate].slice(-60),
      network_recv_rate: [...prev.network_recv_rate, metrics.network_recv_rate].slice(-60),
      cpu_power: [...prev.cpu_power, metrics.cpu_power || 0].slice(-60),
      gpu_power: [...prev.gpu_power, metrics.gpu_power || 0].slice(-60),
      ane_power: [...prev.ane_power, metrics.ane_power || 0].slice(-60),
      system_power: [...prev.system_power, metrics.system_power || 0].slice(-60),
      gpu_usage: [...prev.gpu_usage, metrics.gpu_usage || 0].slice(-60),
      ane_usage: [...prev.ane_usage, metrics.ane_usage || 0].slice(-60),
    }))
  }, [metrics])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Yamon - Mac System Monitor</h1>
        <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>

      <main className="dashboard">
        <div className="grid">
          <div className="grid-item">
            <CpuChart metrics={metrics} history={history.cpu_percent} />
          </div>
          <div className="grid-item">
            <MemoryChart metrics={metrics} history={history.memory_percent} />
          </div>
          <div className="grid-item">
            <NetworkChart 
              metrics={metrics} 
              sentHistory={history.network_sent_rate}
              recvHistory={history.network_recv_rate}
            />
          </div>
          <div className="grid-item">
            <PowerChart 
              metrics={metrics}
              cpuHistory={history.cpu_power}
              gpuHistory={history.gpu_power}
              aneHistory={history.ane_power}
            />
          </div>
          <div className="grid-item">
            <GpuChart metrics={metrics} history={history.gpu_usage} />
          </div>
          <div className="grid-item">
            <AneChart metrics={metrics} history={history.ane_usage} />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
```

---

### 3. 构建和部署

#### 3.1 构建脚本 (`scripts/build.sh`)

```bash
#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Copying static files to backend..."
cd ..
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "Build complete! Static files are in backend/static/"
```

#### 3.2 部署脚本 (`scripts/deploy.sh`)

```bash
#!/bin/bash
set -e

# 构建前端
./scripts/build.sh

# 启动 FastAPI 服务器
echo "Starting FastAPI server..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 3.3 package.json 脚本 (`frontend/package.json`)

```json
{
  "name": "yamon-frontend",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

---

## 开发工作流

### 开发环境

1. **启动后端**：
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **访问应用**：
   - 前端：http://localhost:5173
   - API 文档：http://localhost:8000/docs

### 生产环境

1. **构建前端**：
   ```bash
   cd frontend
   npm run build
   ```

2. **复制静态文件**：
   ```bash
   cp -r frontend/dist/* backend/static/
   ```

3. **启动服务**：
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **访问应用**：
   - 应用：http://localhost:8000
   - API 文档：http://localhost:8000/docs

---

## 优势总结

### 1. 开发体验
- ✅ **Vite HMR**：修改代码立即看到效果，无需刷新
- ✅ **TypeScript**：类型安全，减少运行时错误
- ✅ **React 生态**：丰富的组件库和工具

### 2. 部署简单
- ✅ **单一服务**：FastAPI 同时 serve 静态文件和 API
- ✅ **无需 Nginx**：简化部署流程
- ✅ **静态文件**：前端编译后是纯静态文件，CDN 友好

### 3. 性能优化
- ✅ **代码分割**：Vite 自动代码分割，按需加载
- ✅ **资源优化**：自动压缩和优化资源
- ✅ **WebSocket**：实时推送，减少 HTTP 请求

### 4. 可扩展性
- ✅ **API 优先**：REST API 易于测试和扩展
- ✅ **前后端分离**：可以独立开发和部署
- ✅ **类型安全**：TypeScript 类型定义，前后端一致

---

## 下一步行动

1. **搭建项目结构**
   - [ ] 创建 `backend/` 和 `frontend/` 目录
   - [ ] 初始化 FastAPI 项目
   - [ ] 初始化 Vite + React 项目

2. **迁移现有代码**
   - [ ] 将 `yamon/collectors/` 移动到 `backend/collectors/`
   - [ ] 将 `yamon/history.py` 移动到 `backend/history.py`
   - [ ] 创建 FastAPI API 端点

3. **实现前端**
   - [ ] 创建基础布局和路由
   - [ ] 实现 WebSocket hook
   - [ ] 实现第一个图表组件（CPU Chart）

4. **测试和优化**
   - [ ] 测试开发环境
   - [ ] 测试生产构建
   - [ ] 性能优化
