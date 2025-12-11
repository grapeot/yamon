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
    
    # Calculate P-core and E-core percentages
    cpu_per_core = metrics.cpu_per_core
    cpu_count = metrics.cpu_count
    
    # Determine P-core and E-core counts
    if cpu_count == 8:
        p_core_count = 4
        e_core_count = 4
    elif cpu_count == 10:
        p_core_count = 8
        e_core_count = 2
    elif cpu_count == 12:
        p_core_count = 8
        e_core_count = 4
    elif cpu_count == 16:
        p_core_count = 12
        e_core_count = 4
    else:
        p_core_count = cpu_count // 2
        e_core_count = cpu_count - p_core_count
    
    p_cores = cpu_per_core[:p_core_count] if len(cpu_per_core) >= p_core_count else []
    e_cores = cpu_per_core[p_core_count:] if len(cpu_per_core) > p_core_count else []
    
    if cpu_count > 0:
        cpu_p_percent = (sum(p_cores) / cpu_count) if p_cores else 0.0
        cpu_e_percent = (sum(e_cores) / cpu_count) if e_cores else 0.0
    else:
        cpu_p_percent = 0.0
        cpu_e_percent = 0.0
    
    return {
        "cpu_percent": metrics.cpu_percent,
        "cpu_per_core": metrics.cpu_per_core,
        "cpu_count": metrics.cpu_count,
        "cpu_p_percent": cpu_p_percent,
        "cpu_e_percent": cpu_e_percent,
        "pcpu_freq_mhz": metrics.pcpu_freq_mhz,
        "ecpu_freq_mhz": metrics.ecpu_freq_mhz,
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

