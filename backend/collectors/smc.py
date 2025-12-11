"""SMC (System Management Controller) API bindings for macOS

Uses IOKit to access SMC and read system power (PSTR) and other metrics.
Based on AppleSMC implementation patterns.
"""

import ctypes
import ctypes.util
from typing import Optional
import platform


class SMC:
    """SMC API wrapper using ctypes"""
    
    # SMC key codes
    SMC_KEY_PSTR = b'PSTR'  # System Power (watts)
    
    # SMC data types
    SMC_TYPE_FP1E = b'fp1e'  # Float (16-bit)
    SMC_TYPE_FP4C = b'fp4c'  # Float (32-bit)
    SMC_TYPE_SP78 = b'sp78'  # Fixed point (16-bit)
    SMC_TYPE_UINT16 = b'ui16'
    SMC_TYPE_UINT32 = b'ui32'
    
    def __init__(self, debug=False):
        self._debug = debug
        self._is_macos = platform.system() == 'Darwin'
        self._io_kit = None
        self._conn = None
        
        if self._is_macos:
            self._init_iokit()
    
    def _init_iokit(self):
        """Initialize IOKit framework"""
        try:
            iokit_path = ctypes.util.find_library('IOKit')
            if not iokit_path:
                if self._debug:
                    import sys
                    print("[DEBUG] IOKit library not found", file=sys.stderr)
                return
            
            self._io_kit = ctypes.CDLL(iokit_path)
            
            # Define function signatures
            self._io_kit.IOServiceMatching.argtypes = [ctypes.c_char_p]
            self._io_kit.IOServiceMatching.restype = ctypes.c_void_p
            
            self._io_kit.IOServiceGetMatchingService.argtypes = [
                ctypes.c_uint,  # masterPort
                ctypes.c_void_p,  # matching
            ]
            self._io_kit.IOServiceGetMatchingService.restype = ctypes.c_uint
            
            self._io_kit.IOServiceOpen.argtypes = [
                ctypes.c_uint,  # service
                ctypes.c_uint,  # owningTask
                ctypes.c_uint,  # type
                ctypes.POINTER(ctypes.c_uint),  # connect
            ]
            self._io_kit.IOServiceOpen.restype = ctypes.c_uint
            
            self._io_kit.IOConnectCallStructMethod.argtypes = [
                ctypes.c_uint,  # connection
                ctypes.c_uint,  # selector
                ctypes.c_void_p,  # inputStruct
                ctypes.c_size_t,  # inputStructSize
                ctypes.c_void_p,  # outputStruct
                ctypes.POINTER(ctypes.c_size_t),  # outputStructSize
            ]
            self._io_kit.IOConnectCallStructMethod.restype = ctypes.c_uint
            
            self._io_kit.IOServiceClose.argtypes = [ctypes.c_uint]
            self._io_kit.IOServiceClose.restype = ctypes.c_uint
            
            # Constants
            self._kIOMasterPortDefault = 0
            self._kIOServiceOpen = 0
            
            # Open SMC connection
            self._open_smc()
            
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to initialize IOKit: {e}", file=sys.stderr)
            self._io_kit = None
    
    def _open_smc(self):
        """Open connection to AppleSMC service"""
        if not self._io_kit:
            return False
        
        try:
            # Get matching dictionary for AppleSMC
            matching = self._io_kit.IOServiceMatching(b'AppleSMC')
            if not matching:
                return False
            
            # Get the service
            service = self._io_kit.IOServiceGetMatchingService(
                self._kIOMasterPortDefault,
                matching
            )
            
            if service == 0:
                return False
            
            # Open connection
            conn = ctypes.c_uint()
            result = self._io_kit.IOServiceOpen(
                service,
                0,  # self task
                self._kIOServiceOpen,
                ctypes.byref(conn)
            )
            
            if result == 0:  # KERN_SUCCESS
                self._conn = conn.value
                return True
            
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to open SMC: {e}", file=sys.stderr)
        
        return False
    
    def read_key(self, key: bytes) -> Optional[float]:
        """Read a value from SMC by key"""
        if not self._conn or not self._io_kit:
            return None
        
        try:
            # SMC key structure (simplified)
            # This is a simplified implementation
            # Full implementation would need proper SMC structures
            
            # For now, try using subprocess to call smc command if available
            # Or use a Python SMC library if installed
            return None
            
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to read SMC key {key}: {e}", file=sys.stderr)
            return None
    
    def get_system_power(self) -> Optional[float]:
        """Get system total power (PSTR) in watts"""
        # Try using subprocess to call smc command-line tool if available
        # Or use py-smc2 library if installed
        try:
            # Try py-smc2 if available
            try:
                import smc
                pstr = smc.read_key('PSTR')
                if pstr:
                    # PSTR is typically in fixed-point format
                    # Convert based on data type
                    return float(pstr) / 1000.0  # Convert to watts if needed
            except ImportError:
                pass
            
            # Try smc command-line tool
            import subprocess
            result = subprocess.run(
                ['smc', '-k', 'PSTR', '-r'],
                capture_output=True,
                timeout=2,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                # Parse output (format may vary)
                value = float(result.stdout.strip())
                return value / 1000.0  # Convert to watts if needed
            
        except (FileNotFoundError, ValueError, subprocess.TimeoutExpired) as e:
            if self._debug:
                import sys
                print(f"[DEBUG] SMC read failed: {e}", file=sys.stderr)
        
        return None
    
    def close(self):
        """Close SMC connection"""
        if self._conn and self._io_kit:
            try:
                self._io_kit.IOServiceClose(self._conn)
            except Exception:
                pass
            self._conn = None
    
    def __del__(self):
        self.close()

