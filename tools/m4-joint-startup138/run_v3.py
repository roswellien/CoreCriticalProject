"""Exact admitted full138 writer/strict structural run; semantic gates separate."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(build,digest,review,review_sha,name):
 out=R/'reports/m4-joint-startup138-root'/name;need(not out.exists(),'Fresh full138 execution');out.mkdir(parents=True);pins={};rows=[];passed=False;closed=True;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact current '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable current input');pins[str(p)]=v;return p
 try:
  a=json.loads(pin(review,review_sha).read_bytes());b=json.loads(pin(build,digest).read_bytes());p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());need(a['passed']and b['passed']and p['passed'],'Current complete prelaunch/build/preparation');need(a['build_sha256']==digest and a['preparation_sha256']==b['preparation_sha256'],'Exact full138 execution admission');need(len(p['selected_order'])==138 and p['selected_order'][13]=={'entry':0x5ae3e4,'slot':0x5e0040},'Exact138 slot13 input');parent_path=R/'reports/m4-joint-startup131/preparation-r1/report.json';old=json.loads(pin(parent_path,'2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes());prepdir=Path(b['preparation']).parent;phase_map=json.loads(pin(prepdir/'widget-phase-map.json').read_bytes());page_map=json.loads(pin(prepdir/'source-page-union.json').read_bytes());newroots=[x['root']for x in phase_map];need(len(newroots)==7 and [x for x in p['selected_order']if x['entry']not in newroots]==old['selected_order'],'All131 chronology unchanged');registration_text=pin(prepdir/'registration_contract.hpp').read_text();import re;expected_roots=tuple(int(v,16)for v in re.search(r'registration_roots\{([^}]+)',registration_text)[1].split(','));need(len(expected_roots)==108,'Exact108 source callback inventory')
  for q,h in b['files'].items():pin(q,h)
  sources=[pin(R/f,h)for f,h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')]];pin(__file__);pin(sys.executable)
  path=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('full131_strict_canonical',path);DS=importlib.util.module_from_spec(spec);spec.loader.exec_module(DS)
  for level in ('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');args=list(map(str,[worker,*sources,capture]));launched+=1;st=run_stage(args,stage,timeout_seconds=420,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));print(json.dumps(dict(level=level,stage_passed=st['passed'])),flush=True);need(st['passed'],'Actual full138 worker terminal '+level)
   records=DS.DirectSet(capture/'transport.json',pin);closed=False
   try:
    need(records.words('native-header.bin',6)==(1,6,138,828,17,159716)and records.words('sequences-header.bin',4)==(1,6,147400,17),'Exact unchanged Native/Sequence ABIs');entries=records.words('selected-table.bin',138);need(entries==tuple(x['entry']for x in p['selected_order']),'All138 physical selected slots');roots=records.words('registration-roots.bin',108);need(roots==expected_roots and set(roots)<set(entries),'All108 current callbacks remain exact');pages=records.words('extra-pages.bin',52);need(pages==tuple(page_map['extra'])and len(page_map['union'])==69,'Exact52external plusfixed17 source page inventory')
    for sequence in range(6):
     stem=f'sequence-{sequence}/';tags=struct.unpack_from('<12I',records.data(stem+'summary.bin'));need(tags[0]==sequence and tags[4:]==(1,138,0,0,0,0,0,0),'Actual complete persistent selected138 phase count');need(records.words(stem+'spi-fault.bin',6)==(0,0,0,0,1,1),'Existing SPI source complete')
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
    need(records.data('COMPLETE.txt')==b'Six persistent138-root sequences and source growth/owned cleanup complete; fullM4 incomplete\n','Actual exact current completion');rows.append(dict(level=level,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture/'transport.json'),logical_files=len(records.entries),payload_bytes=records.value['payload_bytes'],elapsed_seconds=st['elapsed_seconds']));print(json.dumps(dict(level=level,structural_passed=True)),flush=True)
   finally:records.close();del records;closed=True
   for q,h in pins.items():need(sha(q)==h,'All successful current physical inputs stable')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual current selected138 + source growth/cleanup structural gate only; independent complete source/provider/paired/caller and genuine domains required',build_path=str(build),build=str(build),build_sha256=digest,admission_review=str(review),admission_review_sha256=review_sha,levels=rows,files=pins,native_executed=bool(launched),all_workers_terminal=True,all_bounded_readers_closed=closed,initializer_credit=0,current138_acceptance=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
