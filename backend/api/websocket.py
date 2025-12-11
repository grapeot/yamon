"""WebSocket API for real-time metrics"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
try:
    from backend.collectors.collector import MetricsCollector
    from backend.history import MetricsHistory
except ImportError:
    from collectors.collector import MetricsCollector
    from history import MetricsHistory
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
            
            # 等待 1 秒
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

