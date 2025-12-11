"""WebSocket API for real-time metrics"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
try:
    from backend.collectors.collector import MetricsCollector, SystemMetrics
    from backend.history import MetricsHistory
except ImportError:
    from collectors.collector import MetricsCollector, SystemMetrics
    from history import MetricsHistory
import asyncio
import json
from typing import Optional

router = APIRouter()
collector = MetricsCollector()
history = MetricsHistory(max_size=120)

# 共享的最新指标数据（线程安全）
_latest_metrics: Optional[SystemMetrics] = None
_metrics_lock = asyncio.Lock()

# 后台收集任务
_collection_task: Optional[asyncio.Task] = None

async def _background_collector():
    """后台任务：持续收集指标数据"""
    global _latest_metrics
    while True:
        try:
            # 在线程池中运行同步的collect()方法，避免阻塞事件循环
            metrics = await asyncio.to_thread(collector.collect)
            async with _metrics_lock:
                _latest_metrics = metrics
            history.add_metrics(metrics)
            # 收集间隔：0.5秒（2fps）
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Background collector error: {e}")
            await asyncio.sleep(0.5)

async def start_background_collector():
    """启动后台收集任务"""
    global _collection_task
    if _collection_task is None or _collection_task.done():
        _collection_task = asyncio.create_task(_background_collector())

@router.websocket("/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket 实时推送系统指标"""
    await websocket.accept()
    
    # 确保后台收集任务已启动
    await start_background_collector()
    
    try:
        while True:
            # 读取最新数据（不等待收集完成）
            async with _metrics_lock:
                metrics = _latest_metrics
            
            if metrics is None:
                # 如果还没有数据，等待一下
                await asyncio.sleep(0.1)
                continue
            
            # 发送数据
            await websocket.send_json({
                "cpu_percent": metrics.cpu_percent,
                "cpu_per_core": metrics.cpu_per_core,
                "cpu_count": metrics.cpu_count,
                "memory_percent": metrics.memory_percent,
                "memory_total": metrics.memory_total,
                "memory_used": metrics.memory_used,
                "memory_available": metrics.memory_available,
                "network_sent_rate": metrics.network_sent_rate,
                "network_recv_rate": metrics.network_recv_rate,
                "cpu_power": metrics.cpu_power,
                "gpu_power": metrics.gpu_power,
                "ane_power": metrics.ane_power,
                "system_power": metrics.system_power,
                "gpu_usage": metrics.gpu_usage,
                "gpu_freq_mhz": metrics.gpu_freq_mhz,
                "ane_usage": metrics.ane_usage,
            })
            
            # 等待 0.5 秒（2fps）
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

