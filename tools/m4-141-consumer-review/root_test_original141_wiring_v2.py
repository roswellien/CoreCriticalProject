"""Ordinary-only current binding and synthetic loaded-export controls."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
from named_loader141_v2 import prove,export_target,CELLS,NAMES,ROOTS
def main():
 out=R/'reports/m4-original141/root-validator-wiring-controls-r1';out.mkdir()
 files={};controls=[]
 def pin(p):
  p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
 def control(name,fn,reject=False):
  try:fn()
  except (ValueError,KeyError,struct.error):
   assert reject,name
  else:assert not reject,name
  controls.append(dict(name=name,rejected=reject))
 links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r1/physical-links.json').read_text());res={}
 for row in links:
  for x in row['relocations']:
   if x['symbol_section']==0 and x['resolution_kind']=='virtual address':
    k=x['symbol'];v=x['actual_symbol_address'];assert k not in res or res[k]==v;(res.update({k:v}))
 required=['_registry_API_'+str(i)for i in range(8)]+['_format_entry_strrchr','_format_entry_malloc','_format_entry_sprintf','_fps_entry']
 assert all(k in res for k in required)
 shims=[res[k]for k in required[:8]]
 crt=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
 declarations=json.loads(pin(R/'reports/m4-original141/transition-preparation-r1/patch-declarations.json').read_text())
 class Image:
  machine=0x14c
  def __init__(self,rows):self.rows=rows
  def exports(self):return self.rows
 kernel=Image([dict(ordinal=i+1,rva=100+i,names=[n],forwarder='NTDLL.F'+str(i))for i,n in enumerate(NAMES)])
 ntdll=Image([dict(ordinal=i+1,rva=1000+4*i,names=['F'+str(i)])for i in range(8)])
 modules={0x100000:dict(name='KERNEL32.DLL',image=kernel),0x200000:dict(name='NTDLL.DLL',image=ntdll)}
 targets=[export_target(modules,0x100000,n)[0]for n in NAMES]
 control('named forwarder owner',lambda:export_target(modules,0x100000,NAMES[0]))
 control('ordinal export',lambda:export_target(modules,0x200000,'#1'))
 control('missing forwarder owner',lambda:export_target({0x100000:modules[0x100000]},0x100000,NAMES[0]),True)
 control('missing named export',lambda:export_target(modules,0x100000,'missing'),True)
 duplicate={**modules,0x300000:modules[0x200000]}
 control('ambiguous loaded owner',lambda:export_target(duplicate,0x100000,NAMES[0]),True)
 cyclic={0x100000:dict(name='KERNEL32.DLL',image=Image([dict(ordinal=1,rva=1,names=['X'],forwarder='KERNEL32.X')]))}
 control('cyclic forwarded export',lambda:export_target(cyclic,0x100000,'X'),True)
 data={'crt-api-targets.bin':struct.pack('<8I',*targets)}
 for base,name,raw in[(0x100000,'KERNEL32.DLL',b'kernel-synthetic'),(0x200000,'NTDLL.DLL',b'ntdll-synthetic')]:
  disk=out/name;disk.write_bytes(raw);pin(disk);prefix='mfc-modules/'+str(base)+'/'
  data[prefix+'image.bin']=raw;data[prefix+'path.bin']=(str(disk)+'\0').encode('utf-16-le')
 for seq in range(6):
  for phase,root in ROOTS.items():
   stem=f'phase/{seq}/{phase}/';page=bytearray(4096)
   for cell,shim in zip(CELLS,shims):struct.pack_into('<I',page,cell%4096,shim)
   data[stem+'CRT-image/before/'+str(0x7802e000)+'.bin']=bytes(page)
   data[stem+'constructor-input/segments-before.bin']=struct.pack('<2I',1,root)+bytes(128)
   data[stem+'constructor-input/named-API-bindings.bin']=b''.join(struct.pack('<7I',i,c,shims[i],targets[i],shims[i],0x100000,0x200000)for i,c in enumerate(CELLS))
 class Records:
  def __init__(self,d):self.d=d;self.entries=d;self.reads=[]
  def data(self,k):self.reads.append(k);return self.d[k]
 def image(raw):return kernel if raw==b'kernel-synthetic'else ntdll
 reader=Records(data);patches,proof=prove(reader,image,pin,shims,crt,declarations)
 assert len(proof['named_binding_rows'])==144 and len(patches)==13 and not any('after'in k.lower()for k in reader.reads)
 controls.append(dict(name='all18 own inputs,144 exact bindings,no AFTER reads',rejected=False))
 key='phase/0/13/constructor-input/named-API-bindings.bin'
 for word in range(7):
  changed=dict(data);raw=bytearray(changed[key]);v=struct.unpack_from('<I',raw,word*4)[0];struct.pack_into('<I',raw,word*4,v^1);changed[key]=bytes(raw)
  control('typed binding field '+str(word),lambda d=changed:prove(Records(d),image,pin,shims,crt,declarations),True)
 for label,key2,value in [('short224',key,data[key][:-4]),('extra224',key,data[key]+bytes(4)),('wrong own root','phase/0/13/constructor-input/segments-before.bin',bytes(136)),('wrong raw IAT','phase/0/13/CRT-image/before/'+str(0x7802e000)+'.bin',bytes(4096))]:
  changed={**data,key2:value};control(label,lambda d=changed:prove(Records(d),image,pin,shims,crt,declarations),True)
 for name in ['validate_original141_v5.py','constructor_supplement141_v4.py','named_loader141_v2.py','mfc_phase141_v1.py','widget_phase141_v1.py','mfc_transition141_v1.py']:
  p=pin(Path(__file__).parent/name);ast.parse(p.read_bytes())
 # Importing the full driver does not invoke main or construct DirectSet.
 p=Path(__file__).parent/'validate_original141_v5.py';spec=importlib.util.spec_from_file_location('original141_wiring',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 assert module.observe_constructor_supplement.__module__=='constructor_supplement141_v4'
 assert module.prove_named_loader.__module__=='named_loader141_v2'
 assert module.WIDGET_PHASES==(17,18,19,50,137,138,139)
 pin(__file__)
 report=dict(passed=True,controls=controls,unique_required_linked_symbols={k:res[k]for k in required},files=files,reader_opened=False,worker_launched=False,native_executed=False,initializer_credit=0,scope='Synthetic current schema/export/input controls plus actual ordinary linked source identities; no actual capture equivalence')
 path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(path.read_bytes()).hexdigest())
if __name__=='__main__':main()
