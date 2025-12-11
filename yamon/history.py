"""History data storage and management"""

from collections import deque
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class HistoryConfig:
    """Configuration for history storage"""
    max_size: int = 120  # Keep 120 data points (2 minutes at 1s interval)
    enabled: bool = True


class HistoryBuffer:
    """Circular buffer for storing historical metrics"""
    
    def __init__(self, max_size: int = 120):
        self.max_size = max_size
        self._data = deque(maxlen=max_size)
    
    def add(self, value: float) -> None:
        """Add a new value to history"""
        self._data.append(value)
    
    def get_values(self) -> List[float]:
        """Get all historical values"""
        return list(self._data)
    
    def get_latest(self, count: int) -> List[float]:
        """Get latest N values"""
        return list(self._data)[-count:]
    
    def clear(self) -> None:
        """Clear all history"""
        self._data.clear()
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self._data) >= self.max_size
    
    def size(self) -> int:
        """Get current size"""
        return len(self._data)


class MetricsHistory:
    """Store history for all metrics"""
    
    def __init__(self, max_size: int = 120):
        self.max_size = max_size
        
        # CPU
        self.cpu_percent = HistoryBuffer(max_size)
        self.cpu_per_core = {}  # Will be populated dynamically
        
        # Memory
        self.memory_percent = HistoryBuffer(max_size)
        
        # Network
        self.network_sent_rate = HistoryBuffer(max_size)
        self.network_recv_rate = HistoryBuffer(max_size)
        
        # Power
        self.cpu_power = HistoryBuffer(max_size)
        self.gpu_power = HistoryBuffer(max_size)
        self.ane_power = HistoryBuffer(max_size)
        self.system_power = HistoryBuffer(max_size)
        
        # GPU/ANE
        self.gpu_usage = HistoryBuffer(max_size)
        self.ane_usage = HistoryBuffer(max_size)
    
    def update_cpu_cores(self, core_count: int) -> None:
        """Initialize per-core history buffers"""
        for i in range(core_count):
            if i not in self.cpu_per_core:
                self.cpu_per_core[i] = HistoryBuffer(self.max_size)
    
    def add_metrics(self, metrics) -> None:
        """Add current metrics to history"""
        # CPU
        self.cpu_percent.add(metrics.cpu_percent)
        
        # Per-core CPU
        self.update_cpu_cores(len(metrics.cpu_per_core))
        for i, core_value in enumerate(metrics.cpu_per_core):
            if i in self.cpu_per_core:
                self.cpu_per_core[i].add(core_value)
        
        # Memory
        self.memory_percent.add(metrics.memory_percent)
        
        # Network
        self.network_sent_rate.add(metrics.network_sent_rate)
        self.network_recv_rate.add(metrics.network_recv_rate)
        
        # Power (only if available)
        if metrics.cpu_power is not None:
            self.cpu_power.add(metrics.cpu_power)
        if metrics.gpu_power is not None:
            self.gpu_power.add(metrics.gpu_power)
        if metrics.ane_power is not None:
            self.ane_power.add(metrics.ane_power)
        if metrics.system_power is not None:
            self.system_power.add(metrics.system_power)
        
        # GPU/ANE usage
        if metrics.gpu_usage is not None:
            self.gpu_usage.add(metrics.gpu_usage)
        if metrics.ane_usage is not None:
            self.ane_usage.add(metrics.ane_usage)

