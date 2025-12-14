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
    
    # CPU frequencies
    pcpu_freq_mhz: Optional[float] = None  # P-core frequency in MHz
    ecpu_freq_mhz: Optional[float] = None  # E-core frequency in MHz
    
    # GPU
    gpu_usage: Optional[float] = None  # percentage, None if not available
    gpu_freq_mhz: Optional[float] = None  # MHz, None if not available
    
    # ANE
    ane_usage: Optional[float] = None  # percentage if available


class AppleAPICollector:
    """Collect Apple Silicon specific metrics using IOReport API (no sudo) or powermetrics (requires sudo)"""
    
    def __init__(self, debug=False):
        self._is_apple_silicon = self._check_apple_silicon()
        self._powermetrics_available = False
        self._ioreport_available = False
        self._last_sample = None
        self._debug = debug
        self._smc = None
        self._ioreport = None
        
        if self._is_apple_silicon:
            self._check_powermetrics()
            self._init_smc()
            self._init_ioreport()
    
    def _init_smc(self):
        """Initialize SMC API for system power"""
        # Note: SMC API may require special permissions even with sudo
        # For now, we'll try to initialize it but won't fail if it doesn't work
        # IOReport should provide CPU/GPU/ANE power, and SMC is mainly for system total power
        try:
            try:
                from yamon.collectors.smc import SMC
            except ImportError:
                from collectors.smc import SMC
            self._smc = SMC(debug=self._debug)
            # Check if connection was actually established
            if not self._smc._conn:
                pass
        except Exception as e:
            self._smc = None
    
    def _init_ioreport(self):
        """Initialize IOReport API for power metrics (no sudo required)"""
        try:
            try:
                from yamon.collectors.ioreport import IOReport, IOReportError
            except ImportError:
                from collectors.ioreport import IOReport, IOReportError
            
            self._ioreport = IOReport(debug=self._debug)
            # Create subscription for Energy Model channels
            channels = [
                ("Energy Model", None),  # CPU/GPU/ANE power
            ]
            self._ioreport.create_subscription(channels)
            self._ioreport_available = True
        except IOReportError as e:
            self._ioreport = None
            self._ioreport_available = False
        except Exception as e:
            self._ioreport = None
            self._ioreport_available = False
    
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
        """Collect Apple Silicon metrics using IOReport API (preferred, no sudo) or powermetrics (fallback, requires sudo)"""
        if not self._is_apple_silicon:
            return None
        
        # Try IOReport API first (no sudo required)
        ioreport_result = None
        if self._ioreport_available and self._ioreport:
            ioreport_result = self._collect_via_ioreport()
            # If IOReport returns something but power is all zero, try fallback
            def _has_power(m: AppleMetrics) -> bool:
                return any([
                    (m.cpu_power or 0) > 0,
                    (m.gpu_power or 0) > 0,
                    (m.ane_power or 0) > 0,
                    (m.dram_power or 0) > 0,
                ])
            if ioreport_result is not None and _has_power(ioreport_result):
                # IOReport successfully got power data, but it doesn't provide GPU/ANE usage
                # Try to get GPU/ANE usage from powermetrics and merge
                if self._powermetrics_available:
                    powermetrics_result = self._collect_via_powermetrics()
                    if powermetrics_result is not None:
                        # Merge GPU/ANE usage and frequencies from powermetrics into IOReport result
                        # Only merge if powermetrics actually got the data (not None)
                        if powermetrics_result.gpu_usage is not None:
                            ioreport_result.gpu_usage = powermetrics_result.gpu_usage
                        if powermetrics_result.ane_usage is not None:
                            ioreport_result.ane_usage = powermetrics_result.ane_usage
                        if powermetrics_result.gpu_freq_mhz is not None:
                            ioreport_result.gpu_freq_mhz = powermetrics_result.gpu_freq_mhz
                        # Merge CPU frequencies from powermetrics
                        if powermetrics_result.pcpu_freq_mhz is not None:
                            ioreport_result.pcpu_freq_mhz = powermetrics_result.pcpu_freq_mhz
                        if powermetrics_result.ecpu_freq_mhz is not None:
                            ioreport_result.ecpu_freq_mhz = powermetrics_result.ecpu_freq_mhz
                return ioreport_result
            # If no power data, attempt fallback to powermetrics
        
        # Fallback to powermetrics if IOReport not available or produced no data
        # Note: This requires sudo, so it may fail
        if self._powermetrics_available:
            result = self._collect_via_powermetrics()
            # Return empty metrics instead of None so UI can show "N/A"
            return result if result is not None else AppleMetrics()
        
        # Return empty metrics if not available
        return AppleMetrics()
    
    def _collect_via_ioreport(self) -> Optional[AppleMetrics]:
        """Collect metrics using IOReport API (no sudo required)"""
        try:
            if not self._ioreport:
                return None
            
            # Get power metrics quickly (single sample for fastest updates)
            metrics_dict = self._ioreport.get_power_metrics(total_ms=100, samples=1)
            
            metrics = AppleMetrics()
            metrics.cpu_power = metrics_dict.get('cpu_power', 0.0)
            metrics.gpu_power = metrics_dict.get('gpu_power', 0.0)
            metrics.ane_power = metrics_dict.get('ane_power', 0.0)
            metrics.dram_power = metrics_dict.get('dram_power', 0.0)
            # Approximate system power from IOReport (sum or provided)
            sys_power = metrics_dict.get('system_power')
            if sys_power is not None:
                metrics.system_power = sys_power
            
            # Try to get system power via SMC API
            if self._smc:
                smc_power = self._smc.get_system_power()
                if smc_power is not None:
                    metrics.system_power = smc_power
            
            return metrics
            
        except Exception as e:
            return None
    
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
                '--samplers', 'cpu_power,gpu_power,ane_power',  # Note: SMC sampler doesn't exist, system power needs SMC API
                '--show-process-gpu',  # Show per-process GPU time (may help calculate usage)
                '--show-extra-power-info'  # Show additional power info (may include system total)
                # Use default text format - plist parsing is complex
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode != 0:
                # powermetrics requires sudo
                # Check if it's a permission error
                stderr_lower = result.stderr.lower() if result.stderr else ""
                if 'superuser' in stderr_lower or 'sudo' in stderr_lower:
                    # Return empty metrics instead of None so UI can show "N/A"
                    return AppleMetrics()
                return AppleMetrics()  # Return empty instead of None
            
            # Parse text output (more reliable than plist)
            parsed = self._parse_powermetrics_text(result.stdout)
            
            # Try to get GPU usage via ioreg only if powermetrics didn't find it
            if parsed.gpu_usage is None:
                ioreg_usage = self._get_gpu_usage_via_ioreg()
                if ioreg_usage is not None:
                    parsed.gpu_usage = ioreg_usage
            
            # Try to get system power via SMC API
            if parsed.system_power is None and self._smc:
                smc_power = self._smc.get_system_power()
                if smc_power is not None:
                    parsed.system_power = smc_power
            
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
            r'PSTR[:\s]+([\d.]+)\s*(?:mW|W)',  # PSTR is System Power from SMC
            r'Package Power[:\s]+([\d.]+)\s*(?:mW|W)',  # Package power might be system total
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
                    metrics.system_power = None  # Set to None instead of approximate value
                except (ValueError, IndexError):
                    pass
        
        # Try to extract CPU frequencies if available
        # Format: "CPU 0 frequency: 4512 MHz"
        # We need to match both CPU number and frequency to identify P-core vs E-core
        # Method 1: Use cluster information (E-Cluster vs P-Cluster)
        # Method 2: Use CPU number ranges (E-cores typically come first, then P-cores)
        
        # Extract CPU frequencies with their CPU numbers
        cpu_freq_pattern = re.compile(r'CPU\s+(\d+)\s+frequency[:\s]+([\d.]+)\s*MHz', re.IGNORECASE)
        cpu_freq_data = cpu_freq_pattern.findall(text)
        
        if cpu_freq_data:
            try:
                # Parse CPU numbers and frequencies
                cpu_freqs = [(int(cpu_num), float(freq)) for cpu_num, freq in cpu_freq_data]
                cpu_freqs.sort(key=lambda x: x[0])  # Sort by CPU number
                
                if cpu_freqs:
                    # Determine P-core and E-core ranges based on CPU count
                    total_cpus = len(cpu_freqs)
                    cpu_numbers = [cpu_num for cpu_num, _ in cpu_freqs]
                    
                    # Try to identify clusters from text
                    # Method 1: Use position-based matching - find cluster boundaries and assign CPUs based on position
                    e_cluster_match = re.search(r'E-Cluster', text, re.IGNORECASE)
                    p_cluster_match = re.search(r'P\d*-Cluster', text, re.IGNORECASE)
                    
                    e_core_indices = []
                    p_core_indices = []
                    
                    if e_cluster_match and p_cluster_match:
                        # Find the end positions of cluster headers
                        e_cluster_end = e_cluster_match.end()
                        p_cluster_end = p_cluster_match.end()
                        
                        # Assign CPUs to clusters based on their position in text
                        for cpu_num, freq in cpu_freqs:
                            # Find the position of this CPU frequency in the text
                            cpu_match = re.search(rf'CPU\s+{cpu_num}\s+frequency', text, re.IGNORECASE)
                            if cpu_match:
                                cpu_pos = cpu_match.start()
                                # If CPU appears between E-Cluster and P-Cluster, it's an E-core
                                # If CPU appears after P-Cluster, it's a P-core
                                if e_cluster_end < cpu_pos < p_cluster_end:
                                    e_core_indices.append((cpu_num, freq))
                                elif cpu_pos > p_cluster_end:
                                    p_core_indices.append((cpu_num, freq))
                    
                    # Fallback: Use CPU count to estimate P/E core split if clusters not found
                    if not e_core_indices and not p_core_indices:
                        # Common Apple Silicon configurations:
                        # M1/M2/M3: 8 CPUs (4P + 4E) - first 4 are E, last 4 are P
                        # M1 Pro/Max: 10 CPUs (8P + 2E) - first 2 are E, last 8 are P
                        # M2 Pro/Max: 12 CPUs (8P + 4E) - first 4 are E, last 8 are P
                        # M3 Pro: 12 CPUs (6P + 6E) - first 6 are E, last 6 are P (ambiguous!)
                        # M3 Max: 16 CPUs (12P + 4E) - first 4 are E, last 12 are P
                        
                        if total_cpus == 8:
                            e_core_indices = cpu_freqs[:4]
                            p_core_indices = cpu_freqs[4:]
                        elif total_cpus == 10:
                            e_core_indices = cpu_freqs[:2]
                            p_core_indices = cpu_freqs[2:]
                        elif total_cpus == 12:
                            # M2 Pro/Max: 8P + 4E OR M3 Pro: 6P + 6E
                            # Default to M2 Pro/Max configuration (first 4 are E)
                            e_core_indices = cpu_freqs[:4]
                            p_core_indices = cpu_freqs[4:]
                        elif total_cpus == 16:
                            e_core_indices = cpu_freqs[:4]
                            p_core_indices = cpu_freqs[4:]
                        else:
                            # Default: assume first half are E-cores, second half are P-cores
                            mid = total_cpus // 2
                            e_core_indices = cpu_freqs[:mid]
                            p_core_indices = cpu_freqs[mid:]
                    
                    # Extract frequencies
                    if e_core_indices:
                        e_freqs = [freq for _, freq in e_core_indices]
                        metrics.ecpu_freq_mhz = max(e_freqs)  # Use max E-core freq
                    
                    if p_core_indices:
                        p_freqs = [freq for _, freq in p_core_indices]
                        metrics.pcpu_freq_mhz = max(p_freqs)  # Use max P-core freq
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
        # Format: "GPU HW active residency: X.XX%" (preferred, direct value)
        # Or "GPU idle residency: X.XX%" (calculate: 100% - idle)
        # We scale it by frequency to get "performance utilization" like macmon:
        # scaled_usage = (avg_freq × active_residency) / max_freq
        
        # First, try to find GPU HW active residency (preferred, more direct)
        gpu_active_match = re.search(r'GPU HW active residency[:\s]+([\d.]+)\s*%', text, re.IGNORECASE | re.MULTILINE)
        hw_active_residency = None
        if gpu_active_match:
            try:
                hw_active_residency = float(gpu_active_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Extract GPU HW active frequency (average frequency)
        gpu_active_freq_match = re.search(r'GPU HW active frequency[:\s]+([\d.]+)\s*MHz', text, re.IGNORECASE | re.MULTILINE)
        avg_freq_mhz = None
        if gpu_active_freq_match:
            try:
                avg_freq_mhz = float(gpu_active_freq_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Extract max frequency from frequency distribution
        # Format: "GPU HW active residency: X.XX% (338 MHz: 2.0% 618 MHz: 36% ... 1578 MHz: 0%)"
        max_freq_mhz = None
        if hw_active_residency is not None:
            # Extract the GPU usage section to avoid matching CPU frequencies
            gpu_section_match = re.search(r'\*\*\*\* GPU usage \*\*\*\*(.*?)(?=\*\*\*\*|\Z)', text, re.IGNORECASE | re.DOTALL)
            search_text = gpu_section_match.group(1) if gpu_section_match else text
            
            # Try to find all frequencies in the GPU frequency distribution
            # Pattern: "1578 MHz: 0%" or "1578 MHz:  0%"
            freq_matches = re.findall(r'(\d+)\s*MHz[:\s]+[\d.]+%', search_text)
            if freq_matches:
                try:
                    frequencies = [float(f) for f in freq_matches]
                    max_freq_mhz = max(frequencies) if frequencies else None
                except (ValueError, IndexError):
                    pass
            
            # If we still don't have max_freq, try to use current GPU frequency as a proxy
            # (though this might not be the true max, it's better than nothing)
            if max_freq_mhz is None and metrics.gpu_freq_mhz is not None:
                # Use a reasonable multiplier (most GPUs max freq is 2-3x the current freq when idle)
                # Or we could use the current freq if it's already high
                max_freq_mhz = max(metrics.gpu_freq_mhz * 2.5, metrics.gpu_freq_mhz)
        
        # Calculate scaled usage if we have all required values
        if hw_active_residency is not None and avg_freq_mhz is not None and max_freq_mhz is not None and max_freq_mhz > 0:
            # Scale by frequency: (avg_freq × active_residency) / max_freq
            # This gives us "performance utilization" similar to macmon
            scaled_usage = (avg_freq_mhz * hw_active_residency / 100.0) / max_freq_mhz * 100.0
            metrics.gpu_usage = scaled_usage
        elif hw_active_residency is not None:
            # Fallback to raw residency if we don't have frequency info
            metrics.gpu_usage = hw_active_residency
        
        # Fallback: try GPU idle residency and calculate usage
        if metrics.gpu_usage is None:
            gpu_idle_match = re.search(r'GPU idle residency[:\s]+([\d.]+)\s*%', text, re.IGNORECASE | re.MULTILINE)
            if gpu_idle_match:
                try:
                    idle_percent = float(gpu_idle_match.group(1))
                    metrics.gpu_usage = 100.0 - idle_percent
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
                        break
                    except (ValueError, IndexError):
                        continue
        
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
        try:
            # Try to query GPU performance controller
            # This is a best-effort attempt - may not work on all systems
            result = subprocess.run(
                ['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                capture_output=True,
                timeout=2,
                text=True
            )
            
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
                            return usage
                        except (ValueError, IndexError):
                            continue
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # ioreg may not be available or may fail
            pass
        
        return None
    
    def is_available(self) -> bool:
        """Check if Apple API collection is available"""
        return self._is_apple_silicon

