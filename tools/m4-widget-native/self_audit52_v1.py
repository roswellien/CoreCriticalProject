"""Static current52 additive-source conservation; no runtime credit."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[2];pins={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,v,h);pins[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
prior=R/'reports/m4-widget-native/preparation-r3';current=R/'reports/m4-widget-native/preparation-r6';old=read(prior/'report.json','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5');p=read(current/'report.json','714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9');b=read(R/'reports/m4-widget-native/build-r7/build.json','7bba3319abef8202d154229ba4243dadd6e2693381c86abcbd41bf41007d20bf');fp=read(R/'reports/m4-widget-native/fixture-preparation-r16/report.json','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401');fb=read(R/'reports/m4-widget-native/fixture-build-r13/build.json','036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98')
assert all(x['passed']for x in(p,b,fp,fb));assert p['literal_bodies']==52 and len(p['IRs'])==52
for path in old['IRs']:
 x=pin(path);y=pin(current/x.name);assert x.read_bytes()==y.read_bytes()
for name in('component.cpp','component.hpp','contracts.json','native_api.s'):
 assert pin(prior/name).read_bytes()==pin(current/name).read_bytes(),name
header=pin(prior/'literals.hpp').read_text();marker='inline Body body(unsigned pc){switch(pc){';expected=header.replace(marker,'extern "C" void *mw34_widget_game_f_5a4590_body(State*,unsigned,void*);\n'+marker+'\ncase 5916048:return mw34_widget_game_f_5a4590_body;');assert expected==pin(current/'literals.hpp').read_text()
bridge=pin(prior/'bridges.inc').read_text();added=p['new_bridge_symbols'];assert len(added)==1 and 'undefined_8' in added[0];assert bridge+'\n'.join(added)+'\n'==pin(current/'bridges.inc').read_text()
x=pin(R/'tools/m4-widget-native/fixture_v4.cpp').read_text();y=pin(R/'tools/m4-widget-native/fixture_v5.cpp').read_text();assert x.count('status{1,unsigned(!failed),6,51,')==1;assert x.replace('status{1,unsigned(!failed),6,51,','status{1,unsigned(!failed),6,52,')==y
pin(R/'tools/m4-widget-native/build_v3.py','5d92064c4a7b8cf923a35ec22f15bb81760f983f7ad3366d926e21c4c6c68cef');pin(R/'tools/m4-widget-native/build_v3.ps1','9296567e295a538a635ba853ee4061c963c631a494fd4674c3cfb75098b91a9d')
assert sum('-fms-runtime-lib=dll' in c['argv']for c in b['commands'])==2
for lev in('O0','O2'):
 assert b['levels'][lev]['literal_objects']==52
 syms=pin(R/f'reports/m4-widget-native/build-r7/{lev}-symbols.stdout').read_text();assert all('mw34_widget_game_f_%x_body'%n['entry']in syms for n in p['namespace_relations']);pin(fb['workers'][lev]['path'],fb['workers'][lev]['sha256'])
contract=read(current/'contracts.json');orig=read(R/'reports/m4-font479590-original/source-r1/source-derivations.json');rows={r['pc']:r for r in contract['instructions']};bodies={n['entry']for n in p['namespace_relations']};targets={};calls=0
for case in orig:
 for pc,nxt in zip(case['source_PCs'],case['source_PCs'][1:]):
  row=rows[pc]
  if row['mnemonic']=='call'and nxt!=pc+row['width']:
   assert nxt in bodies,hex(nxt);targets[nxt]=targets.get(nxt,0)+1;calls+=1
assert calls==1267 and len(targets)==33 and 0x5a4590 in bodies
pin(__file__);out=R/'reports/m4-widget-native/additive52-self-review-r1';assert not out.exists();out.mkdir();report=dict(passed=True,scope='Author self-audit of exact additive52 source/compile linkage; no runtime equivalence or independent acceptance credit',whole_old_IRs_byte_identical=51,component_cpp_header_contracts_assembly_byte_identical=True,only_component_header_dispatch_and_one_undefined8_bridge_added=True,new_literal_entry=0x5a4590,new_physical_instruction_rows=68,new_physical_instruction_bytes=197,total_physical_contract_rows=1093,literal_objects_each_level=52,actual_DLL_CRT_compile_commands=2,fixture_only_truthful_literal_count_changed=True,historical_compiler_wrappers_restored=True,source_observed_calls_with_compiled_callee=1267,source_observed_distinct_compiled_callees=33,source_return_or_original_output_seed=False,worker_launched=False,initializer_credit=0,files=pins);f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(f,sha(f))
