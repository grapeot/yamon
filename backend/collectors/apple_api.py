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
    system_power: Optional[float] = None  # None if not available (requires SMC/IOReport for accurate total)
    
    # GPU
    gpu_usage: Optional[float] = None  # percentage, None if not available
    gpu_freq_mhz: Optional[float] = None  # MHz, None if not available
    
    # ANE
    ane_usage: Optional[float] = None  # percentage if available


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
            # Format: powermetrics -i 1000 -n 1 --samplers cpu_power,gpu_power,ane_power --show-process-gpu
            # Note: powermetrics doesn't directly provide GPU usage percentage
            # --show-process-gpu may provide per-process GPU time, but not overall usage
            # We'll try to get it via ioreg separately
            cmd = [
                'powermetrics',
                '-i', '1000',  # 1 second interval
                '-n', '1',     # 1 sample
                '--samplers', 'cpu_power,gpu_power,ane_power',
                '--show-process-gpu'  # Show per-process GPU time (may help calculate usage)
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
            
            # Try to get GPU usage via ioreg only if powermetrics didn't find it
            if parsed.gpu_usage is None:
                ioreg_usage = self._get_gpu_usage_via_ioreg()
                if ioreg_usage is not None:
                    parsed.gpu_usage = ioreg_usage
            
            if self._debug:
                import sys
                print(f"[DEBUG] Parsed metrics: CPU={parsed.cpu_power}W, GPU={parsed.gpu_power}W, ANE={parsed.ane_power}W, GPU Usage={parsed.gpu_usage}%", file=sys.stderr)
                # Log raw powermetrics output for debugging GPU usage
                print(f"[DEBUG] Raw powermetrics output (first 2000 chars):\n{result.stdout[:2000]}", file=sys.stderr)
                print(f"[DEBUG] Raw powermetrics output (last 2000 chars):\n{result.stdout[-2000:]}", file=sys.stderr)
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
                if 'gpu_usage' in gpu or 'utilization' in gpu:
                    usage = gpu.get('gpu_usage') or gpu.get('utilization')
                    if usage is not None:
                        try:
                            metrics.gpu_usage = float(usage)
                        except (ValueError, TypeError):
                            pass
                if 'gpu_freq' in gpu or 'frequency' in gpu:
                    freq = gpu.get('gpu_freq') or gpu.get('frequency')
                    if freq is not None:
                        try:
                            metrics.gpu_freq_mhz = float(freq)
                        except (ValueError, TypeError):
                            pass
            
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
                
                if 'ane_usage' in ane or 'utilization' in ane:
                    usage = ane.get('ane_usage') or ane.get('utilization')
                    if usage is not None:
                        try:
                            metrics.ane_usage = float(usage)
                        except (ValueError, TypeError):
                            pass
            
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
        
        import sys
        
        # powermetrics text format examples:
        # "CPU Power: 5.971 W"
        # "GPU Power: 1.435 W"  
        # "ANE Power: 0.000 W"
        # Or in sections like:
        # "CPU Power: 5.971 W (average)"
        # "GPU Power: 1.435 W (average)"
        
        # Try multiple patterns for each metric
        # powermetrics output format can vary, try common patterns
        # Check for mW unit indicators first
        mw_patterns = [
            r'CPU Power:\s*([\d.]+)\s*mW',  # "CPU Power: 10555 mW"
            r'GPU Power:\s*([\d.]+)\s*mW',
            r'ANE Power:\s*([\d.]+)\s*mW',
        ]
        
        # Extract with mW unit
        for pattern in mw_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value = float(match.group(1)) / 1000.0  # Convert mW to W
                    if 'CPU' in pattern.upper():
                        metrics.cpu_power = value
                    elif 'GPU' in pattern.upper():
                        metrics.gpu_power = value
                    elif 'ANE' in pattern.upper():
                        metrics.ane_power = value
                except (ValueError, IndexError):
                    pass
        
        cpu_patterns = [
            r'CPU Power:\s*([\d.]+)\s*W',  # "CPU Power: 5.971 W"
            r'CPU.*?power[:\s]+([\d.]+)',  # "CPU power: 5.971" or "CPU power: 10555"
            r'processor.*?power[:\s]+([\d.]+)',
            r'cpu_power[:\s]+([\d.]+)',
            r'CPU.*?([\d.]+)\s*W\s*\(average\)',  # "CPU Power: 5.971 W (average)"
        ]
        
        gpu_patterns = [
            r'GPU Power:\s*([\d.]+)\s*W',  # "GPU Power: 1.435 W"
            r'GPU.*?power[:\s]+([\d.]+)',
            r'gpu_power[:\s]+([\d.]+)',
            r'GPU.*?([\d.]+)\s*W\s*\(average\)',
        ]
        
        ane_patterns = [
            r'ANE Power:\s*([\d.]+)\s*W',  # "ANE Power: 0.000 W"
            r'ANE.*?power[:\s]+([\d.]+)',
            r'ane_power[:\s]+([\d.]+)',
            r'Neural Engine.*?power[:\s]+([\d.]+)',
            r'ANE.*?([\d.]+)\s*W\s*\(average\)',
        ]
        
        # Extract CPU power
        # Note: powermetrics may output in mW (milliwatts) or W (watts)
        # Check for unit indicators and convert accordingly
        for pattern in cpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value = float(match.group(1))
                    # Check if the pattern or surrounding text indicates mW
                    # If value > 100, it's likely mW (normal CPU power is 1-50W)
                    if value > 100:
                        metrics.cpu_power = value / 1000.0  # Convert mW to W
                    else:
                        metrics.cpu_power = value
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract GPU power
        for pattern in gpu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value = float(match.group(1))
                    # GPU power typically 0.5-30W, if > 100 likely mW
                    if value > 100:
                        metrics.gpu_power = value / 1000.0  # Convert mW to W
                    else:
                        metrics.gpu_power = value
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract ANE power
        for pattern in ane_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value = float(match.group(1))
                    # ANE power typically 0-10W, if > 100 likely mW
                    if value > 100:
                        metrics.ane_power = value / 1000.0  # Convert mW to W
                    else:
                        metrics.ane_power = value
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract system total power
        # powermetrics may output "Combined Power (CPU + GPU + ANE): X mW"
        # but system total power should include DRAM and other components
        # Look for patterns like "Total Power", "System Power", or calculate from components
        system_power_patterns = [
            r'Total Power[:\s]+([\d.]+)\s*(?:mW|W)',
            r'System Power[:\s]+([\d.]+)\s*(?:mW|W)',
            r'Total.*?power[:\s]+([\d.]+)\s*(?:mW|W)',
            r'system_power[:\s]+([\d.]+)',
            r'total_power[:\s]+([\d.]+)',
        ]
        
        for pattern in system_power_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    value = float(match.group(1))
                    # Check if it's mW (if > 100, likely mW for system power)
                    if value > 100:
                        metrics.system_power = value / 1000.0  # Convert mW to W
                    else:
                        metrics.system_power = value
                    import sys
                    if self._debug:
                        print(f"[DEBUG] Found system power via pattern '{pattern}': {metrics.system_power}W", file=sys.stderr)
                    break
                except (ValueError, IndexError):
                    continue
        
        # If system power not found, try to calculate from Combined Power + DRAM
        # Note: This is approximate as it doesn't include all system components
        # System total power typically includes: CPU + GPU + ANE + DRAM + other system components
        # macmon shows ~50W total, which is higher than Combined Power (~9W)
        # This suggests we need to use a different method or find the actual system power field
        if metrics.system_power == 0.0:
            combined_match = re.search(r'Combined Power.*?\(CPU.*?GPU.*?ANE\)[:\s]+([\d.]+)\s*mW', text, re.IGNORECASE)
            if combined_match:
                try:
                    combined_mw = float(combined_match.group(1))
                    combined_w = combined_mw / 1000.0
                    # Try to find DRAM power
                    dram_match = re.search(r'DRAM.*?Power[:\s]+([\d.]+)\s*(?:mW|W)', text, re.IGNORECASE)
                    dram_w = 0.0
                    if dram_match:
                        try:
                            dram_value = float(dram_match.group(1))
                            dram_w = dram_value / 1000.0 if dram_value > 100 else dram_value
                        except (ValueError, IndexError):
                            pass
                    
                    # System power is typically much higher than combined power
                    # Based on macmon showing ~50W vs Combined ~9W, there's significant overhead
                    # For now, if we can't find actual system power, set to None
                    # The frontend can display "N/A" or calculate an estimate
                    # Note: To get accurate system power, we may need to use SMC or IOReport API
                    if self._debug:
                        print(f"[DEBUG] System power not found. Combined Power: {combined_w}W, DRAM: {dram_w}W. Setting to None (need SMC/IOReport for accurate total)", file=sys.stderr)
                    metrics.system_power = None  # Set to None instead of approximate value
                except (ValueError, IndexError):
                    pass
        
        # Try to extract GPU frequency if available
        gpu_freq_match = re.search(r'GPU.*?frequency[:\s]+([\d.]+)\s*MHz', text, re.IGNORECASE)
        if gpu_freq_match:
            try:
                metrics.gpu_freq_mhz = float(gpu_freq_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Try to extract GPU usage (percentage)
        # powermetrics outputs GPU usage in the "**** GPU usage ****" section
        # Format: "GPU idle residency: X.XX%"
        # GPU usage = 100% - GPU idle residency
        # Or use "GPU HW active residency: X.XX%" directly
        
        # First, try to find GPU idle residency and calculate usage
        gpu_idle_match = re.search(r'GPU idle residency[:\s]+([\d.]+)\s*%', text, re.IGNORECASE | re.MULTILINE)
        if gpu_idle_match:
            try:
                idle_percent = float(gpu_idle_match.group(1))
                metrics.gpu_usage = 100.0 - idle_percent
                import sys
                print(f"[DEBUG] Found GPU usage via idle residency: {metrics.gpu_usage}% (idle: {idle_percent}%)", file=sys.stderr)
            except (ValueError, IndexError):
                pass
        
        # If not found via idle residency, try GPU HW active residency
        if metrics.gpu_usage is None:
            gpu_active_match = re.search(r'GPU HW active residency[:\s]+([\d.]+)\s*%', text, re.IGNORECASE | re.MULTILINE)
            if gpu_active_match:
                try:
                    metrics.gpu_usage = float(gpu_active_match.group(1))
                    import sys
                    print(f"[DEBUG] Found GPU usage via HW active residency: {metrics.gpu_usage}%", file=sys.stderr)
                except (ValueError, IndexError):
                    pass
        
        # Fallback: try other patterns
        if metrics.gpu_usage is None:
            gpu_usage_patterns = [
                r'GPU.*?Utilization[:\s]+([\d.]+)\s*%',
                r'GPU.*?Usage[:\s]+([\d.]+)\s*%',
                r'GPU[:\s]+([\d.]+)\s*%',
                r'gpu_utilization[:\s]+([\d.]+)',
                r'gpu_usage[:\s]+([\d.]+)',
            ]
            for pattern in gpu_usage_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        metrics.gpu_usage = float(match.group(1))
                        import sys
                        print(f"[DEBUG] Found GPU usage via pattern '{pattern}': {metrics.gpu_usage}%", file=sys.stderr)
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Log if GPU usage still not found
        if metrics.gpu_usage is None:
            import sys
            print(f"[DEBUG] GPU usage not found in powermetrics output", file=sys.stderr)
        
        # Try to extract ANE usage if available
        ane_usage_patterns = [
            r'ANE.*?Utilization[:\s]+([\d.]+)\s*%',
            r'ANE.*?Usage[:\s]+([\d.]+)\s*%',
            r'Neural Engine.*?Usage[:\s]+([\d.]+)\s*%',
            r'ane_utilization[:\s]+([\d.]+)',
            r'ane_usage[:\s]+([\d.]+)',
        ]
        for pattern in ane_usage_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    metrics.ane_usage = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        return metrics
    
    def _get_gpu_usage_via_ioreg(self) -> Optional[float]:
        """Try to get GPU usage percentage via ioreg"""
        import sys
        try:
            # Try to query GPU performance controller
            # This is a best-effort attempt - may not work on all systems
            result = subprocess.run(
                ['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if self._debug:
                print(f"[DEBUG] ioreg IOAccelerator return code: {result.returncode}", file=sys.stderr)
                if result.stdout:
                    print(f"[DEBUG] ioreg IOAccelerator output (first 500 chars):\n{result.stdout[:500]}", file=sys.stderr)
            
            if result.returncode == 0 and result.stdout:
                # Look for GPU utilization patterns in ioreg output
                # This is system-dependent and may need adjustment
                utilization_match = re.search(
                    r'utilization[:\s]+(\d+)',
                    result.stdout,
                    re.IGNORECASE
                )
                if utilization_match:
                    try:
                        usage = float(utilization_match.group(1))
                        if self._debug:
                            print(f"[DEBUG] Found GPU usage via IOAccelerator: {usage}%", file=sys.stderr)
                        return usage
                    except (ValueError, IndexError):
                        pass
            
            # Alternative: Try querying AGXAccelerator (Apple Silicon GPU)
            result = subprocess.run(
                ['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'AGXAccelerator'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
            if self._debug:
                print(f"[DEBUG] ioreg AGXAccelerator return code: {result.returncode}", file=sys.stderr)
                if result.stdout:
                    print(f"[DEBUG] ioreg AGXAccelerator output (first 500 chars):\n{result.stdout[:500]}", file=sys.stderr)
            
            if result.returncode == 0 and result.stdout:
                # Look for various GPU metrics
                patterns = [
                    r'utilization[:\s]+(\d+)',
                    r'gpu.*?usage[:\s]+(\d+)',
                    r'active.*?percent[:\s]+(\d+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, result.stdout, re.IGNORECASE)
                    if match:
                        try:
                            usage = float(match.group(1))
                            if self._debug:
                                print(f"[DEBUG] Found GPU usage via AGXAccelerator pattern '{pattern}': {usage}%", file=sys.stderr)
                            return usage
                        except (ValueError, IndexError):
                            continue
            
            if self._debug:
                print(f"[DEBUG] ioreg method did not find GPU usage", file=sys.stderr)
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # ioreg may not be available or may fail
            if self._debug:
                import sys
                print(f"[DEBUG] ioreg error: {e}", file=sys.stderr)
        
        return None
    
    def is_available(self) -> bool:
        """Check if Apple API collection is available"""
        return self._is_apple_silicon

