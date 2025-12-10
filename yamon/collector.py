"""System metrics collector"""

import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SystemMetrics:
    """System metrics data structure"""
    # CPU
    cpu_percent: float
    cpu_per_core: List[float]
    cpu_count: int
    
    # Memory
    memory_total: int  # bytes
    memory_used: int   # bytes
    memory_percent: float
    swap_total: int    # bytes
    swap_used: int     # bytes
    
    # Network
    network_sent: int      # bytes
    network_recv: int      # bytes
    network_sent_rate: float  # bytes/sec
    network_recv_rate: float  # bytes/sec


class MetricsCollector:
    """Collect system metrics using psutil"""
    
    def __init__(self):
        self._last_network_sent = 0
        self._last_network_recv = 0
        self._last_time = None
    
    def collect(self) -> SystemMetrics:
        """Collect current system metrics"""
        import time
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = psutil.cpu_count(logical=True)
        
        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Network
        net_io = psutil.net_io_counters()
        current_time = time.time()
        
        # Calculate network rates
        if self._last_time is not None:
            time_delta = current_time - self._last_time
            if time_delta > 0:
                network_sent_rate = (net_io.bytes_sent - self._last_network_sent) / time_delta
                network_recv_rate = (net_io.bytes_recv - self._last_network_recv) / time_delta
            else:
                network_sent_rate = 0.0
                network_recv_rate = 0.0
        else:
            network_sent_rate = 0.0
            network_recv_rate = 0.0
        
        # Update last values
        self._last_network_sent = net_io.bytes_sent
        self._last_network_recv = net_io.bytes_recv
        self._last_time = current_time
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            cpu_count=cpu_count,
            memory_total=mem.total,
            memory_used=mem.used,
            memory_percent=mem.percent,
            swap_total=swap.total,
            swap_used=swap.used,
            network_sent=net_io.bytes_sent,
            network_recv=net_io.bytes_recv,
            network_sent_rate=network_sent_rate,
            network_recv_rate=network_recv_rate,
        )
    
    def format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"

