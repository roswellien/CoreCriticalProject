"""Bind genuine loaded state, balanced Lockit frames and complete provider pages."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-lockit-original';sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mapped(pe,base):
 r=bytearray(4096);rva=base-pe.image_base
 for s in pe.sections:
  lo=max(rva,s['virtual_address']);hi=min(rva+4096,s['virtual_address']+s['raw_size'])
  if hi>lo:r[lo-rva:hi-rva]=pe.data[s['raw_offset']+lo-s['virtual_address']:s['raw_offset']+hi-s['virtual_address']]
 return bytes(r)
def main(build,digest,execution,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False
 def need(x,w):
  if not x:raise ValueError(w)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact pin '+str(p));need(str(p)not in files or files[str(p)]==v,'No pin conflict');files[str(p)]=v;return p
 def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
 try:
  b=read(pin(build,digest));need(b['passed'],'Actual x86 build');
  for p,h in b['files'].items():pin(p,h)
  prep=Path(b['preparation']);p=read(pin(prep/'report.json',b['preparation_sha256']));need(p['passed']and p['snapshot_bytes']==12964,'Explicit capture ABI')
  for q,h in p['files'].items():pin(q,h)
  provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');provider=PEImage(provider_path.read_bytes());crt_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');game=PEImage(game_path.read_bytes())
  e=Path(execution);seen=read(e/'observations.json');run=read(e/'run.json');exitcode=read(e/'exit.json');need(exitcode['exit_code']==0 and seen['passed']and run['passed'],'Actual complete probe exit')
  need(seen['process_bits']==32 and seen['CRT_base']==0x78000000 and seen['MSVCP_base']==provider.image_base==0x780c0000 and Path(seen['CRT_path']).resolve()==crt_path and Path(seen['MSVCP_path']).resolve()==provider_path,'Actual exact staged DLLs and preferred bases')
  exports={n:provider.image_base+r['rva']for r in provider.exports()for n in r['names']};need(exports['??0_Lockit@std@@QAE@XZ']==seen['constructor']==0x7810a290 and exports['??1_Lockit@std@@QAE@XZ']==seen['destructor']==0x7810a350,'Physical+actual loaded exports')
  imports={provider.image_base+r['iat_rva']:dict(library=g['library'],**r)for g in provider.imports()for r in g['symbols']};need(len(seen['imports'])==7,'Seven exact loaded imports')
  for i in seen['imports']:need(imports[i['cell']]['name']==i['symbol']and imports[i['cell']]['library'].lower()==i['library'].lower()and i['target']==i['resolved_export'],'Named source owning IAT and actual resolved target')
  gameimports={game.image_base+r['iat_rva']:dict(library=g['library'],**r)for g in game.imports()for r in g['symbols']};game_bindings=[]
  for cell,name,target in[(0x5bb4f8,'??0_Lockit@std@@QAE@XZ',0x7810a290),(0x5bb4f4,'??1_Lockit@std@@QAE@XZ',0x7810a350)]:
   gi=gameimports[cell];need(gi['library'].lower()=='msvcp50.dll'and gi['name']==name and exports[name]==target,'Exact physical game owning named import');off,_=game.rva_range(cell-game.image_base,4);game_bindings.append(dict(cell=cell,raw_IAT=struct.unpack_from('<I',game.data,off)[0],symbol=name,actual_loader_export=target))
  need(seen['post_DllMain_state']==2 and seen['critical_section']==[0xffffffff,0xffffffff,0,0,0,0x020007d0]and seen['state_seeded']is False,'Authentic initialized unheld resource; no seeding')
  before={a:pin(e/f'post-DllMain-{a:08x}-page.bin').read_bytes()for a in(0x7810a000,0x78145000,0x78146000)};after={a:pin(e/f'after-restored-{a:08x}-page.bin').read_bytes()for a in before};need(all(len(x)==4096 for x in list(before.values())+list(after.values())),'Complete pages')
  need(before[0x7810a000]==mapped(provider,0x7810a000),'Whole authentic post-loader RX page equals preferred-base physical source');need(before==after,'Whole three provider pages restored after balanced calls')
  need(pin(e/'state-and-CS.bin').read_bytes()==before[0x78145000][0x640:0x65c],'Exact CS24+state4 bytes from whole page')
  for i in seen['pages']:need(i['allocation_base']==provider.image_base and i['state']==0x1000 and i['type']==0x1000000 and i['protection']==(0x20 if i['page']==0x7810a000 else 4),'Genuine image ownership and permissions')
  for name,disk in [('kernel32-image.bin','C:/Windows/SysWOW64/kernel32.dll'),('ntdll-image.bin','C:/Windows/SysWOW64/ntdll.dll')]:
   captured=pin(e/name);actual=pin(disk);need(captured.read_bytes()==actual.read_bytes()and PEImage(captured.read_bytes()).machine==0x14c,'Actual x86 system provider image under WOW64 path redirection')
  payload=pin(e/'snapshots.bin').read_bytes();need(len(payload)==18*12964 and run['snapshots']==18 and run['snapshot_bytes']==12964 and run['balanced_pairs']==3 and run['recursive_depth']==2 and run['restored']and not run['state_seeded'],'18 genuine machine snapshots and three balanced pairs')
  rows=[];depths=[0,0,1,1,1,0,0,0,1,1,1,2,2,2,1,1,1,0];kinds=[0,1,2,3,4,5]*1+[0,1,2,0,1,2,3,4,5,3,4,5]
  for n in range(18):
   raw=payload[n*12964:(n+1)*12964];words=struct.unpack_from('<8I',raw);cpu=struct.unpack_from('<10I',raw,32);frame=struct.unpack_from('<8I',raw,612);cs=struct.unpack_from('<6I',raw,644);pages={a:raw[668+k*4096:668+(k+1)*4096]for k,a in enumerate(before)};kind=kinds[n];depth=depths[n]
   need(words[:4]==(1,n,0 if n<6 else 1,kind)and words[4]==seen['thread_id']and words[5]==2,'Actual sequence/event/thread/state identities');need(cs==(0xffffffff,0xfffffffe if depth else 0xffffffff,depth,seen['thread_id']if depth else 0,0,0x020007d0),'Actual held/unheld/recursive CS encoding')
   need(pages[0x78145000][0x640:0x658]==raw[644:668]and struct.unpack_from('<I',pages[0x78145000],0x658)[0]==2,'Wholepage actual CS24/state joins');need(raw[12956:12964]==bytes(8),'Scratch objects have no writes')
   if kind in(1,4):need(cpu[9]==words[7]==run['actual_Enter'if kind==1 else'actual_Leave']and frame[:2]==(0x7810a311 if kind==1 else 0x7810a364,0x78145640),'Actual observed provider entry frame and tail-jump target')
   else:need(cpu[9]=={0:0x7810a290,2:0x7810a311,3:0x7810a350,5:0x7810a364}[kind],'Exact actual source checkpoint PC')
   # Every source/provider page byte outside declared code/IAT patches and CS24 is exact.
   for a,page in pages.items():
    expected=bytearray(before[a])
    if a==0x78145000:expected[0x640:0x658]=raw[644:668]
    elif a==0x7810a000:
     for h in p['hooks']:
      o=h['pc']-a;observed=page[o:o+h['size']];need(observed[0]==0xe9 and observed[5:]==b'\x90'*(h['size']-5),'Exact declared JMP/NOP observer patch');expected[o:o+h['size']]=observed
    else:
     for cell in(0x78146198,0x78146184):expected[cell-a:cell-a+4]=page[cell-a:cell-a+4]
    need(page==bytes(expected),'Whole provider page equality outside exact observer patches and actual CS')
   rows.append(dict(index=n,sequence=words[2],kind=kind,PC=cpu[9],ESP=cpu[4],EAX=cpu[0],object=words[6],depth=depth,actual_thread=words[4],flags=cpu[8],frame=list(frame),FX_sha256=hashlib.sha256(raw[72:584]).hexdigest(),ENV_sha256=hashlib.sha256(raw[584:612]).hexdigest()))
  # Actual source entry, authentic CALL provider frame and returned source frame.
  for start in(0,6,9):
   a,api,z=rows[start:start+3];need(api['ESP']==a['ESP']-16 and z['ESP']==a['ESP']-8,'Ctor actual F-16 API/F-8 pre-epilogue frames');need(rows[start]['FX_sha256']==api['FX_sha256']and rows[start]['ENV_sha256']==api['ENV_sha256'],'Integer source prefix preserves complete FX512/ENV28')
  for start in(3,12,15):
   a,api,z=rows[start:start+3];need(api['ESP']==a['ESP']-8 and z['ESP']==a['ESP'],'Dtor actual F-8 API/F preRET frames');need(rows[start]['FX_sha256']==api['FX_sha256']and rows[start]['ENV_sha256']==api['ENV_sha256'],'Integer source prefix preserves complete FX512/ENV28')
  (out/'snapshot-relations.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'snapshot-relations.json');pin(__file__);pin(sys.executable);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Authentic exact staged original32 post-DllMain state2 and balanced scratch Lockit/actual Windows CS provider observations; no initializer credit',build_path=str(build),build_sha256=digest,preparation_path=b.get('preparation')if'b'in locals()else None,preparation_sha256=b.get('preparation_sha256')if'b'in locals()else None,execution=str(execution),snapshots=18,snapshot_bytes=12964,complete_provider_pages=3,whole_page_relations=54,actual_CPU_FX_ENV_boundaries=18,balanced_pairs=3,recursive_depth=2,constructor_observation='actual entry; actual API entry; actual source returned at7810A311 before MOV EAX,EDI/POP EDI/POP ESI/RET; external genuine return EAX==scratchECX validated by worker',destructor_observation='actual entry; actual API entry; actual source immediate preRET7810A364',provider_API_frame_geometry=dict(constructor='F-16',destructor='F-8'),critical_section_bytes=24,post_DllMain_state=2,state_seeded=False,genuine_lazy_initialization_observed=False,genuine_loaded_domain=True,game_import_bindings=game_bindings if'game_bindings'in locals()else[],game_called=False,original_executed=True,native_executed=False,root_credit=0,files=files)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
