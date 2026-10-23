"""Exact retained138 driver extension with same-reader constructor gates."""
from pathlib import Path
import json,ast,hashlib
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/validator-preparation-r4';out.mkdir();p=R/'tools/m4-startup138-original/validate_realloc_v1.py';s=p.read_text();ds=[]
 def edit(a,b,n=1):
  nonlocal s
  assert s.count(a)==n,(a,s.count(a),n);s=s.replace(a,b);ds.append(dict(old=a,new=b,count=n))
 edit("BASE=ROOT/'reports/m4-startup138-original'","BASE=ROOT/'reports/m4-original141'")
 edit(" def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))"," def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))")
 edit("from mfc_phase_v3 import observe as observe_mfc,constructor as observe_constructor", "from mfc_phase141_v1 import observe as observe_mfc,constructor as observe_constructor")
 edit("sys.path.insert(0,str(ROOT/'tools/m4-startup131-original'));", "sys.path.insert(0,str(ROOT/'tools/m4-141-consumer-review'));")
 edit('from widget_phase_realloc_v1 import Observer','from widget_phase141_v1 import Observer')
 edit('from mfc_transition_v1 import Transition','from mfc_transition141_v1 import Transition\nfrom named_loader141_v2 import prove as prove_named_loader\nfrom constructor_supplement141_v4 import observe as observe_constructor_supplement')
 a="  need(build==ROOT/'reports/m4-startup138-original/build-r5/build.json'and digest=='da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'and preflight_path==ROOT/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json'and preflight_digest=='eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c','Exact current admitted original138 worker only')"
 b="""  need(build==ROOT/'reports/m4-original141/build-r1/build.json'and digest=='088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b','Exact current compiled original141 worker only')
  admission=read(pin(preflight_path,preflight_digest));need(admission['passed'] and admission.get('original141_validator_admitted') is True and admission['files'].get(str(build))==digest,'ROOT independent final compiled observer/validator admission required before reader')
  for dependency,identity in admission['files'].items():pin(dependency,identity)
  need(admission['files'].get(str(Path(__file__).resolve()))==sha(Path(__file__).resolve()),'Actual validator code belongs to exact ROOT admission')""";edit(a,b)
 a="prep=Path(b['preparation']);p=read(pin(prep/'report.json',b['preparation_sha256']));need(p['passed']and p['record_bytes']==356992 and p['original_roots']==138 and b['preparation_sha256']=='9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161','Exact original138 ABI/order');"
 b="""prep=Path(b['preparation']);current=read(pin(prep/'report.json',b['preparation_sha256']));need(current['passed']and current['Record_bytes']==356992 and current['root_count']==141 and b['preparation_sha256']=='7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8','Exact actual compiled original141 ABI/order');p=read(pin(ROOT/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'));need(p['original_roots']==138 and p['record_bytes']==356992 and current['callback_count']==111 and current['phases']==846,'Retained original138 physical fixed/extra page schema plus exact additive141 geometry');p['files']={**p.get('files',{}),**current['files']};""";edit(a,b)
 edit("need(len(p['order'])==138 and p['order'][13]['entry']==0x5ae3e4 and", "need(len(p['order'])==141 and [p['order'][i]['entry']for i in(13,14,15,39)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40] and")
 edit("not in(0x5ae3e4,0x4b64f0,", "not in(0x4103f0,0x410440,0x459b40,0x5ae3e4,0x4b64f0,")
 edit("STORAGE_ROOT/'reports/m4-startup138-original'", "STORAGE_ROOT/'reports/m4-original141'",3)
 edit("header[:8]==b'MW4J138O'", "header[:8]==b'MW4J141O'")
 edit('(1,6,138,828,43,356992)','(1,6,141,846,43,356992)')
 edit("need(len(callback_byentry)==108 and tuple(order[i]['entry']for i in WIDGET_PHASES)==WIDGET_ROOTS,'All108 literal callbacks and sorted seven-root chronology')", """need(len(callback_byentry)==108 and tuple(order[i]['entry']for i in WIDGET_PHASES)==WIDGET_ROOTS,'All108 inherited literal callbacks and current sorted seven-root chronology')
   for row in read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json')['roots']:
    need(row['entry']not in callback_byentry and row['entry']in(0x4103f0,0x410440,0x459b40),'Distinct three physically recovered constructor callbacks');callback_byentry[row['entry']]=row['callback']
   need(len(callback_byentry)==111,'All111 physical source callbacks')""")
 edit("prelaunch['build_sha256']==digest and", "prelaunch['original141_validator_admitted']is True and")
 edit("obs=read(Path(preflight_path).parent/'compiled-observers.json');resolutions={}", "obs=read(ROOT/'reports/m4-original141/root-compiled-review-r1/physical-links.json');resolutions={}")
 edit("row['family']=='whole-ASM'and row['symbol']==", "row['symbol']==",2)
 edit("need(len(fs_bindings)==93", "need(len(fs_bindings)==108")
 a=s[s.index("   transition_receipt=read(pin("):s.index('   widget=Observer',s.index("   transition_receipt=read(pin("))]
 b="""   declaration=read(pin(ROOT/'reports/m4-original141/transition-preparation-r1/patch-declarations.json'))
   shim_addresses=[resolutions['_registry_API_'+str(i)]for i in range(8)]
   crt_image=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
   patches,named_loader=prove_named_loader(records,PEImage,pin,shim_addresses,crt_image,declaration);transition=Transition(patches)
   target=out/'current-named-CRT-inputs.json';target.write_text(json.dumps(named_loader,indent=2)+'\\n');pin(target)
""";edit(a,b)
 edit("struct.pack('<108I'", "struct.pack('<111I'")
 edit("counts['phases']==828", "counts['phases']==846")
 for a,b in [('==4968','==5076'),('==114264','==116748'),('==105984','==108288'),('==55896','==57120')]:edit(a,b,2 if a=='==4968' else 1)
 edit("   observe_constructor(records,out,pin,counts,constructor_artifacts)", """   observe_constructor(records,out,pin,counts,constructor_artifacts)
   spec=importlib.util.spec_from_file_location('current_constructor_input_phase',pin(ROOT/'tools/m4-138-validation-review/constructor_input_capture_phase_v1.py'));ctor_helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(ctor_helper)
   supplemental=observe_constructor_supplement(records,prep,order,pages,callback_byentry,counts,pin,read,ctor_helper,shim_addresses)
   for label,value in supplemental.items():
    target=out/('supplement-'+label+'.json');target.write_text(json.dumps(value,indent=2)+'\\n');pin(target)""")
 edit("pin(Path(__file__).resolve().parent/'widget_phase_realloc_v1.py');pin(Path(__file__).resolve().parent/'mfc_transition_v1.py');", "pin(Path(__file__).resolve().parent/'widget_phase141_v1.py');pin(Path(__file__).resolve().parent/'mfc_transition141_v1.py');pin(Path(__file__).resolve().parent/'mfc_phase141_v1.py');pin(Path(__file__).resolve().parent/'named_loader141_v2.py');pin(Path(__file__).resolve().parent/'constructor_supplement141_v4.py');")
 edit('callbacks=108,counts=counts','callbacks=111,counts=counts')
 edit("scope='Actual original138 six persistent relative-order sequences with every inherited131 observation check plus current GDI/FPS selectors, complete69source/64CRT inputs, actual font occurrences and108 literal callback schedule; independent literal and native proofs remain separate'", "scope='Actual original141 six persistent relative-order sequences, all retained original138 observations plus full constructor input/ownership/body/frame/getter/cleanup gates on one reader; whole69 source/64 CRT pages plus5F2000,111 callbacks. Literal native proofs and accepted credit remain separate'")
 reverse=s
 for d in reversed(ds):assert reverse.count(d['new'])==d['count'],d['new'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==p.read_text();q=R/'tools/m4-141-consumer-review/validate_original141_v4.py';assert not q.exists();q.write_text(s);ast.parse(s)
 (out/'driver-deltas.json').write_text(json.dumps(ds,indent=2)+'\n');print(len(ds),hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main()
