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
            # 收集间隔：1秒（1fps）
            await asyncio.sleep(1.0)
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
            
            # 计算 P 核和 E 核的使用率
            cpu_count = metrics.cpu_count
            cpu_per_core = metrics.cpu_per_core
            
            # 根据 CPU 核心数判断 P 核和 E 核数量
            if cpu_count == 8:
                # M1/M2/M3: 4P + 4E
                p_core_count = 4
                e_core_count = 4
            elif cpu_count == 10:
                # M1 Pro/Max: 8P + 2E
                p_core_count = 8
                e_core_count = 2
            elif cpu_count == 12:
                # M2 Pro/Max: 8P + 4E 或 M3 Pro: 6P + 6E
                # 默认假设 8P + 4E
                p_core_count = 8
                e_core_count = 4
            elif cpu_count == 16:
                # M3 Max: 12P + 4E
                p_core_count = 12
                e_core_count = 4
            else:
                # 默认：前一半是 P 核
                p_core_count = cpu_count // 2
                e_core_count = cpu_count - p_core_count
            
            # 计算 P 核和 E 核的使用率
            p_cores = cpu_per_core[:p_core_count] if len(cpu_per_core) >= p_core_count else []
            e_cores = cpu_per_core[p_core_count:] if len(cpu_per_core) > p_core_count else []
            
            # 计算 P 核和 E 核的总算力（所有核心使用率之和）
            p_total_usage = sum(p_cores) if p_cores else 0.0
            e_total_usage = sum(e_cores) if e_cores else 0.0
            total_usage = p_total_usage + e_total_usage
            
            # 计算 P 核和 E 核占整体CPU算力的百分比
            # 这样 P% + E% = 100%，表示它们各自占整体算力的比例
            if total_usage > 0:
                cpu_p_percent = (p_total_usage / total_usage) * 100.0
                cpu_e_percent = (e_total_usage / total_usage) * 100.0
            else:
                cpu_p_percent = 0.0
                cpu_e_percent = 0.0
            
            # 发送数据
            await websocket.send_json({
                "cpu_percent": metrics.cpu_percent,
                "cpu_per_core": metrics.cpu_per_core,
                "cpu_count": metrics.cpu_count,
                "cpu_p_percent": cpu_p_percent,
                "cpu_e_percent": cpu_e_percent,
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
            
            # 等待 1 秒（1fps）
            await asyncio.sleep(1.0)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

