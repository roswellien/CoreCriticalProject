"""Finite current141 named144 MSVCRT import-cell probe; ordinary inputs only.

Resolves all144 physical KERNEL32 imports of the staged MSVCRT (IAT page
7802E000) through the KERNEL32/NTDLL images captured in the current original141
export (named export and forwarder chain). At every original141 phase BEFORE/
AFTER each cell must hold exactly its real loaded export target or, for a
current patch-spec IAT cell, its exact instrumented shim target; the per-phase
shim schedule is DERIVED, not assumed (inherited phase13 is not reused). Every
native141 source6 O0/O2 cell must equal the physical raw import thunk at every
phase. Measurement only; no whole-page policy, footprint or paired141 credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
IAT=0x7802e000
CONFIG=('reports/m4-original141-source/configuration-preparation-r3/configuration.json','451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);D=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');pe=load('physicalPE',R/'tools/analysis/pe.py')
 C=json.loads(pin(R/CONFIG[0],CONFIG[1]).read_bytes());V=json.loads(pin(C['validation']['path'],C['validation']['sha256']).read_bytes());assert V['passed']and V['reader_closed']
 patches=json.loads(pin(C['current_transition_patches']['path'],C['current_transition_patches']['sha256']).read_bytes())
 iat_patches={p['pc']-IAT:p for p in patches if IAT<=p['pc']<IAT+4096};assert all(p['named_API']for p in iat_patches.values())
 msvcrt=(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve();pin(msvcrt,V['files'][str(msvcrt)]);image=pe.PEImage(msvcrt.read_bytes());assert image.image_base==0x78000000
 imports=image.imports();assert len(imports)==1 and imports[0]['library'].lower()=='kernel32.dll'and len(imports[0]['symbols'])==144
 orow=next(e for e in V['paired_exports']if e['branch']=='original');oi=pin(orow['index_path'],orow['index_sha256']);op=pin(orow['payload_path'],orow['payload_sha256'])
 oes=D.entries(oi,re.compile(r'(?:lockit/modules/(?:1984036864|1997275136)/(?:image|path)|phase/[0-5]/\d+/CRT-(?:before|after)/2013454336)\.bin'));assert len(oes)==4+846*2,len(oes)
 def read(path,es,k):
  z=es[k]
  with Path(path).open('rb')as f:f.seek(z['offset']);b=f.read(z['bytes'])
  assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
 modules={};facts=[]
 for base,library in[(0x76420000,'KERNEL32.DLL'),(0x770c0000,'NTDLL.DLL')]:
  raw=read(op,oes,f'lockit/modules/{base}/image.bin');path=read(op,oes,f'lockit/modules/{base}/path.bin');assert library.lower()in path.decode('utf-16le').lower()
  im=pe.PEImage(raw);modules[library]=(base,{n:r for r in im.exports()for n in r['names']});facts.append(dict(runtime_base=base,library=library,physical_image_sha256=hashlib.sha256(raw).hexdigest(),captured_path=path.decode('utf-16le').rstrip('\x00')))
 cells=[];forwarded=0
 for symbol in imports[0]['symbols']:
  offset=symbol['iat_rva']-0x2e000;assert 0<=offset<=4092 and offset%4==0;nm=symbol['name'];base,exports=modules['KERNEL32.DLL'];ex=exports[nm];chain=[dict(library='KERNEL32.DLL',name=nm,rva=ex['rva'])]
  if 'forwarder'in ex:
   lib,fwd=ex['forwarder'].split('.',1);assert lib=='NTDLL';base,exports=modules['NTDLL.DLL'];ex=exports[fwd];assert 'forwarder'not in ex;chain.append(dict(library='NTDLL.DLL',name=fwd,rva=ex['rva']));forwarded+=1
  real=base+ex['rva'];raw=image.rva_u32(symbol['iat_rva']);assert image.rva_string(raw+2)==nm;shim=None
  if offset in iat_patches:
   p=iat_patches[offset];assert p['named_API']==nm,'Patch spec names the same physical import';assert int.from_bytes(bytes.fromhex(p['original_hex']),'little')==real,'Patch original equals actual current loaded export';shim=int.from_bytes(bytes.fromhex(p['instrumented_hex']),'little')
  cells.append(dict(offset=offset,library=imports[0]['library'],name=nm,native_raw_thunk=raw,original_real_target=real,observer_shim_target=shim,physical_export_chain=chain))
 assert len({c['offset']for c in cells})==144
 shim_cells=[c for c in cells if c['observer_shim_target']is not None]
 schedule=collections.defaultdict(list);violations=[]
 for s in range(6):
  for ph in range(141):
   for side in('before','after'):
    page=read(op,oes,f'phase/{s}/{ph}/CRT-{side}/2013454336.bin');installed=0
    for c in cells:
     v=struct.unpack_from('<I',page,c['offset'])[0]
     if v==c['original_real_target']:continue
     if c['observer_shim_target']is not None and v==c['observer_shim_target']:installed+=1;continue
     violations.append(dict(branch='original',sequence=s,phase=ph,side=side,offset=c['offset'],name=c['name'],value=v))
    schedule[(installed,)].append((s,ph,side))
 state={f'{s}/{ph}/{side}':n for(n,),rows in schedule.items()for s,ph,side in rows}
 shim_states=sorted({n for(n,)in schedule});restored=sorted({k for k,n in state.items()if n!=len(shim_cells)})
 for lv in('O0','O2'):
  N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True
  row=next(e for e in N['paired_exports']if e['branch']==lv);i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256'])
  es=D.entries(i,re.compile(r'sequence-[0-5]/phase-\d+-(?:before|after)-page-2013454336\.bin'));assert len(es)==1692
  for s in range(6):
   for ph in range(141):
    for side in('before','after'):
     page=read(p,es,f'sequence-{s}/phase-{ph}-{side}-page-2013454336.bin')
     for c in cells:
      v=struct.unpack_from('<I',page,c['offset'])[0]
      if v!=c['native_raw_thunk']:violations.append(dict(branch=lv,sequence=s,phase=ph,side=side,offset=c['offset'],name=c['name'],value=v))
  assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)]
 assert sha(oi)==pins[str(oi)]and sha(op)==pins[str(op)]
 passed=not violations
 rp=out/'import-cells.json';rp.write_text(json.dumps(dict(cells=cells,module_facts=facts,shim_state_by_endpoint=state,violations=violations[:2000]),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=passed,scope='Current141 named144 MSVCRT IAT cells: actual captured KERNEL32/NTDLL export chain, current patch-spec shims, derived original shim schedule over all846x2 endpoints, native raw thunks over 2x1692 endpoints; measurement, no whole-page policy or paired141 claim',
  named_cells=144,forwarded_to_NTDLL=forwarded,patch_spec_IAT_shims=len(shim_cells),shim_names=[c['name']for c in shim_cells],original_endpoints=846*2,native_endpoints=2*1692,
  original_installed_shim_counts_seen=shim_states,endpoints_with_shims_not_fully_installed=len(restored),first_not_fully_installed=restored[:24],violations=len(violations),module_facts=facts,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','named_cells','forwarded_to_NTDLL','patch_spec_IAT_shims','shim_names','original_installed_shim_counts_seen','endpoints_with_shims_not_fully_installed','first_not_fully_installed','violations')}))
 if not passed:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
