"""Isolated actual reader timing/RAM measurement, no semantic execution credit."""
import ctypes,hashlib,json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path[:0]=[str(H),str(R/'tools/m4-pipeline'),str(R/'tools/m4-crt-allocation-root')]
from capture_bundle import sha_file
from capture_shared_v3 import SharedDirectSet
from run_v2 import DirectSet
class PMC(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
def memory():
    p=PMC();p.cb=ctypes.sizeof(p);k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;api=ctypes.WinDLL('psapi',use_last_error=True);api.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong]
    if not api.GetProcessMemoryInfo(k.GetCurrentProcess(),ctypes.byref(p),p.cb):raise ctypes.WinError(ctypes.get_last_error())
    return {'peak_working_set_bytes':p.PeakWorkingSetSize,'working_set_bytes':p.WorkingSetSize,'peak_pagefile_bytes':p.PeakPagefileUsage}
def main(kind,manifest):
    path=Path(manifest).resolve();pin=sha_file(path);baseline=memory();start=time.perf_counter_ns()
    def pinned(p,expected=None):
        p=Path(p);digest=sha_file(p)
        if expected is not None and digest!=expected:raise ValueError('Actual canonical reader pin')
        return p
    if kind=='shared':owner=SharedDirectSet(path,pin)
    elif kind=='canonical':owner=DirectSet(path,pinned)
    else:raise ValueError('Explicit known reader required')
    opened=time.perf_counter_ns();names=tuple(owner.entries);mem=memory();checksum=0;access=time.perf_counter_ns()
    for _ in range(3):
        for name in names:
            data=owner.data(name);checksum+=len(data)+(data[0] if data else 0)+(data[-1] if data else 0)
    ended=time.perf_counter_ns();final=memory();counts={}
    if kind=='shared':counts={'authenticated_unique_blobs':sum(r.authenticated_blobs for r in owner.readers),'authenticated_unique_blob_bytes':sum(r.authenticated_blob_bytes for r in owner.readers)}
    owner.close()
    print(json.dumps({'passed':True,'reader':kind,'manifest_sha256':pin,'startup_seconds':(opened-start)/1e9,'steady_access_seconds':(ended-access)/1e9,'access_passes':3,'logical_records':len(names),'checksum':checksum,'before':baseline,'after_open':mem,'after_access':final,'authentication':counts,'game_executed':False,'cold_OS_cache_claimed':False}))
if __name__=='__main__':main(*sys.argv[1:])
