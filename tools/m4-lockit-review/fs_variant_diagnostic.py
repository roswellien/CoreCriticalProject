"""Bind the observed pre-API rejection to two exact read-before-push FS prologs."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or h==a,(p,h,a);pins[str(p)]=a;return p
 def read(p):return json.loads(pin(p).read_bytes())
 def load_module(name,path):
  s=importlib.util.spec_from_file_location(name,pin(path));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pe=load_module('lockit_FS_PE',ROOT/'tools/analysis/pe.py').PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 rows=read(ROOT/'reports/m4-lockit-frontier/recovery-r1/game-normal-graphs.json');variants=[]
 for entry,read_pc,early in ((0x4125a0,0x4125a0,True),(0x4dc150,0x4dc167,False),(0x500cd0,0x500cd0,True),(0x596900,0x596907,False)):
  g=rows[str(entry)]['instructions'];prefix=[r for r in g if r['pc']<=read_pc];read_row=next(r for r in prefix if r['pc']==read_pc);assert read_row['bytes']=='64a100000000'
  pushes=[r for r in prefix if r['mnemonic']=='push'];assert len(pushes)==(0 if early else 2)
  for r in prefix:
   off,_=pe.rva_range(r['pc']-pe.image_base,r['size']);assert pe.read(off,r['size'])==bytes.fromhex(r['bytes'])
  variants.append({'entry':entry,'read_PC':read_pc,'read_before_handler_scope_pushes':early,'CALL_frame_at_FS_read':'ESP' if early else 'ESP+8','physical_prefix':prefix})
 read(ROOT/'reports/m4-lockit-review/native-integration-r2/report.json')
 build=read(ROOT/'reports/m4-lockit-review/controls-build-r2/build.json');assert build['passed'];execution=read(ROOT/'reports/m4-lockit-review/controls-execution-r1/report.json');assert not execution['passed']
 direct=load_module('lockit_FS_reader',ROOT/'tools/m4-crt-allocation-root/run_v2.py');observations=[]
 for level in ('O0','O2'):
  pin(build['workers'][level]['path'],build['workers'][level]['sha256']);stage=read(ROOT/f'reports/m4-lockit-review/controls-execution-r1/{level}-stage/stage.json');assert not stage['passed']
  d=direct.DirectSet(ROOT/f'reports/m4-lockit-review/controls-execution-r1/{level}/transport.json',pin)
  try:
   reason=d.data('case-0/first-live/registry-exception-message.bin').decode();assert reason=='Original source CALL frame and literal handler/scope pushes before FS read'
   cpu=struct.unpack('<10I',d.data('case-0/first-causal-CPU.bin'));assert cpu[9]==0x4125a0
   stack=d.data('case-0/first-causal-stack.bin');frame=cpu[4];actual=struct.unpack_from('<6I',stack,frame-0x20001000);assert actual[0]==0x411035 and actual[1:]==(0x200017fb,0x200017fa,0x80,0x411015,0xffffffa0)
   source=d.data('case-0/first-live/locale-source-accesses.bin');assert len(source)%24==0;tail=list(struct.iter_unpack('<IIQII',source))[-6:]
   assert tail[-1]==(0x411030,frame,0x411035,4,1)
   assert d.data('case-0/first-live/lockit-calls.bin')==b'' and d.data('case-0/first-live/lockit-imports.bin')==b''
   observations.append({'level':level,'actual_CPU':cpu,'actual_CALL_frame':frame,'actual_frame_words':actual,'actual_source_prefix_tail':tail,'reason':reason,'Lockit_source_API_reached':False})
  finally:d.close()
 install=pin(ROOT/'reports/m4-lockit-native/preparation-r3/fs_operations.inc').read_text()
 assert 'value!=w[9]||state.gpr.rsp.dword!=w[9]' in install and 'runtime.memory().load<unsigned>({unsigned(w[9]+4)})!=w[10]||runtime.memory().load<unsigned>({unsigned(w[9]+8)})!=UINT32_MAX' in install
 pin(__file__)
 (out/'report.json').write_text(json.dumps({'passed':True,'scope':'Independent physical/compiled observed rejection diagnosis; native candidate is still rejected','initializer_credit':False,'variants':variants,'observations':observations,'required_change':'Only 4125A0 and500CD0 exact early FS reads use ESP for authentic CALL frame; retain complete genuine predecessor/handler/marker verification at exact later source installation, then full restoration/RET checks. Other FS readers retain ESP+8 pre-push verification.','files':pins},indent=2)+'\n')
 print(json.dumps({'passed':True,'sha256':sha(out/'report.json')}))
if __name__=='__main__':main(sys.argv[1])
