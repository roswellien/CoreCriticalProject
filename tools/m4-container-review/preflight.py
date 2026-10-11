"""Independent physical seven-root contracts and bounded verification plan.

No constructor/DLL is executed. Static expectations are not execution credit.
"""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-container-review'/name;need(not out.exists(),'Fresh physical review');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable read');pins[str(p)]=v;return p
 def data(p,h=None):return json.loads(pin(ROOT/p,h).read_bytes())
 accepted=data('reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0');need(accepted['passed'],'Accepted109 parent')
 report=data('reports/m4-fs-next-plan/plan-r3/report.json','8a4131187d8357e6d2ec80262fc8bc0c1536d9cd0da7903ca02ab7e1d388239c')
 plan=data('reports/m4-fs-next-plan/plan-r3/plan.json',report['files'][str(ROOT/'reports/m4-fs-next-plan/plan-r3/plan.json')])
 loader=data('reports/m4-container-source/loader-identity-r2/report.json','f3c5a41e6afcb1c7373a911d5e20434f06c6eafee0cf7755a3fc372e93abd892');need(loader['passed'],'Actual original32 loader proof')
 recovery=data('reports/m4-container-source/recovery-r1/report.json');need(recovery['passed']and recovery['root_count']==7,'Exact new seven-root recovery')
 c=data('reports/m4-container-source/recovery-r1/instruction-contracts.json',recovery['files'][str(ROOT/'reports/m4-container-source/recovery-r1/instruction-contracts.json')])
 spec=importlib.util.spec_from_file_location('independent_container_physical_PE',pin(ROOT/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
 images={}
 for key,path,h in(('game','MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('mfc','local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('crt','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')):
  images[key]=PE.PEImage(pin(ROOT/path,h).read_bytes())
 def literal(key,pc,raw):
  pe=images[key];off=pe.rva_range(pc-pe.image_base,len(raw))[0];need(pe.read(off,len(raw))==raw,'Physical original row '+hex(pc))
 for row in c['instructions']:literal('game',row['pc'],bytes.fromhex(row['bytes_hex']))
 provider=data('reports/m4-fs-next-plan/plan-r3/physical-MFC540-rows.json',report['files'][str(ROOT/'reports/m4-fs-next-plan/plan-r3/physical-MFC540-rows.json')])
 null=data('reports/m4-fs-next-plan/plan-r3/physical-CRTfreeNULL-rows.json',report['files'][str(ROOT/'reports/m4-fs-next-plan/plan-r3/physical-CRTfreeNULL-rows.json')])
 for rows,key in((provider,'mfc'),(null,'crt')):
  for row in rows:literal(key,row['pc'],bytes.fromhex(row['bytes']))
 need(len(provider)==10 and sum(r['size']for r in provider)==22,'Exact borrowed540 integer closure')
 need(any(r['pc']==0x5f4020c4 and r['bytes']=='b854cb4c5f'for r in provider)and any(r['pc']==0x5f4020bc and r['bytes']=='8b00'for r in provider)and any(r['pc']==0x5f4020be and r['bytes']=='8906'for r in provider),'Borrowed value is one DWORD read and one object DWORD store; pointee not read')
 need(any(r['pc']==0x780013b6 and r['bytes']=='85f6'for r in null)and any(r['pc']==0x780013b8 and r['bytes']=='745c'for r in null)and any(r['pc']==0x78001419 and r['bytes']=='64890d00000000'for r in null),'Literal freeNULL tests ESI then restores same saved FS predecessor without HeapFree')
 pe=images['game'];imports={pe.image_base+s['iat_rva']:s for library in pe.imports()if library['library'].lower()=='mfc42.dll'for s in library['symbols']};exports={r['ordinal']:r for r in images['mfc'].exports()}
 for slot,raw,ordinal,target in((0x5bb454,0x8000021c,540,0x5f4020b4),(0x5bb4c8,0x80000339,825,0x5f401782)):
  need(imports[slot]['ordinal']==ordinal and pe.rva_u32(slot-pe.image_base)==raw and images['mfc'].image_base+exports[ordinal]['rva']==target,'Physical owning game ordinal and exact DLL target')
  observed=next(r for r in loader['bindings']if r['ordinal']==ordinal);need((observed['game_IAT'],observed['raw_game_IAT'],observed['actual_loader_export'])==(slot,raw,target),'Genuine original32 load joins exact physical named owner')
 raw_path=ROOT/'reports/m4-container-source/loader-identity-r2/raw-data-page.bin';loaded_path=ROOT/'reports/m4-container-source/loader-r1/loaded-data-page.bin'
 raw=pin(raw_path,loader['borrowed_data']['raw_page_sha256']).read_bytes();loaded=pin(loaded_path,loader['borrowed_data']['loaded_page_sha256']).read_bytes();need(len(raw)==len(loaded)==4096,'Both complete authentic branch-input pages')
 literal('mfc',0x5f4cc000,raw);offset=0xb54;need(raw[offset:offset+4]==loaded[offset:offset+4]==struct.pack('<I',0x5f4cecec),'Actual initialized borrowed scalar exactly agrees with physical input')
 diffs=[dict(offset=i,address=0x5f4cc000+i,raw=x,loaded=y)for i,(x,y)in enumerate(zip(raw,loaded))if x!=y];need(len(diffs)==167,'Every whole loader-vs-raw input difference retained')
 need(diffs==data('reports/m4-container-source/loader-identity-r2/page-differences.json',loader['files'][str(ROOT/'reports/m4-container-source/loader-identity-r2/page-differences.json')]),'Independent complete difference enumeration agrees')
 before=pin(ROOT/'tools/m4-fs-provider-review/observe109_v3.py','1a8f9c00b07cf7f661b5438606a871c78f936686e7fd7242f109c9ac9e0d405a').read_text();tree=ast.parse(before);pages=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='PAGES'for a in n.targets));extra=[p for p in c['source_data_pages']if p not in pages]
 inventory=data('reports/m4-container-source/recovery-r1/source-page-inventory.json');extra=[p for p in inventory['pages']if p not in pages];need(extra==[0x736000,0x5f4cc000],'Exact two additional source pages')
 controls=[
  dict(cause='ordinary-seven-root',requires='Genuine bootstrap/seven source CALLs, source positive/nullfree/borrowed frames, whole State/CPU/FX/ENV/pages, real owners, genuine cleanup'),
  dict(cause='game-825-IAT-identity',requires='Actual owning read-only game region temporarily writable only for intervention; original permissions restored; exact read-time raw target refusal before free dispatch'),
  dict(cause='game-540-IAT-identity',requires='Same explicit exact IAT intervention; exact540 thunk read-time refusal, no constructor object store'),
  dict(cause='borrowed-DWORD-corruption',requires='Actual owned provider-page mutation refuses whole-page guard; do not claim later read-time guard if unreachable'),
  dict(cause='borrowed-no-pointee-map',requires='Normal540 copy succeeds with no5F4CE000 mapping or dereference; exact borrowed scalar provenance'),
  dict(cause='nullfree-argument-corruption',requires='Actual NULL frame boundary with exact source zero argument; refusal before invented owner/API use; legitimate argument mutation distinguished from observer State guard'),
  dict(cause='nullfree-nested-chain',requires='Exact CRT12B FS install/save/restore inside active game frame, no native HeapFree/API/owner-generation side effect; literal EAX/ECX/flags retained'),
  dict(cause='container-capacity-or-publication-RO',requires='Fault at literal store; complete preceding owner writes/copies unchanged, existing fields retained'),
  dict(cause='string-copy-partial',requires='Actual committed copy prefix and untouched initial native padding, exact first refused address/source PC; no libc substitution'),
  dict(cause='owned-native-padding-corruption',requires='Full-width actual native backing intervention plus complete BEFORE/after bytes; exact whole backing refusal'),
  dict(cause='FS-install-or-restore-RO',requires='Exact normal active chain/root/record and genuine source prefix; preserve failed raw chain without invented unwind'),
  dict(cause='private-new-witness-mutation',requires='Each new borrowed/nullfree witness/provenance span actually mutated; full private observer guard plus exact one-word/raw mutation relation'),
  dict(cause='same-session-retry',requires='Every ordinary/fault scenario has zero additional source/API work and identical State/CPU/FX/ENV/fullpages/owners/ledger payloads on retry'),
  dict(cause='outside-hardware-and-destroy',requires='Authored caller NumericHostBoundary/ErrorBoundary encloses call and catch; exact hardware FX/ENV/LastError and real same-HANDLE HeapDestroy before/after/independent triplet'),
 ]
 (out/'controls-plan.json').write_text(json.dumps(controls,indent=2)+'\n');pin(out/'controls-plan.json')
 (out/'loader-input-differences.json').write_text(json.dumps(diffs,indent=2)+'\n');pin(out/'loader-input-differences.json');pin(__file__)
 result=dict(passed=True,scope='Independent physical source/import/loaded borrowed data preflight only; no constructor/freeNULL/native execution or initializer credit. Native raw-page input and original same-worker initialized-page input remain separate; no whole-page mask or prior-process machine seed.',game_rows=len(c['instructions']),borrowed_provider_rows=len(provider),literal_nullfree_rows=len(null),expected_registration_roots_unexecuted=88,expected_MFC_owners_unexecuted=50,expected_string_owners_unexecuted=19,expected_total_owners_unexecuted=70,new_pages=extra,whole_page_loader_differences=len(diffs),borrowed_value=0x5f4cecec,pointee_read=False,pointee_mapping_admitted=False,actual_initializer_credit=0,required_remaining='Fresh full116 original/native/source/paired and independent provider/controls gates',files=pins,physical_closure=verify_manifest(pins))
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
