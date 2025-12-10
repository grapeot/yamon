"""Apple API bindings for macOS system monitoring

Uses powermetrics to access GPU, ANE, and power metrics.
Note: powermetrics requires sudo privileges, but provides comprehensive metrics.
"""

import subprocess
import platform
import re
import json
import plistlib
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
    
    def __init__(self, debug=False):
        self._is_apple_silicon = self._check_apple_silicon()
        self._powermetrics_available = False
        self._last_sample = None
        self._debug = debug
        
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
            result = self._collect_via_powermetrics()
            # Return empty metrics instead of None so UI can show "N/A"
            return result if result is not None else AppleMetrics()
        
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
                '--samplers', 'cpu_power,gpu_power,ane_power'
                # Use default text format - plist parsing is complex
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if self._debug:
                import sys
                print(f"[DEBUG] powermetrics return code: {result.returncode}", file=sys.stderr)
                if result.stderr:
                    print(f"[DEBUG] stderr: {result.stderr[:300]}", file=sys.stderr)
                if result.stdout:
                    print(f"[DEBUG] stdout sample: {result.stdout[:500]}", file=sys.stderr)
            
            if result.returncode != 0:
                # powermetrics requires sudo
                # Check if it's a permission error
                stderr_lower = result.stderr.lower() if result.stderr else ""
                if 'superuser' in stderr_lower or 'sudo' in stderr_lower:
                    # Return empty metrics instead of None so UI can show "N/A"
                    if self._debug:
                        import sys
                        print("[DEBUG] powermetrics requires sudo", file=sys.stderr)
                    return AppleMetrics()
                # Log other errors for debugging
                if self._debug:
                    import sys
                    print(f"[DEBUG] powermetrics error (code {result.returncode}): {result.stderr[:200]}", file=sys.stderr)
                return AppleMetrics()  # Return empty instead of None
            
            # Parse text output (more reliable than plist)
            parsed = self._parse_powermetrics_text(result.stdout)
            if self._debug:
                import sys
                print(f"[DEBUG] Parsed metrics: CPU={parsed.cpu_power}W, GPU={parsed.gpu_power}W, ANE={parsed.ane_power}W", file=sys.stderr)
            return parsed
        
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            import sys
            print(f"Error in powermetrics collection: {e}", file=sys.stderr)
            return None
    
    def _parse_powermetrics(self, data: dict) -> AppleMetrics:
        """Parse powermetrics plist output"""
        metrics = AppleMetrics()
        
        try:
            # powermetrics plist structure:
            # - Top level keys may include 'processor', 'gpu', 'ane', etc.
            # - Power values are typically in W (watts)
            
            # CPU Power - check multiple possible locations
            if 'processor' in data:
                proc = data['processor']
                # Try different key names
                for key in ['cpu_power', 'CPU Power', 'power', 'avg_power']:
                    if key in proc:
                        value = proc[key]
                        if isinstance(value, (int, float)):
                            metrics.cpu_power = float(value)
                        elif isinstance(value, str):
                            # Extract number from string like "5.971 W"
                            match = re.search(r'([\d.]+)', value)
                            if match:
                                metrics.cpu_power = float(match.group(1))
                        break
            
            # GPU Power
            if 'gpu' in data:
                gpu = data['gpu']
                for key in ['gpu_power', 'GPU Power', 'power', 'avg_power']:
                    if key in gpu:
                        value = gpu[key]
                        if isinstance(value, (int, float)):
                            metrics.gpu_power = float(value)
                        elif isinstance(value, str):
                            match = re.search(r'([\d.]+)', value)
                            if match:
                                metrics.gpu_power = float(match.group(1))
                        break
                
                # GPU usage and frequency
                if 'gpu_usage' in gpu:
                    metrics.gpu_usage = float(gpu['gpu_usage'])
                if 'gpu_freq' in gpu or 'frequency' in gpu:
                    freq = gpu.get('gpu_freq') or gpu.get('frequency')
                    if freq:
                        metrics.gpu_freq_mhz = float(freq)
            
            # ANE Power
            if 'ane' in data:
                ane = data['ane']
                for key in ['ane_power', 'ANE Power', 'power', 'avg_power']:
                    if key in ane:
                        value = ane[key]
                        if isinstance(value, (int, float)):
                            metrics.ane_power = float(value)
                        elif isinstance(value, str):
                            match = re.search(r'([\d.]+)', value)
                            if match:
                                metrics.ane_power = float(match.group(1))
                        break
                
                if 'ane_usage' in ane:
                    metrics.ane_usage = float(ane['ane_usage'])
            
            # System power (total)
            if 'system_power' in data:
                metrics.system_power = float(data['system_power'])
            elif 'total_power' in data:
                metrics.system_power = float(data['total_power'])
        
        except (KeyError, ValueError, TypeError) as e:
            # Log error for debugging
            import sys
            print(f"Error parsing powermetrics: {e}", file=sys.stderr)
        
        return metrics
    
    def _parse_powermetrics_text(self, text: str) -> Optional[AppleMetrics]:
        """Parse powermetrics text output"""
        metrics = AppleMetrics()
        
        if not text:
            return metrics
        
        # powermetrics text format examples:
        # "CPU Power: 5.971 W"
        # "GPU Power: 1.435 W"  
        # "ANE Power: 0.000 W"
        # Or in sections like:
        # "CPU Power: 5.971 W (average)"
        # "GPU Power: 1.435 W (average)"
        
        # Try multiple patterns for each metric
        cpu_patterns = [
            r'CPU Power:\s*([\d.]+)\s*W',
            r'CPU.*?power[:\s]+([\d.]+)',
            r'processor.*?power[:\s]+([\d.]+)',
            r'cpu_power[:\s]+([\d.]+)',
        ]
        
        gpu_patterns = [
            r'GPU Power:\s*([\d.]+)\s*W',
            r'GPU.*?power[:\s]+([\d.]+)',
            r'gpu_power[:\s]+([\d.]+)',
        ]
        
        ane_patterns = [
            r'ANE Power:\s*([\d.]+)\s*W',
            r'ANE.*?power[:\s]+([\d.]+)',
            r'ane_power[:\s]+([\d.]+)',
            r'Neural Engine.*?power[:\s]+([\d.]+)',
        ]
        
        # Extract CPU power
        for pattern in cpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    metrics.cpu_power = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract GPU power
        for pattern in gpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    metrics.gpu_power = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract ANE power
        for pattern in ane_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    metrics.ane_power = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Try to extract GPU frequency if available
        gpu_freq_match = re.search(r'GPU.*?frequency[:\s]+([\d.]+)\s*MHz', text, re.IGNORECASE)
        if gpu_freq_match:
            try:
                metrics.gpu_freq_mhz = float(gpu_freq_match.group(1))
            except (ValueError, IndexError):
                pass
        
        return metrics
    
    def is_available(self) -> bool:
        """Check if Apple API collection is available"""
        return self._is_apple_silicon

