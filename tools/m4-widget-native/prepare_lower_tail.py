"""Recover the actual backward normal tail omitted by the prior entry lift."""
from pathlib import Path
import ast, copy, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh lower-tail compilation preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact actual bounded input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 failed=read(R/'reports/m4-widget-native/fixture-execution-r3/report.json','c85aca55ca4f63aea2bf3b12425ac02c9e2e4eca7bce12030df7875360fc7141');need(not failed['passed']and failed['all_workers_terminal'],'Actual failed first four complete/fifth diagnostic run is closed')
 cpu=pin(R/'reports/m4-widget-native/fixture-execution-r3/O0/phase-4/root-5924592/fault/CPU.bin');import struct;need(struct.unpack('<10I',cpu.read_bytes())[9]==0x5a4590,'Actual missing target is precise lower-address constructor tail')
 source=read(R/'reports/m4-font479590-original/source-r1/report.json','7a5b070228618400a1a4524b4df4214226f12c2570bcff9775fc6416265c4e9b');rows=read(R/'reports/m4-font479590-original/source-r1/source-derivations.json',source['files'][str((R/'reports/m4-font479590-original/source-r1/source-derivations.json').resolve())]);normal=rows[4];need(normal['root']==0x5a66f0 and normal['source_PCs'][:4]==[0x5a66f0,0x5a6700,0x5a6705,0x5a4590],'Genuine physical normal chronological CALL/JMP/lower-tail path')
 original=read(R/'reports/m4-widget-source/lift-preparation-r1/game-new-graphs.json');g=copy.deepcopy(original[str(0x5a6700)]);g['entry']=0x5a4590;g['instructions']=[v for v in g['instructions']if v['pc']not in(0x5a6700,0x5a6705)];need(len(g['instructions'])==68 and min(v['pc']for v in g['instructions'])==0x5a4590,'Exact original graph lower tail, only two trampoline instructions excluded')
 contract=read(R/'reports/m4-widget-native/preparation-r3/contracts.json');by={v['pc']:v for v in contract['instructions']}
 import importlib.util
 pe_path=pin(R/'tools/analysis/pe.py');sp=importlib.util.spec_from_file_location('widget_lower_tail_PE',pe_path);M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=M.PEImage(game.read_bytes())
 for v in g['instructions']:
  off,_=pe.rva_range(v['pc']-pe.image_base,v['size']);need(pe.data[off:off+v['size']]==bytes.fromhex(v['bytes'])==bytes.fromhex(by[v['pc']]['bytes_hex']),'Every unchanged lower-tail physical instruction')
 need(not g['unresolved_controls']and not g['FP_sites'],'Exact finite integer lower tail retains prior source graph obligations')
 for f,v in [('game-new-graphs.json',{str(0x5a4590):g}),('fs-roots.json',[]),('normal-lower-tail-path.json',dict(source_root=0x5a66f0,source_prefix_path=normal['source_PCs'][:4],all_tail_PCs=[v['pc']for v in g['instructions']],actual_failed_target=0x5a4590,opaque_output_seed=False))]:p=out/f;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 template=pin(R/'tools/m4-widget-source/lift.py');s=template.read_text().replace("ROOT/'reports/m4-widget-source/lift-preparation-r1'","ROOT/'reports/m4-widget-native/lower-tail-preparation-r1'").replace('b1778f7359075bae0c6c2afa0f5745b864b481f2e762dce64b385bb16c9a01dd','CURRENT_LOWER_TAIL_SHA').replace("ROOT/'reports/m4-widget-source'/name","ROOT/'reports/m4-widget-native'/name").replace('root_count=5,','root_count=0,');need('CURRENT_LOWER_TAIL_SHA'in s,'Exact static compiler preparation digest replaced');ast.parse(s);p=out/'lift-template.py';p.write_text(s);pin(p);pin(__file__)
 report=dict(passed=True,scope='Exact actual normal backward constructor-tail recovery and compile preparation; no new target execution or equivalence credit',counts=dict(new_bodies=1,physical_instruction_rows=68,physical_instruction_bytes=sum(v['size']for v in g['instructions'])),entry=0x5a4590,prior_failed_execution_sha256=sha(R/'reports/m4-widget-native/fixture-execution-r3/report.json'),existing_source_contract_rows_unchanged=1093,AFTER_or_result_seed=False,worker_executed=False,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');h=sha(p);dest=R/'tools/m4-widget-native/lift_lower_tail.py';need(not dest.exists(),'Fresh tail compiler');dest.write_text(s.replace('CURRENT_LOWER_TAIL_SHA',h));print(json.dumps(dict(passed=True,path=str(p),sha256=h,entry=hex(g['entry']),rows=68)))
if __name__=='__main__':main(sys.argv[1])
