"""Seal genuine32 loader observations against exact original PE imports/exports."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mfc-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original loader identity receipt');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact loader physical input');pins[str(p)]=v;return p
 probe=BASE/'loader-r2';observed=json.loads(pin(probe/'loader.json').read_text(encoding='utf-8-sig'));need(observed['passed']and observed['process_bits']==32,'Successful actual32 loader')
 spec=importlib.util.spec_from_file_location('loader_primary_PE',pin(ROOT/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
 crtpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');mfcpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');crt=P.PEImage(crtpath.read_bytes());mfc=P.PEImage(mfcpath.read_bytes())
 need(Path(observed['CRT_path']).resolve()==crtpath and Path(observed['MFC_path']).resolve()==mfcpath and observed['CRT_base']==crt.image_base==0x78000000 and observed['MFC_base']==mfc.image_base==0x5f400000,'Exact actually loaded staged paths/base identities')
 named={n:e for e in crt.exports()for n in e['names']};imports={mfc.image_base+s['iat_rva']:dict(library=g['library'],**s)for g in mfc.imports()for s in g['symbols']};rows=[]
 for q in observed['bindings']:
  slot=q['MFC_IAT_slot'];name=q['name'];need(name in('malloc','free')and imports[slot]['library'].lower()=='msvcrt.dll'and imports[slot]['name']==name,'Original named MFC dependency')
  expected=crt.image_base+named[name]['rva'];off,_=mfc.rva_range(slot-mfc.image_base,4);raw=struct.unpack_from('<I',mfc.data,off)[0]
  need(q['actual_loader_target']==q['exact_staged_CRT_named_export']==q['actual_owner_named_export']==expected and q['actual_owner_base']==q['region_allocation_base']==crt.image_base and Path(q['actual_owner_path']).resolve()==crtpath and q['region_state']==4096 and q['region_type']==0x1000000 and q['region_protect']in(0x20,0x40),'Actual loader-bound named export in exact staged committed executable owning image')
  off,_=crt.rva_range(expected-crt.image_base,32);need(bytes.fromhex(q['target_first32_hex'])==crt.data[off:off+32],'Actual loaded target bytes match physical original named export')
  rows.append(dict(**q,raw_bound_IAT=raw,loader_resolved_target=expected,owning_module_sha256=sha(crtpath),original_named_export=named[name],raw_bound_matches_loaded_target=raw==expected))
 ordinals={e['ordinal']:e for e in mfc.exports()};need(observed['MFC_allocator_export823']==mfc.image_base+ordinals[823]['rva']==0x5f401ea0 and observed['MFC_free_export825']==mfc.image_base+ordinals[825]['rva']==0x5f401782,'Actual loaded MFC exports correspond to exact physical ordinals')
 off,_=mfc.rva_range(0x98970,4);handler=struct.unpack_from('<I',mfc.data,off)[0];need(observed['MFC_initialized_handler']==handler==0xffffffff,'Exact observed post-DllMain handler state matches rawDWORD')
 for p in(probe/'probe.exe',probe/'probe.obj',probe/'compile.log',ROOT/'tools/m4-mfc-source/loader_probe.cpp',ROOT/'tools/m4-mfc-source/build_loader_v2.ps1',Path(__file__),Path(sys.executable)):pin(p)
 # Genuine original32 loader execution is already complete. Constructor,
 # allocator, destructor and stale raw-pointer execution receive no credit.
 report=dict(passed=True,schema='mw34-mfc-genuine-original32-loader-identity-v1',scope='Actual32 loader-resolved MFC named CRT malloc/free imports, exact loaded module/base/path/physical export identity and post-DllMain handler state; constructor/allocator/free bodies uncalled',observation=str(probe/'loader.json'),observation_sha256=sha(probe/'loader.json'),bindings=rows,MFC_base=0x5f400000,CRT_base=0x78000000,MFC_module_sha256=sha(mfcpath),MFC_allocator_export823=0x5f401ea0,MFC_free_export825=0x5f401782,MFC_handler=dict(address=0x5f498970,post_loader_value=handler,physical_raw_value=handler),original_loader_executed=True,MFC_DllMain_initialization_executed=True,game_functions_called=False,allocator_source_called=False,free_source_called=False,raw_bound_targets_executed=False,root_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
