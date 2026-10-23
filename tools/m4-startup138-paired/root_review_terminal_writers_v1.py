"""ROOT independent terminal source-writer joins; no capture reader."""
from pathlib import Path
import hashlib,json,importlib.util
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
out=R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r1';need(not out.exists(),'Fresh ROOT terminal writer review');out.mkdir(parents=True);pins={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical source identity '+str(p));pins[str(p)]=v;return p
def read(p,h):return json.loads(pin(p,h).read_bytes())
prep=read(R/'reports/m4-startup138-paired/widget-terminal-writer-preparation-r1/report.json','1e00221663b55031927068748c2d91b27b2f2c7e866e22439ec45f86c1f06b17')
prepath=R/'reports/m4-startup138-paired/widget-terminal-writer-preflight-r1/report.json'
pre=read(prepath,'89eb78351636acf5e442681cf781dd82704ca59df4469aa13cc31683286246b7')
for p,h in {**prep['files'],**pre['files']}.items():pin(p,h)
old=(R/'tools/m4-startup138-paired/widget_relations_v7.py').read_text();new=(R/'tools/m4-startup138-paired/widget_relations_v8.py').read_text()
delta=json.loads((R/'reports/m4-startup138-paired/widget-terminal-writer-preparation-r1/exact-delta.json').read_bytes());inverse=new
for a,b in reversed(delta):need(inverse.count(b)==1,'Unique finite helper delta');inverse=inverse.replace(b,a)
need(inverse==old,'Whole helper inverse; all birth and cleanup relations retained')
def artifact(report,label):
 v=json.loads(report.read_bytes());p=report.parent/label;return json.loads(pin(p,v['files'][str(p)]).read_bytes())
ori=artifact(R/'reports/m4-startup138-original/widget-complete-source-r1/report.json','source-derivations.json')
nat=artifact(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','Widget-source-derivations.json')
relations=artifact(prepath,'source-terminal-relations.json')
need(len(relations)==84 and len(ori)==42 and len(nat)==84,'Complete current branch matrix')
fields=zero=font=0
for r in relations:
 o=next(x for x in ori if (x['sequence'],x['root'])==(r['sequence'],r['root']))
 n=next(x for x in nat if (x['level'],x['sequence'],x['root'])==(r['level'],r['sequence'],r['root']))
 for t in r['terminal_handle_field_source_writers']:
  addr=t['address'];last=[]
  for source in (o,n):
   writes=[(i,x)for i,x in enumerate(source['source_accesses'])if x[4] and x[1]<addr+4 and addr<x[1]+x[3]]
   need(writes,'Own source field has actual writer');i,x=writes[-1]
   need(i==t['source_access_index'] and x[0]==t['PC'] and x[1]==addr and x[3:]==[4,1],'Independent last overlapping write, exact whole DWORD')
   last.append(x[2])
  need(last==[t['original'],t['native']],'Both own source terminal values retained')
  if t['PC']==0x5a0645:need(last==[0,0] and t['source_zero_clear'],'Literal complete zero clear');zero+=1
  else:
   need(t['PC']==0x5a0753 and not t['source_zero_clear'],'All actual positive terminal fields are source font stores')
   births=[b for b in r['typed_handle_source_stores']if b['source_access_index']==t['source_access_index'] and b['address']==addr]
   need(len(births)==1 and [births[0]['original'],births[0]['native']]==last,'Exact API-associated terminal font birth');font+=1
  fields+=1
need((fields,zero,font)==(804,624,180),'Current measured terminal source domain')
pepath=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('root_terminal_PE',pepath);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
imagepath=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');image=P.PEImage(imagepath.read_bytes());start,end=image.rva_range(0x5a0645-0x400000,10);need(image.data[start:end].hex()=='c7865802000000000000','Authentic PE literal MOV DWORD [ESI+258],0')
pin(__file__);value=dict(passed=True,independent_review=True,scope='Exact four helper source edits and independent final overlapping writer in both current source branches; full raw pairing still required',source_cases=84,terminal_fields=fields,source_zero_terminal_fields=zero,source_font_terminal_fields=font,API_birth_and_font_cleanup_rules_unchanged=True,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
p=out/'report.json';p.write_text(json.dumps(value,indent=2)+'\n');print(sha(p))
