"""ROOT-admitted ordinary input cut: current provider identities and13 spans.

No source execution. Actual BEFORE cells/loaded named rows are inputs;
post-MFC bytes are equality targets only, never defaults for original spans.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
VPATH=R/'reports/m4-original141/root-capture-validation-r3/report.json'
VSHA='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,name):
 ap=Path(admission_path).resolve();need(sha(ap)==admission_sha,'Exact ROOT input-cut admission');ad=json.loads(ap.read_bytes());need(ad['passed']is True and ad['independent_review']is True and ad['scope_identity']=='original141_current_input_materialization','ROOT only, no self admission')
 admitted={}
 for p,h in ad['files'].items():
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Ordinary closure only');need(str(p)not in admitted and sha(p)==h,'Whole unique closure before imports');admitted[str(p)]=h
 out=R/'reports/m4-original141-source'/name;need(not out.exists(),'Fresh immutable input cut');out.mkdir();pins={str(ap):admission_sha};reader=None;passed=False;rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical data');v=sha(p);need(p.is_relative_to(out)or admitted.get(str(p))==v,'Exact admitted input without fallback');need(h is None or h==v,'Exact named identity');need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 try:
  pin(__file__);V=read(VPATH,VSHA);need(V['passed']and V['reader_closed']and V['counts']['phases']==846 and V['callbacks']==111,'Exact actual current strict3')
  metadata=read(R/'reports/m4-original141-source/root-input-metadata-r1/report.json','eb73abbf388a8407a5f412755675e5f611ef70cfdb8698b9b450f3476c0cbe67')
  named=read(VPATH.parent/'current-named-CRT-inputs.json');need(named['passed']and named['source_AFTER_seed']is False and len(named['named_binding_rows'])==144,'Whole actual18 by8 named own rows')
  declarations=read(R/'reports/m4-original141/transition-preparation-r3/patch-declarations.json');need(len(declarations)==13,'Exact compiled current13 declarations')
  pin(R/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c');pin(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json')
  P=load(R/'tools/analysis/pe.py','current141_physical_PE');images={}
  for key,path in [('MFC',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL'),('CRT',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),('Game',R/'MW3/Mech3.exe')]:images[key]=P.PEImage(pin(path).read_bytes())
  def export(key,field,value):
   image=images[key];found=[r for r in image.exports()if(r['ordinal']==value if field=='ordinal'else value in r['names'])];need(len(found)==1 and not found[0].get('forwarder'),'Exact physical named direct export');return image.image_base+found[0]['rva']
  targets={'823':export('MFC','ordinal',823),'825':export('MFC','ordinal',825),'malloc':export('CRT','name','malloc'),'free':export('CRT','name','free'),'_onexit':export('CRT','name','_onexit')}
  def imported(key,cell,library,field,value):
   image=images[key];found=[s for d in image.imports()if d['library'].casefold()==library.casefold()for s in d['symbols']if image.image_base+s['iat_rva']==cell];need(len(found)==1 and found[0].get(field)==value,'Exact physical owning named import')
  for args in [('Game',0x5bb4bc,'MFC42.DLL','ordinal',823),('Game',0x5bb4c8,'MFC42.DLL','ordinal',825),('Game',0x5bb52c,'MSVCRT.DLL','name','_onexit'),('MFC',0x5f49814c,'MSVCRT.DLL','name','malloc'),('MFC',0x5f498148,'MSVCRT.DLL','name','free')]:imported(*args)
  E=load(R/'tools/m4-startup138-original/export_reader_r2.py','original141_input_export');reader=E.ExportReader(VPATH,VSHA,'original',pin)
  expected=[1,targets['823'],targets['825'],targets['823'],targets['825'],targets['malloc'],targets['free']];need(list(struct.unpack('<7I',reader.data('constructor/provider-entries.bin')))==expected,'Actual current loaded provider-entry tuple')
  def page(seq,phase,side,address):
   stem=f'phase/{seq}/{phase}';logical=f'{stem}/extra-{side}/{address}.bin'
   if 0x78000000<=address<0x78040000:
    need(address%4096==0 and side in('before','after')and V['counts']['widget_whole_CRT_phase_page_endpoints']==108288,'Exact current own64CRT source domain and all846 paired observations');logical=f'{stem}/CRT-{side}/{address}.bin';need(logical in reader.entries,'Exact producer own64CRT logical input/target, no page fallback');b=reader.data(logical)
   elif logical in reader.entries:b=reader.data(logical)
   else:
    raw=reader.data(stem+'.bin');need(len(raw)==356992 and address in metadata['observed_pages'],'Whole observed own page');off=(2276 if side=='before'else 178404)+metadata['observed_pages'].index(address)*4096;b=raw[off:off+4096]
   need(len(b)==4096,'Whole input/target page');return b
  for seq in range(6):
   for phase in(13,14,39):
    for cell,target in [(0x5bb4bc,targets['823']),(0x5bb4c8,targets['825']),(0x5bb52c,targets['_onexit']),(0x5f49814c,targets['malloc']),(0x5f498148,targets['free'])]:need(struct.unpack_from('<I',page(seq,phase,'before',cell&~4095),cell&4095)[0]==target,'Every actual own constructor BEFORE owning import')
  patches=[]
  for declaration in declarations:
   patch=dict(declaration);pc=patch['pc']
   if patch['kind']=='registry-IAT':
    facts=[r for r in named['named_binding_rows']if r['cell']==pc];need(len(facts)==18 and len({r['target']for r in facts})==1 and all(r['shim']==patch['compiled_target']and r['raw']==patch['compiled_target']for r in facts),'Actual stable own18 named cell targets/current shim')
    need(patch['original_hex']is None,'Dynamic declarations remain unfilled until actual source input cut');patch['original_hex']=struct.pack('<I',facts[0]['target']).hex()
   else:
    b=bytes.fromhex(patch['original_hex']);image=images['CRT'];off=image.rva_range(pc-image.image_base,len(b))[0];need(image.data[off:off+len(b)]==b,'Literal original CRT bytes from physical staged module')
   a=bytes.fromhex(patch['original_hex']);z=bytes.fromhex(patch['instrumented_hex']);need(len(a)==len(z)>0,'Exact span width')
   for seq in range(6):
    for phase,side,want in [(14,'after',z),(15,'before',a),(15,'after',a),(16,'before',z)]:need(page(seq,phase,side,pc&~4095)[pc&4095:(pc&4095)+len(want)]==want,f'Current exact owning producer-cut span PC={pc:#x} sequence={seq} phase={phase} side={side} expected={want.hex()} actual={page(seq,phase,side,pc&~4095)[pc&4095:(pc&4095)+len(want)].hex()}');rows.append(dict(sequence=seq,phase=phase,side=side,pc=pc,bytes=len(want)))
   patches.append(patch)
  write(out/'patches.json',patches);write(out/'provider-proof.json',dict(passed=True,scope='Current physical named provider exports/owning imports, all18 genuine constructor BEFORE loaded cells and actual current provider-entry tuple; no source CPU execution',targets=targets,provider_entry_expected=expected,original_validation_sha256=VSHA,source_AFTER_seed=False,canonical_reader_opened=False,files=dict(pins)))
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc())
 finally:
  if reader:reader.close()
  for p,h in pins.items():need(sha(p)==h,'Final exact dependency rehash')
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,original_validation_sha256=VSHA,span_relations=rows,reader_closed=reader is None or reader.closed,canonical_reader_opened=False,source_execution=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
