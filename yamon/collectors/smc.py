"""SMC (System Management Controller) API bindings for macOS
Corrected implementation matching macmon / AppleSMC.h structures.
"""

import ctypes
import ctypes.util
import struct
import sys

# --- Structures ---

class KeyDataVer(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint8),
        ("minor", ctypes.c_uint8),
        ("build", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
        ("release", ctypes.c_uint16),
    ]

class PLimitData(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint16),
        ("length", ctypes.c_uint16),
        ("cpu_p_limit", ctypes.c_uint32),
        ("gpu_p_limit", ctypes.c_uint32),
        ("mem_p_limit", ctypes.c_uint32),
    ]

class KeyInfo(ctypes.Structure):
    _fields_ = [
        ("data_size", ctypes.c_uint32),
        ("data_type", ctypes.c_uint32),
        ("data_attributes", ctypes.c_uint8),
    ]

class KeyData(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_uint32),
        ("vers", KeyDataVer),
        ("p_limit_data", PLimitData),
        ("key_info", KeyInfo),
        ("result", ctypes.c_uint8),
        ("status", ctypes.c_uint8),
        ("data8", ctypes.c_uint8),
        ("data32", ctypes.c_uint32),
        ("bytes", ctypes.c_uint8 * 32),
    ]

class SMC:
    KERNEL_INDEX_SMC = 2
    SMC_CMD_READ_BYTES = 5
    SMC_CMD_READ_KEY_INFO = 9

    def __init__(self, debug=False):
        self._debug = debug
        self._conn = 0
        self._init_iokit()

    def _init_iokit(self):
        try:
            iokit_path = ctypes.util.find_library('IOKit')
            self._io_kit = ctypes.CDLL(iokit_path)
            
            # Signatures
            self._io_kit.IOServiceMatching.argtypes = [ctypes.c_char_p]
            self._io_kit.IOServiceMatching.restype = ctypes.c_void_p
            
            self._io_kit.IOServiceGetMatchingServices.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
            self._io_kit.IOServiceGetMatchingServices.restype = ctypes.c_int
            
            self._io_kit.IOIteratorNext.argtypes = [ctypes.c_uint]
            self._io_kit.IOIteratorNext.restype = ctypes.c_uint
            
            self._io_kit.IOServiceOpen.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
            self._io_kit.IOServiceOpen.restype = ctypes.c_int
            
            self._io_kit.IOServiceClose.argtypes = [ctypes.c_uint]
            self._io_kit.IOServiceClose.restype = ctypes.c_int

            self._io_kit.IOConnectCallStructMethod.argtypes = [
                ctypes.c_uint,      # connection
                ctypes.c_uint,      # selector
                ctypes.c_void_p,    # inputStructure
                ctypes.c_size_t,    # inputStructureSize
                ctypes.c_void_p,    # outputStructure
                ctypes.POINTER(ctypes.c_size_t) # outputStructureSize
            ]
            self._io_kit.IOConnectCallStructMethod.restype = ctypes.c_int
            
            self._open_smc()

        except Exception as e:
            if self._debug: print(f"Init failed: {e}")

    def _open_smc(self):
        matching = self._io_kit.IOServiceMatching(b'AppleSMC')
        iterator = ctypes.c_uint()
        res = self._io_kit.IOServiceGetMatchingServices(0, matching, ctypes.byref(iterator))
        if res != 0: return

        while True:
            service = self._io_kit.IOIteratorNext(iterator)
            if not service: break
            
            conn = ctypes.c_uint()
            
            # Access mach_task_self
            task_port = 0
            try:
                libc = ctypes.CDLL(ctypes.util.find_library('c'))
                task_port = ctypes.c_uint.in_dll(libc, "mach_task_self_").value
            except:
                try: task_port = libc.mach_task_self()
                except: pass
            
            res = self._io_kit.IOServiceOpen(service, task_port, 0, ctypes.byref(conn))
            if res == 0:
                self._conn = conn.value
                if self._debug: print("SMC Connected")
                break
            self._io_kit.IOObjectRelease(service)

    def call_smc(self, input_data):
        if not self._conn: return None
        
        output_data = KeyData()
        output_size = ctypes.c_size_t(ctypes.sizeof(KeyData))
        
        res = self._io_kit.IOConnectCallStructMethod(
            self._conn,
            self.KERNEL_INDEX_SMC,
            ctypes.byref(input_data),
            ctypes.sizeof(KeyData),
            ctypes.byref(output_data),
            ctypes.byref(output_size)
        )
        
        if res != 0:
            if self._debug: print(f"SMC Call Failed: {hex(res)}")
            return None
        
        if output_data.result != 0:
            if self._debug: print(f"SMC Result Error: {output_data.result}")
            return None
            
        return output_data

    def read_key_info(self, key_fourcc):
        k_int = int.from_bytes(key_fourcc.encode(), 'big')
        
        kd = KeyData()
        kd.key = k_int
        kd.data8 = self.SMC_CMD_READ_KEY_INFO
        
        out = self.call_smc(kd)
        if out: return out.key_info
        return None

    def read_key(self, key_str):
        if len(key_str) != 4: return None
        
        info = self.read_key_info(key_str)
        if not info: return None
        
        k_int = int.from_bytes(key_str.encode(), 'big')
        kd = KeyData()
        kd.key = k_int
        kd.key_info = info
        kd.data8 = self.SMC_CMD_READ_BYTES
        
        out = self.call_smc(kd)
        if not out: return None
        
        return bytes(out.bytes)[:info.data_size]

    def get_system_power(self):
        # Read PSTR
        val = self.read_key("PSTR")
        if val:
            # PSTR is usually 4 bytes float (flt) or 2 bytes fixed point (sp78)
            # macmon treats it as f32 if 4 bytes? 
            # macmon: f32::from_le_bytes
            
            # Try Little Endian Float first (like macmon)
            if len(val) == 4:
                return struct.unpack('<f', val)[0]
                
        return None

    def close(self):
        if self._conn:
            self._io_kit.IOServiceClose(self._conn)
            self._conn = 0
    
    def __del__(self):
        self.close()
