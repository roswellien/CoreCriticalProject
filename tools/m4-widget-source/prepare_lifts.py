"""Additive bounded widget source preparation; no runtime admission."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-widget-source'
PINS={}
def need(v,t):
 if not v:raise ValueError(t)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture payload');a=sha(p);need(h is None or a==h,'Exact physical source input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=B/name;need(not out.exists(),'Fresh widget lift preparation');out.mkdir(parents=True)
 acceptance=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa');need(acceptance['passed'],'Current accepted130 parent')
 dispatch=read(B/'dispatch-r1/report.json','ee96052d75b9f459bcb1a96953e7130bbb98125c1d57c76fa7ed8ada9c415375');need(dispatch['passed'],'Exact dispatch source preparation')
 graphs={int(e):g for e,g in read(B/'dispatch-r1/game-bound-graphs.json').items()}
 native=read(R/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 old={};reused={}
 for p,h in native['entry_objects'].items():
  m=re.search(r'(?:^|[/\\])(?:f_|game_)([0-9a-f]+)-O([02])\.obj$',p)
  if m:old.setdefault(int(m[1],16),{})[m[2]]=dict(path=p,sha256=h)
 new={e:g for e,g in graphs.items()if e not in old}
 need(len(new)==39,'39 distinct new literal body entries relative accepted130 native object inventory')
 for e in sorted(set(graphs)&set(old)):
  need(set(old[e])=={'0','2'},'Both existing optimization object identities')
  for o in old[e].values():pin(o['path'],o['sha256'])
  reused[e]=old[e]
 rows={r['pc']:r for g in graphs.values()for r in g['instructions']};need(not any(g['FP_sites']for g in graphs.values()),'Current integer-only widget graph')
 regs=read(B/'recovery-r2/registration-roots.json');roots=[]
 for reg,obj in zip(regs,(0x5f4d78,0x5fc838,0x731ac0,0x736130,0x736328)):
  roots.append(dict(entry=reg['root'],slot=reg['slot'],object=obj,registration=reg,measured=False))
 contracts=read(B/'recovery-r2/instruction-contracts.json');all_normal_contracts=list(contracts['instructions']);known={r['pc']for r in all_normal_contracts}
 import importlib.util
 path=pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py');s=importlib.util.spec_from_file_location('widget_operand_contract',path);P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
 for pc,r in sorted(rows.items()):
  if pc in known:continue
  raw=dict(pc=pc,width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]);all_normal_contracts.append(P.instruction_contract(raw))
 all_normal_contracts.sort(key=lambda r:r['pc'])
 data=dict(schema='mw34-widget-literal-source-v1',instructions=all_normal_contracts,selected_roots=roots,source_indirect_contracts=read(B/'dispatch-r1/source-indirect-contracts.json'),source_array_contracts=read(B/'dispatch-r1/source-array-contracts.json'),source_code_pages=sorted({pc&~4095 for pc in rows}),observed_data_pages=None,current_zero_font_registry_required=True,nonzero_font_registry_admitted=False,format_string_nonnull_path_admitted=False,callback_failure_unwind_admitted=False,AFTER_machine_seed=False)
 payloads={'game-new-graphs.json':new,'game-reused-objects.json':reused,'fs-roots.json':roots,'instruction-contracts.json':data}
 for n,d in payloads.items():p=out/n;p.write_text(json.dumps(d,indent=2)+'\n');pin(p)
 parent=pin(R/'tools/m4-next-source/lift.py');code=parent.read_text()
 code=code.replace("ROOT/'reports/m4-next-source/recovery-r1'","ROOT/'reports/m4-widget-source/lift-preparation-r1'")
 code=code.replace("99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb",'PREPARATION_HASH')
 code=code.replace("ROOT/'reports/m4-next-source'/name","ROOT/'reports/m4-widget-source'/name")
 code=code.replace("need(not g['unresolved_controls'],'Game source graph closed with literal FS0 only');", "need(not g['unresolved_controls'] or (entry==0x5ac210 and {u['pc']for u in g['unresolved_controls']}=={0x5ac24b}), 'Only retained reverse-destructor callback frontier; no admission');")
 code=code.replace("root_count=4,","root_count=5,").replace("undefined_calls=len(re.findall(r'call i8 @__remill_undefined_8\\(',baseline.read_text()))", "undefined_calls=len(re.findall(r'call (?:zeroext )?i8 @__remill_undefined_8\\(',baseline.read_text()))")
 # Host bridge identity matches the accepted native dispatcher ABI. This
 # preparatory compiler accepts the finite indirect callback boundary only;
 # it does not grant target domains, resource mapping or reverse unwinding.
 code=code.replace('"""Literal game callback-registration bodies; source preparation, no admission."""','"""Widget exact literal source compilation; no execution or admission."""')
 template=out/'lift-template.py';template.write_text(code);pin(template)
 pin(__file__)
 report=dict(passed=True,scope='Exact five-widget source/COFF preparation and accepted object reuse only; no GDI, FS, indirect instance, constructor-array or cleanup runtime admission',accepted_parent_sha256=sha(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json'),dispatch_sha256=sha(B/'dispatch-r1/report.json'),counts=dict(roots=5,new_literal_entries=39,reused_literal_entries=10,reused_objects=20,instructions=len(rows),bytes=sum(r['size']for r in rows.values()),prospective_added_registrations=5),new_entries=sorted(new),reused_entries=sorted(reused),retained_unadmitted_reverse_callback_PC=0x5ac24b,original_executed=False,native_executed=False,initializer_credit=0,files=PINS)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');h=sha(p)
 dest=R/'tools/m4-widget-source/lift.py';need(not dest.exists(),'Fresh additive widget compiler');dest.write_text(code.replace('PREPARATION_HASH',h))
 print(json.dumps(dict(passed=True,sha256=h,counts=report['counts'],lift_tool_sha256=sha(dest))))
if __name__=='__main__':main(sys.argv[1])
