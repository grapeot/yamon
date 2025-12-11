"""Metrics API endpoints"""

from fastapi import APIRouter
try:
    from yamon.collectors.collector import MetricsCollector
    from yamon.history import MetricsHistory
except ImportError:
    from collectors.collector import MetricsCollector
    from history import MetricsHistory
from typing import Optional

router = APIRouter()
collector = MetricsCollector()
history = MetricsHistory(max_size=120)

@router.get("/metrics")
async def get_metrics():
    """获取当前系统指标"""
    metrics = collector.collect()
    history.add_metrics(metrics)
    return {
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

