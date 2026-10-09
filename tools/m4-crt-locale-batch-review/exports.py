"""Read-only native export-chain audit; no CS/NLS/heap API is invoked."""
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
NAMES=('InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection','GetACP','GetCPInfo','GetStringTypeW','GetStringTypeA','LCMapStringW','LCMapStringA','MultiByteToWideChar','WideCharToMultiByte')

def need(ok,why):
    if not ok:raise ValueError(why)

def export(raw,name):
    u16=lambda p:struct.unpack_from('<H',raw,p)[0];u32=lambda p:struct.unpack_from('<I',raw,p)[0]
    pe=u32(60);opt=pe+24;need(u16(0)==0x5a4d and u32(pe)==0x4550 and u16(pe+4)==0x8664 and u16(opt)==0x20b,'Actual AMD64 PE module')
    er,es=u32(opt+112),u32(opt+116);sections=[opt+u16(pe+20)+40*i for i in range(u16(pe+6))]
    def at(rva,n=1):
        hits=[u32(s+20)+rva-u32(s+12) for s in sections if u32(s+12)<=rva and rva+n<=u32(s+12)+u32(s+16)]
        need(len(hits)==1 and hits[0]+n<=len(raw),'Unique checked physical export RVA');return hits[0]
    def text(rva):
        p=at(rva);end=raw.find(b'\0',p,min(len(raw),p+4096));need(end>=p,'Bounded terminated native export string');return raw[p:end].decode('ascii')
    e=at(er,40);fs,ns,os=u32(e+28),u32(e+32),u32(e+36);result=[]
    for i in range(u32(e+24)):
        if text(u32(at(ns+4*i,4)))==name:
            o=u16(at(os+2*i,2));need(o<u32(e+20),'Named native export ordinal');r=u32(at(fs+4*o,4));result.append({'name':name,'RVA':r,'forwarder':text(r) if er<=r<er+es else ''})
    need(len(result)==1,'Unique native named export');return result[0]

def main(directory):
    out=workspace_path(directory,reports=True);need(out.parent==ROOT/'reports/m4-crt-locale-batch-review' and not out.exists(),'Fresh read-only export review')
    k=C.WinDLL('kernel32',use_last_error=True)
    k.GetModuleHandleW.argtypes=[C.c_wchar_p];k.GetModuleHandleW.restype=C.c_void_p
    k.GetProcAddress.argtypes=[C.c_void_p,C.c_char_p];k.GetProcAddress.restype=C.c_void_p
    k.GetModuleFileNameW.argtypes=[C.c_void_p,C.c_wchar_p,C.c_uint32];k.GetModuleFileNameW.restype=C.c_uint32
    class MBI(C.Structure):
        _fields_=[('base',C.c_void_p),('owner',C.c_void_p),('allocation_protect',C.c_uint32),('partition',C.c_uint16),('bytes',C.c_size_t),('state',C.c_uint32),('protect',C.c_uint32),('type',C.c_uint32)]
    k.VirtualQuery.argtypes=[C.c_void_p,C.POINTER(MBI),C.c_size_t];k.VirtualQuery.restype=C.c_size_t
    files={};modules={}
    def module(handle):
        if handle not in modules:
            b=C.create_unicode_buffer(32768);n=k.GetModuleFileNameW(handle,b,len(b));need(0<n<len(b),'Native module path bounds');p=Path(b.value);raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();files[str(p)]=digest;modules[handle]=(p,raw,digest)
        return modules[handle]
    named=k.GetModuleHandleW('kernel32.dll');need(named,'Loaded original named module');evidence=[]
    for name in NAMES:
        target=k.GetProcAddress(named,name.encode());need(target,'Actual named target');region=MBI();need(k.VirtualQuery(target,C.byref(region),C.sizeof(region))==C.sizeof(region) and region.state==0x1000 and region.type==0x1000000 and not region.protect&0x101 and region.protect&0xf0,'Actual executable committed native image')
        origin=module(named);owner=module(region.owner);current=name;handle=named;chain=[]
        for depth in range(4):
            p,raw,digest=module(handle);entry=export(raw,current);chain.append({'module':str(p),'module_base':handle,'module_sha256':digest,**entry})
            if not entry['forwarder']:
                resolved=k.GetProcAddress(handle,current.encode());need(handle+entry['RVA']==target==resolved and handle==region.owner,'Physical terminal export and actual owner/target agree');break
            dll,current=entry['forwarder'].rsplit('.',1);need(current and not current.startswith('#'),'Finite named forwarder chain');handle=k.GetModuleHandleW(dll+'.dll');need(handle,'Already loaded forwarded owner; no DLL load')
        else:raise ValueError('Bounded direct terminal forwarder chain')
        evidence.append({'requested_name':name,'actual_target':target,'actual_owner':region.owner,'same_spelling_owner_export':k.GetProcAddress(region.owner,name.encode()),'chain':chain})
    for p in (Path(__file__).absolute(),Path(sys.executable),ROOT/'tools/m4-crt-locale-batch-review/review-contract.md'):
        files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    report={'passed':True,'scope':'Read-only current native export/forwarder identities; no CS/NLS/heap call or source/game execution','API_semantics_executed':False,'heap_or_CS_created':False,'source_executed':False,'names':list(NAMES),'evidence':evidence,'files':files}
    out.mkdir(parents=True);publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'passed':True,'names':len(NAMES),'chains':{r['requested_name']:[c['forwarder'] or c['name'] for c in r['chain']] for r in evidence}}))

if __name__=='__main__':main(*sys.argv[1:])
