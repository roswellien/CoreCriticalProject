"""Independent original import/export table and raw bound-pointer audit."""
import hashlib,importlib.util,json,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise RuntimeError(w)
def main(name):
 out=ROOT/'reports/m4-strings-native'/name;need(re.fullmatch('next-mfc-linkage-r[1-9][0-9]*',name) and not out.exists(),'Fresh independent linkage audit');pins={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Original physical file identity');pins[str(p)]=v;return p
 parser_path=pin(ROOT/'tools/m4-crt/recover_provider.py');spec=importlib.util.spec_from_file_location('independent_mfc_linkage',parser_path);R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
 mfcpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');crtpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');mfc=R.PE(mfcpath,sha(mfcpath));crt=R.PE(crtpath,sha(crtpath))
 imports=mfc.imports();exports=crt.exports();rows=[]
 directory,size=struct.unpack_from('<II',mfc.bytes,mfc.opt+104);descriptors=[]
 for n in range(size//20):
  rva=directory+n*20;fields=struct.unpack('<5I',mfc.read(rva,20))
  if not any(fields):break
  lookup,timestamp,chain,library,iat=fields;descriptors.append(dict(lookup_RVA=lookup,timestamp=timestamp,forwarder_chain=chain,library=mfc.text(library),IAT_RVA=iat,descriptor_RVA=rva,descriptor_file_offset=mfc.offset(rva,20),descriptor_hex=mfc.read(rva,20).hex()))
 descriptor=[d for d in descriptors if d['library'].lower()=='msvcrt.dll'];need(len(descriptor)==1,'One exact MSVCRT descriptor');descriptor=descriptor[0]
 for slot,name in [(0x5f49814c,'malloc'),(0x5f498148,'free')]:
  found=[i for i in imports if i['iat']==slot];need(found==[{'library':'MSVCRT.dll','iat':slot,'name':name}],'Independent import name and IAT agree')
  n=(slot-mfc.base-descriptor['IAT_RVA'])//4;lookup_rva=descriptor['lookup_RVA']+4*n;name_rva=struct.unpack('<I',mfc.read(lookup_rva,4))[0];need(mfc.text(name_rva+2)==name,'Physical original lookup names exact dependency')
  current=exports[name];raw=struct.unpack('<I',mfc.read(slot-mfc.base,4))[0]
  rows.append(dict(name=name,slot=slot,slot_file_offset=mfc.offset(slot-mfc.base,4),raw_IAT_hex=mfc.read(slot-mfc.base,4).hex(),raw_bound_target=raw,lookup_RVA=lookup_rva,lookup_hex=mfc.read(lookup_rva,4).hex(),hint_name_RVA=name_rva,hint=struct.unpack('<H',mfc.read(name_rva,2))[0],hint_name_hex=mfc.read(name_rva,len(name)+3).hex(),current_staged_export=current,raw_equals_current_named_export=raw==current['address'],current_export_file_offset=crt.offset(current['rva'],12),current_export_first12_hex=crt.read(current['rva'],12).hex(),raw_pointer_first12_in_current_DLL_hex=crt.read(raw-crt.base,12).hex(),actual_loader_bound_target_observed=False))
 prior=pin(ROOT/'reports/m4-strings-native/next-mfc-r1/report.json','112b31d1cb62f42756a7ae486bb174c474ea5049721f6084c57f5b701e611daf');data=json.loads(prior.read_bytes())
 need(all(any(r['slot']==old['slot'] and r['raw_bound_target']==old['raw_bound_IAT'] and r['current_staged_export']['address']==old['current_exact_staged_CRT_export'] for r in rows)for old in data['named_CRT_bindings']),'Independent parser agrees with prior bounded source report')
 bound_RVA,bound_bytes=struct.unpack_from('<II',mfc.bytes,mfc.opt+96+11*8)
 bound=None
 if bound_RVA and bound_bytes:
  need(bound_bytes<=4096,'Finite raw bound import directory');bound=dict(RVA=bound_RVA,bytes=bound_bytes,raw_hex=mfc.read(bound_RVA,bound_bytes).hex())
 out.mkdir(parents=True);pin(Path(__file__));pin(Path(sys.executable))
 result=dict(passed=True,scope='Independent existing physical PE reader proves original named import and staged export addresses only; no load, import resolution, capture or native execution',MFC_base=mfc.base,CRT_base=crt.base,MFC_COFF_timestamp=mfc.u32(mfc.pe+8),CRT_COFF_timestamp=crt.u32(crt.pe+8),CRT_import_descriptor=descriptor,raw_bound_import_directory=bound,bindings=rows,raw_IAT_targets_match_exact_staged_named_exports=False,reuse_of_current_CRT_bodies_requires_explicit_source_import_relocation=True,observed_original_loader_binding=False,assumption='MSVCRT.dll named imports identify intended dependency; exact runtime loaded module/target and initialization remain unobserved until original witness capture',files=pins,new_root_credit=0)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),bindings=[dict(name=r['name'],raw=hex(r['raw_bound_target']),actual_staged_export=hex(r['current_staged_export']['address']))for r in rows])))
if __name__=='__main__':main(sys.argv[1])
