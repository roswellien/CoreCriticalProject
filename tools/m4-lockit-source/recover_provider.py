"""Literal initialized Lockit provider path authenticated by genuine DLL load."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;need(not out.exists(),'Fresh initialized provider source');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact source provider input');pins[str(p)]=v;return p
 def emit(n,v):
  p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 rec=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/report.json','25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d').read_bytes());need(rec['passed'],'Frozen physical four-root source')
 observed=json.loads(pin(ROOT/'reports/m4-lockit-original/loader-execution-r1/observations.json').read_bytes());build=json.loads(pin(ROOT/'reports/m4-lockit-original/loader-build-r1/build.json').read_bytes());need(build['passed'],'Actual x86 loader build')
 for p,h in build['files'].items():pin(p,h)
 need(observed['passed']and observed['process_bits']==32 and observed['CRT_base']==0x78000000 and observed['MSVCP_base']==0x780c0000 and observed['post_DllMain_state']==2 and not observed['state_seeded']and not observed['constructor_called']and not observed['game_called'],'Authentic postDllMain initialized state before scratch/original constructor')
 need(Path(observed['CRT_path']).resolve()==(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve()and Path(observed['MSVCP_path']).resolve()==(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').resolve(),'Exact original loader module identities')
 need(observed['constructor']==0x7810a290 and observed['destructor']==0x7810a350,'Exact actual named Lockit exports');need(observed['critical_section'][1:5]==[0xffffffff,0,0,0],'Authentic unheld guest CS24B identity')
 graphs=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/provider-graphs.json').read_bytes());fast=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/initialized-provider-path.json').read_bytes());selected={}
 for entry,rows in((0x7810a290,fast['constructor_rows']),(0x7810a350,fast['destructor_rows'])):
  g=dict(graphs[str(entry)]);g.update(instructions=rows,direct_calls=[],unresolved_controls=[],FS_sites=[],FP_sites=[],research_terminal=None,initialized_state2_domain_only=True,cold_state0_and_contended_state1_admitted=False);selected[entry]=g
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 pe=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes());parserp=pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py');s=importlib.util.spec_from_file_location('lockit_provider_parser',parserp);parser=importlib.util.module_from_spec(s);s.loader.exec_module(parser)
 rows={r['pc']:r for g in selected.values()for r in g['instructions']};decoded=[]
 for r in sorted(rows.values(),key=lambda r:r['pc']):
  raw=bytes.fromhex(r['bytes']);off,_=pe.rva_range(r['pc']-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Every exact provider initialized-path byte');decoded.append(parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0])))
 inputs=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/provider-inputs.json').read_bytes());bycell={r['address']:r for r in inputs['provider_imports']};actualbycell={r['cell']:r for r in observed['imports']};apis=[]
 for site,slot,name,delta in((0x7810a30b,0x78146198,'EnterCriticalSection',-16),(0x7810a35e,0x78146184,'LeaveCriticalSection',-8)):
  need(bycell[slot]['symbol']['name']==name and actualbycell[slot]['symbol']==name and actualbycell[slot]['target']==actualbycell[slot]['resolved_export'],'Original named kernel32 cell resolves actual forwarded export')
  apis.append(dict(pc=site,IAT=slot,API=name,kind='call',raw_IAT=int.from_bytes(bytes.fromhex(bycell[slot]['raw']['initial_hex']),'little'),argument_DWORDs=1,void=True,argument=0x78145640,actual_resolved_target=actualbycell[slot]['target'],actual_owner_path=actualbycell[slot]['actual_owner_path'],entry_API_frame_delta=delta))
 emit('game-new-graphs.json',selected);emit('provider-graphs.json',selected);emit('fs-roots.json',[]);emit('API-contracts.json',apis);emit('instruction-contracts.json',dict(schema='mw34-Lockit-initialized-provider-source-v1',instructions=decoded,API_sites=apis,AFTER_machine_seed=False,condition='Actual original postDllMain state2, same privately associated MSVCP CS identity; serial balanced source calls',state_global=0x78145658,CS_address=0x78145640,CS_guest_bytes=24,CS_native_bytes=40,constructor_frame_delta=-16,destructor_frame_delta=-8,unadmitted_state0=True,unadmitted_state1=True))
 pin(__file__);pin(ROOT/'tools/analysis/pe.py');report=dict(passed=True,scope='Exact17 initialized provider rows authenticated by actual32-bit DLL loader beforeconstructor. Static COFF preparation pending; no root/runtime credit.',body_count=2,unique_instructions=len(rows),unique_bytes=sum(r['size']for r in rows.values()),actual_postDllMain_state=2,loader_observations_sha256=sha(ROOT/'reports/m4-lockit-original/loader-execution-r1/observations.json'),loader_build_sha256=sha(ROOT/'reports/m4-lockit-original/loader-build-r1/build.json'),provider_API_sites=apis,source_data_pages=[0x78145000,0x78146000],source_code_pages=[0x7810a000],ctor_RET_value='Original ECX in EAX',dtor_RET_value='VOID, preserves guest EAX through API seam',state_seeded=False,initialized_state2_domain_only=True,cold_state0_admitted=False,contended_state1_admitted=False,game_execution=False,native_execution=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),bodies=2,instructions=len(rows),bytes=report['unique_bytes'])))
if __name__=='__main__':main(sys.argv[1])
