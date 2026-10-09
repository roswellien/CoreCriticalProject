"""Debugger observations of the preserved own-worker longjmp failfast only."""
import ctypes as c,ctypes.wintypes as w,hashlib,json,pathlib,subprocess,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
class Startup(c.Structure):_fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),('x',w.DWORD),('y',w.DWORD),('xs',w.DWORD),('ys',w.DWORD),('xc',w.DWORD),('yc',w.DWORD),('fill',w.DWORD),('flags',w.DWORD),('show',w.WORD),('reserved2',w.WORD),('ptr2',c.c_void_p),('hin',w.HANDLE),('hout',w.HANDLE),('herr',w.HANDLE)]
class Process(c.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
class Event(c.Structure):_fields_=[('code',w.DWORD),('pid',w.DWORD),('tid',w.DWORD),('pad',w.DWORD),('payload',c.c_ubyte*160)]
k=c.WinDLL('kernel32',use_last_error=True);k.CreateProcessW.argtypes=[w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.POINTER(Startup),c.POINTER(Process)];k.CreateProcessW.restype=w.BOOL;k.WaitForDebugEvent.argtypes=[c.POINTER(Event),w.DWORD];k.WaitForDebugEvent.restype=w.BOOL;k.ContinueDebugEvent.argtypes=[w.DWORD,w.DWORD,w.DWORD];k.CloseHandle.argtypes=[w.HANDLE];k.TerminateProcess.argtypes=[w.HANDLE,w.UINT]
def main(out):
 import struct
 out=pathlib.Path(out);assert not out.exists();out.mkdir();exe=ROOT/'build/m4-cmd-controls-compiled-controls-r2-O0/commandline_controls.exe';args=[str(exe),str(ROOT/'MW3/Mech3.exe'),str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),str(ROOT/'reports/m4-crt-commandline-native/static-r1/pack.bin')];si=Startup();si.cb=c.sizeof(si);pi=Process();rows=[];exited=False;created=False
 try:
  assert k.CreateProcessW(str(exe),c.create_unicode_buffer(subprocess.list2cmdline(args)),None,None,False,2|0x08000000,None,str(ROOT),c.byref(si),c.byref(pi)),c.get_last_error();created=True;deadline=time.monotonic()+30
  while time.monotonic()<deadline:
   e=Event()
   if not k.WaitForDebugEvent(c.byref(e),1000):continue
   raw=bytes(e.payload);status=0x10002
   if e.code==1:
    code,flags=struct.unpack_from('<2I',raw);address=struct.unpack_from('<Q',raw,16)[0];n=struct.unpack_from('<I',raw,24)[0];first=struct.unpack_from('<I',raw,152)[0];params=struct.unpack_from('<'+'Q'*min(n,15),raw,32);rows.append(dict(exception_code=f'{code:08x}',flags=flags,address=address,first_chance=first,parameters=params));status=0x10002 if code==0x80000003 else 0x80010001
   elif e.code in(3,6):
    h=struct.unpack_from('<Q',raw)[0]
    if h:k.CloseHandle(h)
   elif e.code==5:rows.append(dict(process_exit=struct.unpack_from('<I',raw)[0]));exited=True
   assert k.ContinueDebugEvent(e.pid,e.tid,status)
   if exited:break
  assert exited,'Diagnostic deadline'
 finally:
  if created and not exited:k.TerminateProcess(pi.process,1)
  if pi.thread:k.CloseHandle(pi.thread)
  if pi.process:k.CloseHandle(pi.process)
  (out/'report.json').write_text(json.dumps(dict(exited=exited,worker=str(exe),worker_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),observations=rows,scope='Preserved failed authored worker only; no repaired/original-provider equivalence',script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),indent=2))
if __name__=='__main__':main(sys.argv[1])
