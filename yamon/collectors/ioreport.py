"""IOReport API bindings for macOS

Uses IOReport framework to access CPU, GPU, ANE, and DRAM power consumption
without requiring sudo privileges.

Based on macmon's implementation: https://github.com/vladkens/macmon
"""

import ctypes
import ctypes.util
from typing import Optional, List, Tuple, Dict
import platform
import time


# Core Foundation types
CFAllocatorRef = ctypes.c_void_p
CFTypeRef = ctypes.c_void_p
CFStringRef = ctypes.c_void_p
CFDictionaryRef = ctypes.c_void_p
CFMutableDictionaryRef = ctypes.c_void_p
CFArrayRef = ctypes.c_void_p
CFDataRef = ctypes.c_void_p

# Constants
kCFAllocatorDefault = None
kCFAllocatorNull = None


class IOReportError(Exception):
    """IOReport API error"""
    pass


class IOReport:
    """IOReport API wrapper using ctypes"""
    
    def __init__(self, debug=False):
        self._debug = debug
        self._is_macos = platform.system() == 'Darwin'
        self._core_foundation = None
        self._ioreport = None
        self._iokit = None
        self._subscription = None
        self._channels = None
        
        if self._is_macos:
            self._init_frameworks()
    
    def _init_frameworks(self):
        """Initialize Core Foundation and IOReport frameworks"""
        try:
            # Load Core Foundation
            cf_path = ctypes.util.find_library('CoreFoundation')
            if not cf_path:
                raise IOReportError("CoreFoundation framework not found")
            
            self._core_foundation = ctypes.CDLL(cf_path)
            
            # Load IOReport (dynamic library)
            ioreport_path = ctypes.util.find_library('IOReport')
            if not ioreport_path:
                raise IOReportError("IOReport library not found")
            
            self._ioreport = ctypes.CDLL(ioreport_path)
            
            # Load IOKit
            iokit_path = ctypes.util.find_library('IOKit')
            if not iokit_path:
                raise IOReportError("IOKit framework not found")
            
            self._iokit = ctypes.CDLL(iokit_path)
            
            # Define Core Foundation function signatures
            self._init_core_foundation()
            
            # Define IOReport function signatures
            self._init_ioreport()
            
        except Exception as e:
            raise IOReportError(f"Failed to initialize IOReport: {e}")
    
    def _init_core_foundation(self):
        """Initialize Core Foundation function signatures"""
        # CFStringCreateWithBytesNoCopy
        self._core_foundation.CFStringCreateWithBytesNoCopy.argtypes = [
            CFAllocatorRef, ctypes.POINTER(ctypes.c_uint8), ctypes.c_long,
            ctypes.c_uint32, ctypes.c_uint8, CFAllocatorRef
        ]
        self._core_foundation.CFStringCreateWithBytesNoCopy.restype = CFStringRef
        
        # CFStringCreateWithBytes (makes an internal copy; safer for alignment)
        self._core_foundation.CFStringCreateWithBytes.argtypes = [
            CFAllocatorRef, ctypes.POINTER(ctypes.c_uint8), ctypes.c_long,
            ctypes.c_uint32, ctypes.c_uint8
        ]
        self._core_foundation.CFStringCreateWithBytes.restype = CFStringRef
        
        # CFStringGetCString
        self._core_foundation.CFStringGetCString.argtypes = [
            CFStringRef, ctypes.POINTER(ctypes.c_char), ctypes.c_long, ctypes.c_uint32
        ]
        self._core_foundation.CFStringGetCString.restype = ctypes.c_int
        
        # CFDictionaryGetCount
        self._core_foundation.CFDictionaryGetCount.argtypes = [CFDictionaryRef]
        self._core_foundation.CFDictionaryGetCount.restype = ctypes.c_long
        
        # CFDictionaryGetValue
        self._core_foundation.CFDictionaryGetValue.argtypes = [CFDictionaryRef, ctypes.c_void_p]
        self._core_foundation.CFDictionaryGetValue.restype = CFTypeRef
        
        # CFDictionaryCreateMutableCopy
        self._core_foundation.CFDictionaryCreateMutableCopy.argtypes = [
            CFAllocatorRef, ctypes.c_long, CFDictionaryRef
        ]
        self._core_foundation.CFDictionaryCreateMutableCopy.restype = CFMutableDictionaryRef
        
        # CFRelease
        self._core_foundation.CFRelease.argtypes = [CFTypeRef]
        self._core_foundation.CFRelease.restype = None
        
        # CFArrayGetCount
        self._core_foundation.CFArrayGetCount.argtypes = [CFArrayRef]
        self._core_foundation.CFArrayGetCount.restype = ctypes.c_long
        
        # CFArrayGetValueAtIndex
        self._core_foundation.CFArrayGetValueAtIndex.argtypes = [CFArrayRef, ctypes.c_long]
        self._core_foundation.CFArrayGetValueAtIndex.restype = CFTypeRef
    
    def _init_ioreport(self):
        """Initialize IOReport function signatures"""
        # IOReportCopyAllChannels
        self._ioreport.IOReportCopyAllChannels.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
        self._ioreport.IOReportCopyAllChannels.restype = CFDictionaryRef
        
        # IOReportCopyChannelsInGroup
        self._ioreport.IOReportCopyChannelsInGroup.argtypes = [
            CFStringRef, CFStringRef, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64
        ]
        self._ioreport.IOReportCopyChannelsInGroup.restype = CFDictionaryRef
        
        # IOReportMergeChannels
        self._ioreport.IOReportMergeChannels.argtypes = [
            CFDictionaryRef, CFDictionaryRef, CFTypeRef
        ]
        self._ioreport.IOReportMergeChannels.restype = None
        
        # IOReportCreateSubscription
        # Signature: IOReportCreateSubscription(void* refcon,
        #                                      CFMutableDictionaryRef channels,
        #                                      CFMutableDictionaryRef* subscription_details,
        #                                      uint64_t options,
        #                                      CFTypeRef allocator) -> IOReportSubscriptionRef
        self._ioreport.IOReportCreateSubscription.argtypes = [
            ctypes.c_void_p,             # refcon
            CFMutableDictionaryRef,      # channels
            ctypes.POINTER(CFMutableDictionaryRef),  # subscription_details (out)
            ctypes.c_uint64,             # options
            CFTypeRef,                   # allocator
        ]
        self._ioreport.IOReportCreateSubscription.restype = ctypes.c_void_p
        
        # IOReportCreateSamples
        self._ioreport.IOReportCreateSamples.argtypes = [
            ctypes.c_void_p, CFMutableDictionaryRef, CFTypeRef
        ]
        self._ioreport.IOReportCreateSamples.restype = CFDictionaryRef
        
        # IOReportCreateSamplesDelta
        self._ioreport.IOReportCreateSamplesDelta.argtypes = [
            CFDictionaryRef, CFDictionaryRef, CFTypeRef
        ]
        self._ioreport.IOReportCreateSamplesDelta.restype = CFDictionaryRef
        
        # IOReportChannelGetGroup
        self._ioreport.IOReportChannelGetGroup.argtypes = [CFDictionaryRef]
        self._ioreport.IOReportChannelGetGroup.restype = CFStringRef
        
        # IOReportChannelGetSubGroup
        self._ioreport.IOReportChannelGetSubGroup.argtypes = [CFDictionaryRef]
        self._ioreport.IOReportChannelGetSubGroup.restype = CFStringRef
        
        # IOReportChannelGetChannelName
        self._ioreport.IOReportChannelGetChannelName.argtypes = [CFDictionaryRef]
        self._ioreport.IOReportChannelGetChannelName.restype = CFStringRef
        
        # IOReportChannelGetUnitLabel
        self._ioreport.IOReportChannelGetUnitLabel.argtypes = [CFDictionaryRef]
        self._ioreport.IOReportChannelGetUnitLabel.restype = CFStringRef
        
        # IOReportSimpleGetIntegerValue
        self._ioreport.IOReportSimpleGetIntegerValue.argtypes = [CFDictionaryRef, ctypes.c_int32]
        self._ioreport.IOReportSimpleGetIntegerValue.restype = ctypes.c_int64
        
        # IOReportStateGetCount
        self._ioreport.IOReportStateGetCount.argtypes = [CFDictionaryRef]
        self._ioreport.IOReportStateGetCount.restype = ctypes.c_int32
        
        # IOReportStateGetNameForIndex
        self._ioreport.IOReportStateGetNameForIndex.argtypes = [CFDictionaryRef, ctypes.c_int32]
        self._ioreport.IOReportStateGetNameForIndex.restype = CFStringRef
        
        # IOReportStateGetResidency
        self._ioreport.IOReportStateGetResidency.argtypes = [CFDictionaryRef, ctypes.c_int32]
        self._ioreport.IOReportStateGetResidency.restype = ctypes.c_int64
    
    def _cf_string_from_str(self, s: str) -> CFStringRef:
        """Create CFString from Python string (copying into CF-managed buffer)"""
        if not s:
            return None
        
        bytes_data = s.encode('utf-8')
        return self._core_foundation.CFStringCreateWithBytes(
            kCFAllocatorDefault,
            (ctypes.c_uint8 * len(bytes_data))(*bytes_data),
            len(bytes_data),
            0x08000100,  # kCFStringEncodingUTF8
            0,
        )
    
    def _cf_string_to_str(self, cf_str: CFStringRef) -> str:
        """Convert CFString to Python string"""
        if not cf_str:
            return ""
        
        buf = ctypes.create_string_buffer(256)
        if self._core_foundation.CFStringGetCString(cf_str, buf, 256, 0x08000100):
            return buf.value.decode('utf-8')
        return ""
    
    def create_subscription(self, channels: List[Tuple[str, Optional[str]]]) -> None:
        """Create IOReport subscription for specified channels"""
        if not self._ioreport:
            raise IOReportError("IOReport not initialized")
        
        # Get channels dictionary
        if not channels:
            # Get all channels
            all_channels = self._ioreport.IOReportCopyAllChannels(0, 0)
            if not all_channels:
                raise IOReportError("Failed to copy all channels")
            
            count = self._core_foundation.CFDictionaryGetCount(all_channels)
            self._channels = self._core_foundation.CFDictionaryCreateMutableCopy(
                kCFAllocatorDefault, count, all_channels
            )
            self._core_foundation.CFRelease(all_channels)
        else:
            # Get specific channels
            channel_dicts = []
            for group, subgroup in channels:
                group_str = self._cf_string_from_str(group)
                subgroup_str = self._cf_string_from_str(subgroup) if subgroup else None
                
                chan = self._ioreport.IOReportCopyChannelsInGroup(
                    group_str, subgroup_str, 0, 0, 0
                )
                if chan:
                    channel_dicts.append(chan)
                
                # Release CFStrings (they're temporary)
                if group_str:
                    self._core_foundation.CFRelease(group_str)
                if subgroup_str:
                    self._core_foundation.CFRelease(subgroup_str)
            
            if not channel_dicts:
                raise IOReportError("Failed to get any channels")
            
            # Merge channels
            self._channels = channel_dicts[0]
            for i in range(1, len(channel_dicts)):
                self._ioreport.IOReportMergeChannels(self._channels, channel_dicts[i], None)
                self._core_foundation.CFRelease(channel_dicts[i])
            
            count = self._core_foundation.CFDictionaryGetCount(self._channels)
            self._channels = self._core_foundation.CFDictionaryCreateMutableCopy(
                kCFAllocatorDefault, count, self._channels
            )
        
        # Create subscription
        sub_details = CFMutableDictionaryRef()
        self._subscription = self._ioreport.IOReportCreateSubscription(
            None,
            self._channels,
            ctypes.byref(sub_details),
            0,
            None
        )
        
        if not self._subscription:
            raise IOReportError("Failed to create IOReport subscription")
    
    def get_power_metrics(self, total_ms: int = 1000, samples: int = 4) -> Dict:
        """
        Get smoothed power metrics over total_ms by taking multiple deltas.
        Mirrors macmon's approach: multiple samples -> average power.
        """
        if not self._subscription:
            raise IOReportError("Subscription not created")
        
        samples = max(1, samples)
        # For single sample, use minimal wait time for faster collection
        if samples == 1:
            step_ms = 10  # 10ms minimum wait for delta calculation
        else:
            step_ms = max(1, total_ms // samples)
        
        # Initial sample
        prev_sample = self._ioreport.IOReportCreateSamples(
            self._subscription, self._channels, None
        )
        prev_time = time.time()
        
        acc = {
            'cpu_power': 0.0,
            'gpu_power': 0.0,
            'ane_power': 0.0,
            'dram_power': 0.0,
            'gpu_sram_power': 0.0,
            'system_power': 0.0,
        }
        
        for _ in range(samples):
            time.sleep(step_ms / 1000.0)
            cur_sample = self._ioreport.IOReportCreateSamples(
                self._subscription, self._channels, None
            )
            elapsed_ms = max(1, int((time.time() - prev_time) * 1000))
            
            delta = self._ioreport.IOReportCreateSamplesDelta(prev_sample, cur_sample, None)
            metrics = self._parse_sample(delta, elapsed_ms)
            
            for k in acc:
                acc[k] += metrics.get(k, 0.0)
            
            # release
            self._core_foundation.CFRelease(prev_sample)
            self._core_foundation.CFRelease(delta)
            
            prev_sample = cur_sample
            prev_time = time.time()
        
        # release last sample
        self._core_foundation.CFRelease(prev_sample)
        
        # average
        for k in acc:
            acc[k] /= samples
        
        return acc
    
    def _parse_sample(self, sample: CFDictionaryRef, duration_ms: int) -> Dict:
        """Parse IOReport sample to extract power metrics"""
        metrics = {
            'cpu_power': 0.0,
            'gpu_power': 0.0,
            'ane_power': 0.0,
            'dram_power': 0.0,
            'gpu_sram_power': 0.0,
            'system_power': 0.0,
        }
        
        # Get IOReportChannels array
        channels_key = self._cf_string_from_str("IOReportChannels")
        channels_array = self._core_foundation.CFDictionaryGetValue(sample, channels_key)
        self._core_foundation.CFRelease(channels_key)
        
        if not channels_array:
            return metrics
        
        # Iterate through channels
        count = self._core_foundation.CFArrayGetCount(channels_array)
        for i in range(count):
            channel = self._core_foundation.CFArrayGetValueAtIndex(channels_array, i)
            if not channel:
                continue
            
            # Get channel info
            group = self._cf_string_to_str(
                self._ioreport.IOReportChannelGetGroup(channel)
            )
            subgroup = self._cf_string_to_str(
                self._ioreport.IOReportChannelGetSubGroup(channel)
            )
            channel_name = self._cf_string_to_str(
                self._ioreport.IOReportChannelGetChannelName(channel)
            )
            unit = self._cf_string_to_str(
                self._ioreport.IOReportChannelGetUnitLabel(channel)
            ).strip()
            
            # Parse Energy Model channels
            if group == "Energy Model":
                value = self._ioreport.IOReportSimpleGetIntegerValue(channel, 0)
                watts = self._convert_to_watts(value, unit, duration_ms)
                
                if "CPU Energy" in channel_name or channel_name.endswith("CPU Energy"):
                    metrics['cpu_power'] += watts
                elif channel_name.startswith("GPU Energy") or channel_name == "GPU Energy":
                    metrics['gpu_power'] += watts
                elif channel_name.startswith("ANE") or "ANE Energy" in channel_name:
                    metrics['ane_power'] += watts
                elif channel_name.startswith("DRAM"):
                    metrics['dram_power'] += watts
                elif channel_name.startswith("GPU SRAM"):
                    metrics['gpu_sram_power'] += watts
                elif "System" in channel_name or "Total" in channel_name or "All" in channel_name:
                    # Some systems expose total/soc power channel
                    metrics['system_power'] += watts
        
        # If system_power not provided, approximate as sum of components
        if metrics['system_power'] <= 0.0:
            metrics['system_power'] = metrics['cpu_power'] + metrics['gpu_power'] + metrics['ane_power'] + metrics['dram_power'] + metrics['gpu_sram_power']
        
        return metrics
    
    def _convert_to_watts(self, value: int, unit: str, duration_ms: int) -> float:
        """Convert energy value to watts"""
        if duration_ms == 0:
            return 0.0
        
        # Convert energy to joules, then to watts
        joules = value / (duration_ms / 1000.0)
        
        if unit == "mJ":
            joules = joules / 1000.0
        elif unit == "uJ":
            joules = joules / 1000000.0
        elif unit == "nJ":
            joules = joules / 1000000000.0
        
        return joules
    
    def close(self):
        """Clean up resources"""
        if self._channels:
            self._core_foundation.CFRelease(self._channels)
            self._channels = None
        
        if self._subscription:
            # Note: IOReport subscription cleanup may need special handling
            # For now, we'll rely on Python's garbage collection
            self._subscription = None
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup

