"""Apple API bindings for macOS system monitoring

Uses powermetrics to access GPU, ANE, and power metrics.
Note: powermetrics requires sudo privileges, but provides comprehensive metrics.
"""

import subprocess
import platform
import re
import json
from typing import Optional
from dataclasses import dataclass


@dataclass
class AppleMetrics:
    """Apple Silicon specific metrics"""
    # Power (watts)
    cpu_power: float = 0.0
    gpu_power: float = 0.0
    ane_power: float = 0.0
    dram_power: float = 0.0
    system_power: float = 0.0
    
    # GPU
    gpu_usage: float = 0.0  # percentage
    gpu_freq_mhz: float = 0.0
    
    # ANE
    ane_usage: float = 0.0  # percentage if available


class AppleAPICollector:
    """Collect Apple Silicon specific metrics using powermetrics"""
    
    def __init__(self):
        self._is_apple_silicon = self._check_apple_silicon()
        self._powermetrics_available = False
        self._last_sample = None
        
        if self._is_apple_silicon:
            self._check_powermetrics()
    
    def _check_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon"""
        try:
            arch = platform.machine()
            return arch == 'arm64'
        except Exception:
            return False
    
    def _check_powermetrics(self) -> None:
        """Check if powermetrics is available"""
        try:
            result = subprocess.run(
                ['which', 'powermetrics'],
                capture_output=True,
                timeout=1
            )
            self._powermetrics_available = result.returncode == 0
        except Exception:
            self._powermetrics_available = False
    
    def collect(self) -> Optional[AppleMetrics]:
        """Collect Apple Silicon metrics using powermetrics"""
        if not self._is_apple_silicon:
            return None
        
        # Try to use powermetrics if available
        # Note: This requires sudo, so it may fail
        if self._powermetrics_available:
            return self._collect_via_powermetrics()
        
        # Return empty metrics if not available
        return AppleMetrics()
    
    def _collect_via_powermetrics(self) -> Optional[AppleMetrics]:
        """Collect metrics using powermetrics command"""
        try:
            # Run powermetrics with a short sample interval
            # Format: powermetrics -i 1000 -n 1 --samplers cpu_power,gpu_power,ane_power
            cmd = [
                'powermetrics',
                '-i', '1000',  # 1 second interval
                '-n', '1',     # 1 sample
                '--samplers', 'cpu_power,gpu_power,ane_power,dram_power',
                '--format', 'json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=3,
                text=True
            )
            
            if result.returncode != 0:
                # powermetrics requires sudo, so this will likely fail
                return None
            
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                return self._parse_powermetrics(data)
            except json.JSONDecodeError:
                # Try parsing text output as fallback
                return self._parse_powermetrics_text(result.stdout)
        
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _parse_powermetrics(self, data: dict) -> AppleMetrics:
        """Parse powermetrics JSON output"""
        metrics = AppleMetrics()
        
        try:
            # Extract power metrics from JSON structure
            # Structure varies by macOS version
            if 'processor' in data:
                proc = data['processor']
                if 'cpu_power' in proc:
                    metrics.cpu_power = float(proc['cpu_power'])
            
            if 'gpu' in data:
                gpu = data['gpu']
                if 'gpu_power' in gpu:
                    metrics.gpu_power = float(gpu['gpu_power'])
                if 'gpu_usage' in gpu:
                    metrics.gpu_usage = float(gpu['gpu_usage'])
                if 'gpu_freq' in gpu:
                    metrics.gpu_freq_mhz = float(gpu['gpu_freq'])
            
            if 'ane' in data:
                ane = data['ane']
                if 'ane_power' in ane:
                    metrics.ane_power = float(ane['ane_power'])
                if 'ane_usage' in ane:
                    metrics.ane_usage = float(ane['ane_usage'])
            
            if 'dram' in data:
                dram = data['dram']
                if 'dram_power' in dram:
                    metrics.dram_power = float(dram['dram_power'])
        
        except (KeyError, ValueError, TypeError):
            pass
        
        return metrics
    
    def _parse_powermetrics_text(self, text: str) -> Optional[AppleMetrics]:
        """Parse powermetrics text output as fallback"""
        metrics = AppleMetrics()
        
        # Try to extract power values using regex
        # This is a simplified parser - actual output format may vary
        patterns = {
            'cpu_power': r'CPU Power:\s*([\d.]+)\s*W',
            'gpu_power': r'GPU Power:\s*([\d.]+)\s*W',
            'ane_power': r'ANE Power:\s*([\d.]+)\s*W',
            'dram_power': r'DRAM Power:\s*([\d.]+)\s*W',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    if key == 'cpu_power':
                        metrics.cpu_power = value
                    elif key == 'gpu_power':
                        metrics.gpu_power = value
                    elif key == 'ane_power':
                        metrics.ane_power = value
                    elif key == 'dram_power':
                        metrics.dram_power = value
                except ValueError:
                    pass
        
        return metrics
    
    def is_available(self) -> bool:
        """Check if Apple API collection is available"""
        return self._is_apple_silicon

