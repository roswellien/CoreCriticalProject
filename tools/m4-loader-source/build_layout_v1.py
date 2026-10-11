"""Actual x86/x64 SDK COFF layout witnesses only. No link, workers or readers."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(preparation,expected,name):
 prep=(R/preparation).resolve();need(sha(prep)==expected,'Exact obligations preparation');d=json.loads(prep.read_bytes());need(d['passed']and d['root']==0x47f760,'Actual loader obligation domain');out=R/'reports/m4-loader-source'/name;need(not out.exists(),'Fresh compile-only output');out.mkdir(parents=True);pins={};commands=[];witnesses={};error=None
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.zip','.mwb'),'No archive input');v=sha(p);need(h is None or h==v,'Exact physical compiler/source input '+str(p));pins[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 pin(__file__);src=pin(prep.parent/'layout_witness.cpp');vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231');sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0');env=dict(os.environ);env['INCLUDE']=';'.join(str(p)for p in[vc/'include',sdk/'ucrt',sdk/'shared',sdk/'um',sdk/'winrt',sdk/'cppwinrt']);fields=['marker','pointer_bytes','OSVERSIONINFOA_bytes','DDSURFACEDESC_bytes','lpSurface_offset','ddpfPixelFormat_offset','ddsCaps_offset','QueryInterface_slot','Release_slot','SetCooperativeLevel_slot','CreateSurface_slot','GUID_bytes']
 try:
  for arch,machine in[('x86',0x14c),('x64',0x8664)]:
   compiler=pin(vc/'bin/Hostx64'/arch/'cl.exe');obj=out/(arch+'.obj');argv=[str(compiler),'/nologo','/std:c++20','/O2','/EHsc','/W4','/WX','/MD','/showIncludes','/c','/Fo'+str(obj),str(src)];p=subprocess.run(argv,cwd=out,env=env,capture_output=True,timeout=90,creationflags=0x08000000);a=out/(arch+'.stdout');b=out/(arch+'.stderr');a.write_bytes(p.stdout);b.write_bytes(p.stderr);pin(a);pin(b);headers=[]
   for line in(p.stdout+p.stderr).decode(errors='replace').splitlines():
    if 'Note: including file:'in line:
     q=pin(line.split('Note: including file:',1)[1].strip())
     if str(q)not in headers:headers.append(str(q))
   commands.append(dict(argv=argv,INCLUDE_environment=env['INCLUDE'],exit_code=p.returncode,stdout=str(a),stderr=str(b),actual_headers=headers));need(p.returncode==0,'Actual SDK layout compile '+arch);pin(obj);raw=obj.read_bytes();m,count=struct.unpack_from('<HH',raw);need(m==machine and count<=96,'Actual COFF architecture');sections=[]
   for i in range(count):
    off=20+40*i;nm,_,_,size,fo=struct.unpack_from('<8sIIII',raw,off)
    if nm.split(b'\0')[0]==b'.mwabi':need(fo+size<=len(raw),'Whole COFF witness extent');sections.append(raw[fo:fo+size])
   need(len(sections)==1 and len(sections[0])==48,'Whole named actual layout witness');vals=struct.unpack('<12I',sections[0]);need(vals[0]==0x4d573431 and vals[2]==148 and vals[11]==16,'Actual API input layouts');witnesses[arch]=dict(zip(fields,vals));witnesses[arch]['whole_CO​​FF_section_hex']=sections[0].hex();witnesses[arch]['object_sha256']=sha(obj)
  need([witnesses['x86'][x]for x in fields]==[0x4d573431,4,148,108,36,72,104,0,8,80,24,16],'Actual x86 SDK fields equal all physical source struct/slot dimensions');need(witnesses['x64']['pointer_bytes']==8,'Actual x64 pointer layout');need([witnesses['x64'][x]for x in fields[7:11]]==[0,16,160,48],'Actual typed x64 slot offsets, not fabricated x86 byte offsets')
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in pins.items():need(sha(p)==h,'Stable complete compiler/source/header closure')
 report=dict(passed=error is None,scope='Actual two-architecture SDK COFF layout proof, compile only; no runtime service results',preparation_sha256=expected,root=0x47f760,witnesses=witnesses,commands=commands,files=pins,worker_linked=False,source_or_provider_API_executed=False,archive_reader_opened=False,initializer_credit=0,error=error);p=out/'build.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(p),sha256=sha(p),witnesses=witnesses,error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
