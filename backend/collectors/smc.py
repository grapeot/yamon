"""SMC (System Management Controller) API bindings for macOS

Uses IOKit to access SMC and read system power (PSTR) and other metrics.
Based on AppleSMC implementation patterns.
"""

import ctypes
import ctypes.util
from typing import Optional
import platform
import struct


class SMCKeyData_t(ctypes.Structure):
    """SMC key data structure"""
    _fields_ = [
        ('key', ctypes.c_uint32),
        ('dataSize', ctypes.c_uint8),
        ('dataType', ctypes.c_uint8),
        ('dataAttributes', ctypes.c_uint8),
        ('data', ctypes.c_uint8 * 32),
        ('padding', ctypes.c_uint8 * 2),
    ]


class SMCVal(ctypes.Structure):
    """SMC value structure"""
    _fields_ = [
        ('key', ctypes.c_char * 5),
        ('dataSize', ctypes.c_uint32),
        ('dataType', ctypes.c_char * 5),
        ('bytes', ctypes.c_uint8 * 32),
    ]


class SMC:
    """SMC API wrapper using ctypes"""
    
    # SMC key codes
    SMC_KEY_PSTR = b'PSTR'  # System Power (watts)
    
    # SMC selectors
    KERNEL_INDEX_SMC = 2
    SMC_CMD_READ_KEYINFO = 9
    SMC_CMD_READ_BYTES = 5
    SMC_CMD_READ_INDEX = 8
    
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
                if self._debug:
                    import sys
                    print("[DEBUG] Failed to get AppleSMC matching dictionary", file=sys.stderr)
                return False
            
            # Get the service
            service = self._io_kit.IOServiceGetMatchingService(
                self._kIOMasterPortDefault,
                matching
            )
            
            if service == 0:
                if self._debug:
                    import sys
                    print("[DEBUG] Failed to get AppleSMC service", file=sys.stderr)
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
                if self._debug:
                    import sys
                    print(f"[DEBUG] Successfully opened SMC connection: {self._conn}", file=sys.stderr)
                return True
            else:
                if self._debug:
                    import sys
                    # Common error codes:
                    # 0xE00002C2 = kIOReturnNotPrivileged (requires root)
                    # 0xE00002C1 = kIOReturnBadArgument
                    error_hex = hex(result)
                    if result == 0xE00002C2:
                        print(f"[DEBUG] SMC connection failed: Not privileged (requires sudo), error: {error_hex}", file=sys.stderr)
                    else:
                        print(f"[DEBUG] Failed to open SMC connection, result: {result} ({error_hex})", file=sys.stderr)
        
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to open SMC: {e}", file=sys.stderr)
        
        return False
    
    def _str_to_key(self, key_str: str) -> int:
        """Convert string key to integer"""
        key_bytes = key_str.encode('ascii')
        if len(key_bytes) != 4:
            raise ValueError(f"Key must be 4 characters: {key_str}")
        return struct.unpack('>I', key_bytes)[0]
    
    def read_key(self, key_str: str) -> Optional[float]:
        """Read a value from SMC by key string (e.g., 'PSTR')"""
        if not self._conn or not self._io_kit:
            return None
        
        try:
            # Convert key string to integer
            key = self._str_to_key(key_str)
            
            # Prepare input structure
            input_data = SMCKeyData_t()
            input_data.key = key
            input_data.dataSize = 0
            input_data.dataType = 0
            input_data.dataAttributes = 0
            
            # Prepare output structure
            output_data = SMCKeyData_t()
            output_size = ctypes.c_size_t(ctypes.sizeof(SMCKeyData_t))
            
            # Call SMC to read key info first
            result = self._io_kit.IOConnectCallStructMethod(
                self._conn,
                self.SMC_CMD_READ_KEYINFO,
                ctypes.byref(input_data),
                ctypes.sizeof(SMCKeyData_t),
                ctypes.byref(output_data),
                ctypes.byref(output_size)
            )
            
            if result != 0:
                if self._debug:
                    import sys
                    print(f"[DEBUG] Failed to read key info for {key_str}, result: {result}", file=sys.stderr)
                return None
            
            # Now read the actual data
            input_data.dataSize = output_data.dataSize
            input_data.dataType = output_data.dataType
            
            result = self._io_kit.IOConnectCallStructMethod(
                self._conn,
                self.SMC_CMD_READ_BYTES,
                ctypes.byref(input_data),
                ctypes.sizeof(SMCKeyData_t),
                ctypes.byref(output_data),
                ctypes.byref(output_size)
            )
            
            if result != 0:
                if self._debug:
                    import sys
                    print(f"[DEBUG] Failed to read bytes for {key_str}, result: {result}", file=sys.stderr)
                return None
            
            # Parse the data based on data type
            data_bytes = bytes(output_data.data[:output_data.dataSize])
            
            # PSTR is typically sp78 format (16-bit fixed point)
            if output_data.dataType == ord('s') and output_data.dataSize >= 2:
                # sp78: signed 16-bit fixed point, 7 integer bits, 8 fractional bits
                value = struct.unpack('>h', data_bytes[:2])[0]
                return value / 256.0  # Divide by 256 to get float
            elif output_data.dataSize == 2:
                # Try as unsigned 16-bit
                value = struct.unpack('>H', data_bytes[:2])[0]
                return value / 1000.0  # Convert to watts
            elif output_data.dataSize == 4:
                # Try as float or uint32
                try:
                    value = struct.unpack('>f', data_bytes[:4])[0]
                    return value
                except:
                    value = struct.unpack('>I', data_bytes[:4])[0]
                    return value / 1000.0
            
            if self._debug:
                import sys
                print(f"[DEBUG] Unknown data type for {key_str}: type={output_data.dataType}, size={output_data.dataSize}", file=sys.stderr)
            
            return None
            
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to read SMC key {key_str}: {e}", file=sys.stderr)
            return None
    
    def get_system_power(self) -> Optional[float]:
        """Get system total power (PSTR) in watts"""
        if not self._conn:
            return None
        
        try:
            power = self.read_key('PSTR')
            if power is not None and power > 0:
                if self._debug:
                    import sys
                    print(f"[DEBUG] Got PSTR from SMC: {power}W", file=sys.stderr)
                return power
        except Exception as e:
            if self._debug:
                import sys
                print(f"[DEBUG] Failed to get system power: {e}", file=sys.stderr)
        
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
