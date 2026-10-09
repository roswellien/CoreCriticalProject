"""Read-only actual loaded allocation export/forwarder diagnosis; no heap calls."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from paths import publish_bytes,workspace_path


def export(path,name):
    raw=path.read_bytes();u16=lambda p:struct.unpack_from('<H',raw,p)[0];u32=lambda p:struct.unpack_from('<I',raw,p)[0]
    pe=u32(60);opt=pe+24;directory=opt+(112 if u16(opt)==0x20b else 96)
    erva,esize=u32(directory),u32(directory+4)
    sections=[opt+u16(pe+20)+40*i for i in range(u16(pe+6))]
    def offset(rva):
        matches=[u32(s+20)+rva-u32(s+12) for s in sections if u32(s+12)<=rva<u32(s+12)+u32(s+16)]
        if len(matches)!=1:raise ValueError('Unique raw export RVA')
        return matches[0]
    def text(rva):
        p=offset(rva);return raw[p:raw.index(b'\0',p)].decode('ascii')
    e=offset(erva);functions,names,ordinals=u32(e+28),u32(e+32),u32(e+36)
    for i in range(u32(e+24)):
        if text(u32(offset(names+4*i)))==name:
            index=u16(offset(ordinals+2*i));rva=u32(offset(functions+4*index))
            return dict(name=name,RVA=rva,forwarder=text(rva) if erva<=rva<erva+esize else None)
    return None


def main(directory):
    out=workspace_path(directory,reports=True)
    if out.exists() or out.parent!=ROOT/'reports/m4-crt-allocation-root':raise ValueError('Fresh read-only API diagnosis')
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetModuleHandleW.argtypes=[C.c_wchar_p];kernel.GetModuleHandleW.restype=C.c_void_p
    kernel.GetProcAddress.argtypes=[C.c_void_p,C.c_char_p];kernel.GetProcAddress.restype=C.c_void_p
    kernel.GetModuleFileNameW.argtypes=[C.c_void_p,C.c_wchar_p,C.c_uint32];kernel.GetModuleFileNameW.restype=C.c_uint32
    class MBI(C.Structure):
        _fields_=[('base',C.c_void_p),('owner',C.c_void_p),('allocation_protect',C.c_uint32),
                  ('partition',C.c_uint16),('bytes',C.c_size_t),('state',C.c_uint32),('protect',C.c_uint32),('type',C.c_uint32)]
    kernel.VirtualQuery.argtypes=[C.c_void_p,C.POINTER(MBI),C.c_size_t];kernel.VirtualQuery.restype=C.c_size_t
    def module_path(owner):
        buf=C.create_unicode_buffer(32768);n=kernel.GetModuleFileNameW(owner,buf,len(buf))
        if not 0<n<len(buf):raise ValueError('Exact loaded module path')
        return Path(buf.value)
    imported=kernel.GetModuleHandleW('kernel32.dll');origin=module_path(imported)
    evidence=[];files={str(origin):hashlib.sha256(origin.read_bytes()).hexdigest()}
    for name,alias in (('HeapAlloc','RtlAllocateHeap'),('HeapFree','RtlFreeHeap')):
        target=kernel.GetProcAddress(imported,name.encode());mbi=MBI()
        if not target or kernel.VirtualQuery(target,C.byref(mbi),C.sizeof(mbi))!=C.sizeof(mbi):raise ValueError('Exact actual export target region')
        path=module_path(mbi.owner);files[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        same=kernel.GetProcAddress(mbi.owner,name.encode());aliased=kernel.GetProcAddress(mbi.owner,alias.encode())
        owner_name=name if same==target else alias
        owner_export=export(path,owner_name)
        resolved=same if same==target else aliased
        if not owner_export or owner_export['forwarder'] is not None or mbi.owner+owner_export['RVA']!=target or aliased!=target:
            if not owner_export or owner_export['forwarder'] is not None or mbi.owner+owner_export['RVA']!=target or resolved!=target:
                raise ValueError('Exact actual owner named export, preserving finite forwarding')
        evidence.append(dict(imported_name=name,imported_module=str(origin),imported_export=export(origin,name),
                             actual_target=target,actual_owner=mbi.owner,actual_owner_module=str(path),
                             same_spelling_owner_export=same,actual_owner_export_name=owner_name,
                             owner_export=owner_export,actual_owner_named_target=resolved))
    files[str(Path(__file__).absolute())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.mkdir(parents=True)
    report=dict(passed=True,scope='Read-only loaded current export diagnosis; no HeapAlloc or HeapFree executed',
                evidence=evidence,files=files,heap_API_executed=False,source_or_game_executed=False)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report))


if __name__=='__main__':main(*sys.argv[1:])
