"""Prepare exact accepted IR routing derivative; no original process or execution."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-fp-numeric-max/repaired-r2'
HASHES={'4c19f0':'567fff4bf65edcc13b496194d46801282ce51fa5bc28b591fbf25e9b2c4ebc04','4c1a00':'3c30058705539810e74ae72a032c7e0146e02460de03a929f15bb679df7878d1','780c10f0':'b40b744f1d8b4930171878a93f723ec1571453d4f1dc938899ed771f2d3bf1f9'}
BRIDGES={'__remill_read_memory_32':'mw34_nmx_read32','__remill_write_memory_32':'mw34_nmx_write32','__remill_read_memory_f32':'mw34_nmx_readf32','__remill_write_memory_f32':'mw34_nmx_writef32','__remill_function_call':'mw34_nmx_call','__remill_function_return':'mw34_nmx_return','__remill_fpu_exception_clear':'mw34_nmx_clear','__remill_fpu_exception_test':'mw34_nmx_test','mw34_numeric_body_entry':'mw34_nmx_body_entry','mw34_numeric_fld_commit':'mw34_nmx_fld_commit','mw34_numeric_fstp_commit':'mw34_nmx_fstp_commit'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path(sys.argv[1]).resolve();assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max-integration') and not out.exists();out.mkdir(parents=True)
 files={};changes=[]
 def bind(p):files[str(Path(p).resolve())]=sha(p)
 def exact(text,old,new,count=1):
  assert text.count(old)==count,(old,text.count(old));changes.append({'before':old,'after':new,'occurrences':count});return text.replace(old,new)
 for entry,expected in HASHES.items():
  source=BASE/f'{entry}-repaired.ll';assert sha(source)==expected;bind(source);(out/f'{entry}-ancestor.ll').write_bytes(source.read_bytes());text=source.read_text()
  if entry=='4c19f0':
   text=exact(text,'call ptr @sub_4c1a00(ptr %state, i32 %34, ptr %33)','call ptr @mw34_nmx_dispatch_body(ptr %state, i32 %34, ptr %33)')
   text=exact(text,'declare ptr @sub_4c1a00(ptr noalias, i32, ptr noalias)','declare ptr @mw34_nmx_dispatch_body(ptr noalias, i32, ptr noalias)')
  for before,after in BRIDGES.items():
   count=text.count('@'+before+'(')
   if count:text=exact(text,'@'+before+'(','@'+after+'(',count)
  text=exact(text,'@mw34_numeric_entry_'+entry+'(','@mw34_nmx_entry_'+entry+'(')
  target=out/f'{entry}-runtime.ll';target.write_text(text);bind(target);bind(out/f'{entry}-ancestor.ll')
 # Own PE parser: exact provider header, export owner and bounded file-backed pages.
 provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';raw=provider.read_bytes();assert len(raw)==565760 and sha(provider)=='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a';bind(provider)
 def u16(o):return struct.unpack_from('<H',raw,o)[0]
 def u32(o):return struct.unpack_from('<I',raw,o)[0]
 nt=u32(0x3c);assert raw[:2]==b'MZ' and raw[nt:nt+4]==b'PE\0\0' and u16(nt+4)==0x14c
 optional=nt+24;assert u16(optional)==0x10b and u32(optional+28)==0x780c0000
 sections=[];off=optional+u16(nt+20)
 for j in range(u16(nt+6)):
  at=off+40*j;sections.append((u32(at+12),u32(at+16),u32(at+20),u32(at+36)))
 def file_offset(rva,n):
  candidates=[(ptr+rva-start,flags) for start,size,ptr,flags in sections if start<=rva and rva+n<=start+size];assert len(candidates)==1;at,flags=candidates[0];assert at+n<=len(raw);return at,flags
 def slice_(rva,n):return raw[file_offset(rva,n)[0]:file_offset(rva,n)[0]+n]
 def rv32(rva):return struct.unpack('<I',slice_(rva,4))[0]
 er=u32(optional+96);es=u32(optional+100);base=rv32(er+16);nf=rv32(er+20);nn=rv32(er+24);fa=rv32(er+28);na=rv32(er+32);oa=rv32(er+36);exports=[]
 for j in range(nn):
  name_rva=rv32(na+4*j);at=file_offset(name_rva,1)[0];end=raw.index(0,at);name=raw[at:end].decode('ascii');ordinal_index=struct.unpack('<H',slice_(oa+2*j,2))[0]
  if name=='?max@?$numeric_limits@M@std@@SAMXZ':exports.append((base+ordinal_index,rv32(fa+4*ordinal_index)))
 assert exports==[(1545,0x10f0)] and not er<=0x10f0<er+es and nf>1545-base
 leaf=slice_(0x10f0,7)
 assert hashlib.sha256(leaf).hexdigest()=='31d3ed84e61450051bfba7bc7265523bc3e687f3c7e1a1cb237ec08494ec3d1d'
 # Generic FLD m32 absolute-address and near-RET shapes, not a copied source span.
 assert len(leaf)==7 and leaf[0]==0xd9 and leaf[1]==0x05 and leaf[6]==0xc3
 assert struct.unpack_from('<I',leaf,2)[0]==0x78115004 and rv32(0x55004)==0x7f7fffff
 for rva,name in [(0x1000,'provider-code-page.bin'),(0x55000,'provider-data-page.bin')]:
  p=out/name;p.write_bytes(slice_(rva,4096));bind(p)
 report={'passed':True,'scope':'Static NEW shared-r9 numeric-max preparation only; no worker execution/admission','ancestor_IRs':HASHES,'mechanical_changes':changes,'numeric_or_flag_changes':0,'type_definition_changes':0,'bridge_aliases':BRIDGES,'MSVCP50_provider':{'path':str(provider),'sha256':sha(provider),'image_base':0x780c0000,'named_export':'?max@?$numeric_limits@M@std@@SAMXZ','ordinal':1545,'entry':0x780c10f0,'source_hex':leaf.hex(),'data_address':0x78115004},
 'routing':{'table_slot':0x5e016c,'root':0x4c19f0,'body':0x4c1a00,'game_IAT':0x5bb4fc,'body_return':0x4c19f8,'provider_return':0x4c1a09,'r9_provider_continuation_extension_required':False,'explanation':'Real provider RET returns directly into admitted game RX, not a provider code continuation. NEW registry independently admits exact MSVCP50 identity/named export/raw owning game IAT; shared MSVCRT-only continuation parser remains unused/unchanged.'},
 'bounded_domain':{'masked_CW':12,'TOP':[0,7],'live_depth':[0,1,7],'incoming_sticky_status':[0,2,34],'provider_default_data':'actual file-backed 0x7F7FFFFF','full_depth8_preentry_denied':True,'legacy_and_FX_metadata':'Distinct persistent views; no reseeding after first seed','guest_FS':'owned r9 TEB base; no guest FS instruction in selected closure'},
 'native_orchestration':'Real compiled CALLs already store frames. Typed dispatcher restores caller-view ESP by4 then r9 rewrites exactly the same real return word. Nested call/provider RETs have exact cleanup0.',
 'offline_old_original_projection':{'outer_original_broker':0x10000100,'shared_native_return':0x410a80,'resolved_reference_IAT':0x780c10f0,'native_IAT':'original admitted raw DWORD, never patched to host/provider pointer','explanation':'Both instrumented outer return word/returned PC and resolved IAT are explicit BEFORE fixture projections. They do not authorize output-value normalization or original AFTER execution inputs.'},'original_executed':False,'shared_runtime_modified':False,'whole_M4_complete':False}
 report['preparation_source_sha256']=sha(__file__)
 report['provider_source_check']='Exact private SHA + generic FLD-memory/near-RET shape, actual absolute RO operand and 7-byte extent'
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');bind(Path(__file__));(out/'prepare-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'prepare-source.py');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':main()
