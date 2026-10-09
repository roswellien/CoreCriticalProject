"""Read-only audit of the completed root BEFORE-only source-model proof.

No model imports/execution, native reruns, or candidate modifications occur.
"""
import ast, importlib.util, json, ntpath, re, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('own_mainargs_contract',Path(__file__).with_name('review.py'))
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ROOT,BASE=R.ROOT,R.BASE
FROZEN={
 'tools/m4-crt-entry-initterm-root/model.py':'b19863e5ab04f8a348c626601ce3086adfbcd8357b399eefb47c5439565707e1',
 'tools/m4-crt-entry-initterm-root/observe.py':'453b0032ac308b090d1b77438a10d8fa66ed32d13e979fb991d4536ce44d769f',
 'tools/m4-crt-entry-control-root/model.py':'da9c2cf73fdc0db5832412bd66f3fd128c4366cc70485ddf4d5bde30f687110f',
 'tools/m4-crt-entry-control-root/observe.py':'aaee1da9ef938d9d8bb176bb2b26944c02fcdf8f881447fe568b5f5d11056e60',
 'tools/m4-crt-entry-matherr-root/model.py':'5bd21ddfc1ffef390a88891f60821ff055c32d73610fba7740d1f94688e0da32',
 'tools/m4-crt-entry-matherr-root/observe.py':'8a55f96c298f19ff1ccbe6c24a449378064b678cea07da3fd6aa83a79a58445f',
 'tools/m4-crt-entry-data-review/observe.py':'6f65958d1c7603e4c508ef560dcc443437f0ab551319989f926723bcecbe486e',
 'tools/m4-crt-fdiv-independent/replay_model.py':'eb77c8cf6b0f533b2cd2b50b3ce6d3bbb2c26be2ea5e844278a45ca5cb297b35',
 'tools/m4-crt-fdiv-independent/native_model.py':'8eada91041660b2e3d149cc8df89c01c3a13c5e0d925b21f0bca0af69d2bed6b',
}
def text(p):return R.pin(p).read_text(encoding='utf-8-sig')
def read(p):return json.loads(text(p))
def main(proof_name,expected_hash,out_name):
 out=BASE/out_name;R.need(out.parent==BASE and out_name.startswith('independent-root-model-audit-')and not out.exists(),'New independent audit only');out.mkdir(parents=True)
 try:
  for p,h in {**R.FROZEN,**FROZEN}.items():R.pin(ROOT/p,h)
  proof=BASE/proof_name;rp=R.pin(proof/'report.json',expected_hash);report=read(rp);manifest=read(proof/'pins.json')
  execution=read(BASE/'root-execution-r1/execution.json');R.pin(BASE/'root-execution-r1/pins.json');R.need(execution['passed'],'Root fresh actual native execution completed')
  source=read(BASE/'independent-contract-r1/report.json');R.pin(BASE/'independent-contract-r1/pins.json');final=read(BASE/'independent-contract-r4/report.json');R.pin(BASE/'independent-contract-r4/pins.json');R.need(source['passed']and final['passed'],'Independent original and final source closure')
  mp=ROOT/'tools/m4-crt-mainargs-root/model.py';op=ROOT/'tools/m4-crt-mainargs-root/observe.py';model=text(mp);observer=text(op);R.pin(ROOT/'tools/m4-crt-mainargs-root/run.py')
  mt,ot=ast.parse(model),ast.parse(observer)
  for p in (mp,op):
   canonical=ntpath.normcase(ntpath.normpath(str(p)))
   matches=[h for k,h in manifest['files'].items()if ntpath.normcase(ntpath.normpath(k))==canonical];R.need(matches==[R.sha(p)],'Final proof binds stable current root source '+p.name)
  imports=[n for n in ast.walk(mt)if isinstance(n,(ast.Import,ast.ImportFrom))]
  names=[a.name for n in imports for a in n.names];R.need(not any(any(t in n for t in ('candidate','session','composition'))for n in names),'No candidate model import in root source interpreter')
  R.need("ROOT/'tools/m4-crt-entry-initterm-root/model.py'"in model and FROZEN['tools/m4-crt-entry-initterm-root/model.py']in model,'Original frozen source interpreter explicitly pinned')
  R.need(FROZEN['tools/m4-crt-entry-initterm-root/observe.py']in observer,'Frozen full16-page observer explicitly pinned')
  R.need("original[:24]"in observer and "payloads=[R.project(v) for v in original[:24]]"in observer,'Only original FDIV BEFORE corpus supplies positive input')
  R.need("writer_result(row,payload,wp,pp,gp,source)"in observer and 'final,memory,fx,control,level'in observer,'Entry model starts independently validated writer source result, not stopped mainargs native AFTER')
  R.need('entry.run();'in observer and 'compare(row,entry,phases)'in observer,'Expected source phases precede actual equality checks')
  R.need('self.args_write(address,value);self.r[\'esp\']=address'in model,'PUSH checked store before State ESP publication')
  R.need('target=self.args_operand(operands[0]);address=(self.r[\'esp\']-4)'in model and 'self.args_write(address,nxt);self.r[\'esp\']=address;self.args_pc=target;self.args_commit()'in model,'CALL source operand before checked store before ESP/PC publication')
  R.need('value=self.raw_load(address)'in model and 'value!=0x343b0:self.args_deny'in model,'Actual raw provider import identity denied before access receipt')
  R.need('self.raw_store(address,value);self.args_access(address,value,1)'in model and "value!=0:self.args_deny('Required nonzero startup mode"in model,'Mode56 required original global store recorded before domain denial')
  R.need('if self.raw_load(address)!=nxt:self.args_deny'in model,'Mode55 modified real internal return word checked after source CALL publication')
  R.need("self.args_event(4,pc,API_SLOT,target)"in model and "self.args_deny('Required KERNEL32.dll!GetModuleFileNameA remains unresolved',API_SLOT,API_PC)"in model,'Correct public fault site/IAT distinct from source raw target')
  R.need('self.runtime_cpu=struct.pack' in model and model.count('self.runtime_cpu=struct.pack')==1,'Runtime CPU projected only at actual game import; partial provider source State remains distinct')
  R.need("unused_early_args"in observer and 'control>=4'in observer,'Explicit early absent-schema distinct from later unused default-schema')
  R.need("M.API_PC,M.API_SLOT"in observer and "(4,M.SLOT,M.SLOT)"in observer,'Unresolved native import and causal Runtime catches have source-derived exact fault triples')
  R.need('whole_source_prefix_predicted=control!=43'in observer and 'artifact_specific_injected_operand=control==43'in observer and 'architectural_source_equivalence_credited=control!=43'in observer,'Inherited mode43 preserved as two artifact-specific injected operand fixtures only')
  R.need('D.equal(altered,files,'in observer and "('mainargs-provider.bin','mainargs-builder.bin')"in observer and 'for offset in (0,len(files[name])-1)'in observer,'Same shared equality validator rejects both ends of every new source identity')
  R.need(report['passed']and report['positive_records']==48 and report['causal_records']==120 and report['whole_State_bytes']==3504 and report['whole_FX_bytes']==512 and report['whole_pages']==16 and report['source_identity_bytes']==1140,'Complete matching source-proof schema')
  R.need(report['mainargs_accesses']==768 and report['mainargs_route_events']==192 and report['direct_host_boundary_pairs']==330,'Actual positive prefix and hardware observation counts')
  path=source['source_contract']['actual_instruction_path'];R.need(len(path)==19,'Fixed independent original prefix path')
  R.need({(p['level'],p['id'])for p in report['positives']}=={(l,i)for l in ('O0','O2')for i in range(24)}and len(report['positives'])==48,'Exactly48 unique source-positive rows')
  for p in report['positives']:R.need(p['mainargs_accesses']==16 and p['mainargs_routes']==4 and p['mainargs_source_PCs']==path,'Positive PC/access/route sequence independently original-source derived')
  R.need({(p['level'],p['control'])for p in report['causals']}=={(l,c)for l in ('O0','O2')for c in range(1,61)}and len(report['causals'])==120,'Exactly120 unique inherited/new causal rows')
  paths={49:[],50:path[:8],51:[],52:path,53:path[:6],54:path[:1],55:path[:8],56:path[:6],57:path[:7]+[0x7800ba71],58:path[:8],59:[],60:path[:9]}
  for p in report['causals']:
   if p['control']>=49:R.need(p['mainargs_source_PCs']==paths[p['control']]and p['whole_source_prefix_predicted']and p['terminal_retry'],'Each new fault PC-prefix derives original operand/injection order')
   if p['control']==43:R.need(not p['whole_source_prefix_predicted']and p['artifact_specific_injected_operand']and not p['architectural_source_equivalence_credited'],'No inherited mode43 overclaim')
  denials=report['observer_corruption_denials'];R.need(denials and all(v['rejected']for v in denials),'Recorded corruption checks all fail closed')
  pairs={(v['level'],v['control'],v['phase'])for v in denials if v.get('file')=='mainargs-provider.bin'}
  for level,control,phase in pairs:
   for name,last in [('mainargs-provider.bin',65),('mainargs-builder.bin',139)]:
    for offset in (0,last):R.need(any(v.get('level')==level and v.get('control')==control and v.get('phase')==phase and v.get('file')==name and v.get('offset')==offset for v in denials),'Every new source file beginning/end exercised against same equality')
  R.need({(l,c)for l,c,_ in pairs}=={(l,c)for l in ('O0','O2')for c in [0,*range(49,61)]},'Positive and all new causal identity corruption coverage')
  for n in('mainargs-host.ll','mainargs-guest.ll','normal_argv-host.ll','normal_argv-guest.ll'):R.pin(BASE/'recovery-r3'/n)
  R.pin(BASE/'preparation-r2/main_v2.inc');R.pin(BASE/'preparation-r2/mainargs_context.hpp');R.pin(BASE/'preparation-r2/mainargs_binding.inc');R.pin(ROOT/'tools/m4-crt-entry-initterm-root/model.py',FROZEN['tools/m4-crt-entry-initterm-root/model.py']);R.pin(Path(__file__))
  result=dict(passed=True,scope='Independent read-only source/model/observer audit of completed root proof; no root model or native rerun',root_model_sha256=R.sha(mp),root_observer_sha256=R.sha(op),root_proof_sha256=R.sha(rp),root_execution_sha256=R.sha(BASE/'root-execution-r1/execution.json'),positive_records=48,causal_records=120,new_prefix_source_PCs=19,new_prefix_accesses=16,new_prefix_routes=4,all_source_identity_bytes=1140,State_bytes=3504,separate_FX_bytes=512,whole_pages=16,partial_fault_order='Source operand read; checked PUSH/CALL memory store; ESP/PC publication; typed nested/import closure. Failed source store leaves pre-publication ESP.',early_controls1_3='Absent mainargs Context phases and absent default trace/job/reason files; old pre-context native schema',controls4_48='Exact unused default trace/job/reason with no new service phase; inherited source prefixes',inherited_mode43='Only two optimization-level artifact fixtures of deliberately alias-changing observer; no generalized x86/noalias equivalence',shared_equality_corruption_denials=len(denials),BEFORE_only=True,candidate_model_imported=False,native_AFTER_as_expected_seed=False,filename_OS_import_success=False,argument_environment_initialization_complete=False,ordinary_game_launched=False,native_rerun=False,model_rerun=False,whole_M4_complete=False,files=R.PINS)
 except Exception as e:result=dict(passed=False,error=str(e),traceback=traceback.format_exc(),files=R.PINS)
 p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');R.pin(p);(out/'pins.json').write_text(json.dumps(dict(files=R.PINS),indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],report_sha256=R.sha(p),bindings=len(R.PINS),error=result.get('error'))));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main(*sys.argv[1:]))
