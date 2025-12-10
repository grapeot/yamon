"""System metrics collector"""

import psutil
import subprocess
import json
import re
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
    
    # Apple Silicon specific (optional)
    cpu_power: Optional[float] = None  # watts
    gpu_power: Optional[float] = None  # watts
    ane_power: Optional[float] = None  # watts
    dram_power: Optional[float] = None  # watts
    system_power: Optional[float] = None  # watts
    gpu_usage: Optional[float] = None  # percentage
    gpu_freq_mhz: Optional[float] = None  # MHz
    ane_usage: Optional[float] = None  # percentage


class MetricsCollector:
    """Collect system metrics using psutil and Apple APIs"""
    
    def __init__(self):
        self._last_network_sent = 0
        self._last_network_recv = 0
        self._last_time = None
        self._apple_collector = None
        self._init_apple_collector()
    
    def _init_apple_collector(self):
        """Initialize Apple API collector if available"""
        try:
            from yamon.apple_api import AppleAPICollector
            self._apple_collector = AppleAPICollector()
        except Exception:
            self._apple_collector = None
    
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
        
        # Try to get Apple Silicon metrics
        apple_metrics = None
        if self._apple_collector:
            apple_metrics = self._apple_collector.collect()
        
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
            cpu_power=apple_metrics.cpu_power if apple_metrics else None,
            gpu_power=apple_metrics.gpu_power if apple_metrics else None,
            ane_power=apple_metrics.ane_power if apple_metrics else None,
            dram_power=apple_metrics.dram_power if apple_metrics else None,
            system_power=apple_metrics.system_power if apple_metrics else None,
            gpu_usage=apple_metrics.gpu_usage if apple_metrics else None,
            gpu_freq_mhz=apple_metrics.gpu_freq_mhz if apple_metrics else None,
            ane_usage=apple_metrics.ane_usage if apple_metrics else None,
        )
    
    def format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"

