"""Exact current141 complete inherited138 plus constructor structural gate."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BUILD='ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc'
PREP='98b3f726249ef233ccdc63855cd5c735aa2ff01cc8717494b686bec34dafb46e'
REVIEW='207e37dcafd10b62886ee8cd22dd3ef82962e029c9d40d1d1129efab41e5426f'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(execution,digest,name):
 out=R/'reports/m4-startup141-root'/name;need(not out.exists(),'Fresh strict141 structural namespace');out.mkdir(parents=True);pins={};passed=False;closed=True;rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact141 structural input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable141 physical input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  e=read(execution,digest);need(e['passed']and e['actual_workers_launched']==2 and e['all_workers_terminal']and e['build_sha256']==BUILD and e['preparation_sha256']==PREP and e['admission_review_sha256']==REVIEW,'Two terminal current141 writers with exact reviewed artifacts')
  p=read(R/'reports/m4-startup141-runway/preparation-r3/report.json',PREP);b=read(R/'reports/m4-startup141-runway/build-r3/build.json',BUILD);a=read(R/'reports/m4-138-validation-review/full141-prelaunch-r2/report.json',REVIEW);need(p['passed']and b['passed']and a['passed'],'Exact current141 source/link prelaunch')
  for q,h in e['files'].items():pin(q,h)
  prepdir=Path(b['preparation']).parent;phase_map=read(R/'reports/m4-startup141-runway/widget-phase-correction-r1/widget-phase-map141.json');old_map=read(prepdir/'widget-phase-map.json');need(len(phase_map)==len(old_map)==7,'Exact inherited seven widgets')
  for current,old in zip(phase_map,old_map):
   actual=next(i for i,x in enumerate(p['selected_order'])if x==dict(entry=current['root'],slot=current['slot']));need(current['phase']==actual and {k:v for k,v in current.items()if k!='phase'}=={k:v for k,v in old.items()if k!='phase'},'Exact physical141 widget phase with every old identity retained')
  page_map=read(prepdir/'source-page-union.json');registration=pin(prepdir/'registration_contract.hpp').read_text();expected_roots=tuple(int(v,16)for v in re.search(r'registration_roots\{([^}]+)',registration)[1].split(','));need(len(expected_roots)==108,'Inherited108 registration observation identities')
  C=load(R/'tools/m4-startup141-root/constructor_structural_v1.py','current141_constructor_structural');source={v['pc']:v for v in read(R/'reports/m4-constructor-source/preparation-r1/source-instructions.json')};cold={pc for pc in source if 0x56fea0<=pc<0x56ff00};constructor_roots=[0x4103f0,0x410440,0x459b40];expectedcalls=[(constructor_roots[0],0x58af12,0x5abd26,12),(constructor_roots[0],0x58af6a,0x5abd26,4),(constructor_roots[0],0x58af9a,0x5abd1a,0),(constructor_roots[1],0x58af12,0x5abd26,12),(constructor_roots[1],0x58af6a,0x5abd26,4),(constructor_roots[1],0x58af9a,0x5abd1a,0),(constructor_roots[2],0x58f2a2,0x5abd26,12),(constructor_roots[2],0x45b80e,0x5abd26,12)]
  BUDGET=load(R/'tools/m4-startup141-root/allocation_budget_v1.py','current141_exact_allocation_budget');RAW=load(R/'tools/m4-startup141-root/raw12_v1.py','current141_raw12');DS=load(R/'tools/m4-crt-allocation-root/run_storage.py','current141_canonical_storage');pin(__file__);pin(sys.executable)
  for level in('O0','O2'):
   records=DS.DirectSet(Path(e['runs'][level]['capture']),pin);closed=False
   try:
    need(records.words('native-header.bin',6)==(1,6,141,846,17,159716)and records.words('sequences-header.bin',4)==(1,6,147400,17),'Exact unchanged Native/Sequence ABIs');entries=records.words('selected-table.bin',141);need(entries==tuple(x['entry']for x in p['selected_order']),'All138 physical selected slots');roots=records.words('registration-roots.bin',108);need(roots==expected_roots and set(roots)<set(entries),'All108 current callbacks remain exact');pages=records.words('extra-pages.bin',52);need(pages==tuple(page_map['extra'])and len(page_map['union'])==69,'Exact52external plusfixed17 source page inventory')
    for sequence in range(6):
     stem=f'sequence-{sequence}/';tags=struct.unpack_from('<12I',records.data(stem+'summary.bin'));need(tags[0]==sequence and tags[4:]==(1,141,0,0,0,0,0,0),'Actual complete persistent selected138 phase count');need(records.words(stem+'spi-fault.bin',6)==(0,0,0,0,1,1),'Existing SPI source complete')
     for phase,entry in enumerate(entries):
      prefix=stem+f'phase-{phase}';r=records.data(prefix+'.bin');need(len(r)==159716,'Whole phase ABI');w=struct.unpack_from('<9I',r);need(w[0]==sequence and w[2]==phase and w[4]==entry and not w[7],'Exact completed source phase identity')
      for point in ('before','after'):
       need(len(records.data(prefix+'-'+point+'-registry.bin'))==256,'Whole old registry endpoint');need(all(len(records.data(prefix+'-'+point+'-page-'+str(a)+'.bin'))==4096 for a in pages),'All entire current ordinary source pages')
     need(len(records.data(stem+'MFC/after/accesses.bin'))==113*24 and len(records.data(stem+'MFC/after/APIs.bin'))==4*352,'Actual new source causal/API extent');need(records.words(stem+'MFC/cleaned/resource-context.bin',12,'Q')[2:9]==(0,0,0,0,0,113,4),'Actual new resource source lifecycle closed');need(len(records.data(stem+'MFC-caller-hardware.bin'))==1632,'Whole actual full selected-table caller boundary');need(len(records.data(stem+'Widget/font-cleanup-caller-hardware.bin'))==1632,'Actual separate owned font cleanup boundary');
     for new in phase_map:
      widgetstem=stem+'Widget/root-'+str(new['root'])+'/';need(all(len(records.data(widgetstem+'carried-'+point+'/'+part+'.bin'))==size for point in ('before','after')for part,size in (('State',3504),('CPU',40),('FX',512),('stack',4096),('TIB',20))),'Whole current carried widget machine/stack/FS endpoint');need(all(len(records.data(widgetstem+'carried-'+point+'/provider-source-page-'+str(a)+'.bin'))==4096 for point in ('before','after')for a in (0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000)),'Complete owning formatter page endpoints');
     provider_stem=stem+'Widget/GDI-provider/';names=[x for x in records.entries if x.startswith(provider_stem)and x.endswith('/call.bin')];need(len(names)==164,'All149 actual source GDI plus15 actual manual font delete observations')
     for serial in range(164):
      local=provider_stem+str(serial)+'/';call=records.words(local+'call.bin',11,'Q');before=records.words(local+'before-identity.bin',9,'Q');after=records.words(local+'after-identity.bin',9,'Q');need(call[:2]==(1,serial)and call[2]<3 and call[3]==int(serial>=149)and before==after and before[:3]==(1,call[2],call[8])and before[6]==0x1000 and before[8]==0x1000000,'Complete exact real GDI call/owning-image relation');need(len(records.data(local+'before-entry64.bin'))==64 and records.data(local+'before-entry64.bin')==records.data(local+'after-entry64.bin'),'Whole current actual GDI entry64 sides');need(records.data(local+'before-path.txt')==records.data(local+'after-path.txt')and len(records.data(local+'before-sha256.txt'))==64 and records.data(local+'before-sha256.txt')==records.data(local+'after-sha256.txt'),'Whole current actual physical owner identities')
     need(1<=records.words(stem+'growth-replay-count.bin',1)[0]<=512,'Old genuine source growth bounded')
    need(records.data('COMPLETE.txt')==b'Six persistent141-root sequences and source growth/owned cleanup complete; fullM4 incomplete\n','Actual exact current completion')
    cases=[(0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7)]
    for seq,(repeat,cw,top)in enumerate(cases):
     prefix=f'sequence-{seq}/';C.host(records.data(prefix+'MFC-caller-hardware.bin'));C.host(records.data(prefix+'Widget/font-cleanup-caller-hardware.bin'))
     for phase,row in enumerate(p['selected_order']):
      raw=records.data(prefix+f'phase-{phase}.bin');tags=struct.unpack_from('<9I',raw);need(tags[:7]==(seq,repeat,phase,row['slot'],row['entry'],cw,top)and tags[7]==0,'All141 exact physical root/CW/TOP identities');need(struct.unpack_from('<2I',raw,148580)==(1,0),'Every141 source State seeded and no domain error');before=struct.unpack_from('<10I',raw,36);after=struct.unpack_from('<10I',raw,76);need(before[4]==0x20001800 and before[9]==row['entry']and after[4]==0x20001804 and after[9]==0x410a80,'Every genuine root CALL/RET frame')
      for side in('before','after'):need(len(records.data(prefix+f'phase-{phase}-{side}-constructor-global5F2000.bin'))==4096,'Additional entire carried constructor global5F2000 page')
     need(records.words(prefix+'selected/constructor-FS-source-scope.bin',2)==(0,0)and records.words(prefix+'cleaned/constructor-FS-source-scope.bin',2)==(0,0),'Balanced private current constructor source/FS scopes')
     result=C.validate_sequence(records,seq,constructor_roots,[v['root']for v in phase_map],source,cold,expectedcalls);raw12=RAW.validate(records,seq,p['selected_order']);budget=BUDGET.validate(records,seq,result);rows.append(dict(level=level,sequence=seq,phases=141,raw12=raw12,budget=budget,**result))
   finally:records.close();del records;closed=True
  need(len(rows)==12,'Both native levels and all six carried141 domains');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for q,h in pins.items():need(sha(q)==h,'Current141 structural conservation')
  d=dict(passed=passed,scope='Full141 strict structural/actual constructor source/frame/owner/resource/caller observations only; literal/provider/paired/refusal acceptance separate',execution_path=str(execution),execution_sha256=digest,build_sha256=BUILD,preparation_sha256=PREP,cases=rows,reader_closed=closed,initializer_credit=0,current141_acceptance=False,source_AFTER_seed=False,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=closed,sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
