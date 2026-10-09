"""Independent literal field/IAT scope checks for the passing paired relation."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-strings-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh field scope receipt');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact source-scope identity');files[str(p)]=v;return p
 parent=json.loads(pin(BASE/'paired-initialization-policy-r2/report.json','1f454d420cb4bad8ec8cbe6aa0466fc4b516aa71abc1236afa53e6f5210ce047').read_bytes());need(parent['passed'],'Passing raw paired evidence')
 rec=json.loads(pin(BASE/'recovery-r7/report.json','972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341').read_bytes());graphs=json.loads(pin(BASE/'recovery-r7/game-normal-graphs.json').read_bytes());allrows={r['pc']:r for g in graphs.values()for r in g['instructions']}
 sp=importlib.util.spec_from_file_location('field_scope_PE',pin(ROOT/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P);pe=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 bytechecks=set()
 def check(row):
  pc=row['pc'];raw=bytes.fromhex(row['bytes']);off,_=pe.rva_range(pc-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Original literal field input/store bytes');bytechecks.add(pc)
 fields=[]
 for r in rec['roots']:
  if not r['string']['actual_strdup_called']:continue
  source=r['string'];call=allrows[source['CALL_pc']];check(call);need(call['mnemonic']=='call'and call['operands']=='dword ptr [0x5bb670]','Exact source _strdup owning-IAT CALL')
  start=source['return_pc'];rows=sorted((x for x in allrows.values()if start<=x['pc']<start+20),key=lambda x:x['pc']);store=next(x for x in rows if x['mnemonic']=='mov'and x['operands']=='dword ptr [esi + 0x4], eax');check(store)
  # No operation on EAX between source return and its object-field store.
  between=[x for x in rows if x['pc']<store['pc']];need(all(x['mnemonic']=='add'and x['operands']=='esp, 0x4'for x in between),'Strdup return pointer flows unchanged to field')
  for x in between:check(x)
  need(len(r['objects'])==1,'One literal object');obj=r['objects'][0];literal=allrows[obj['pc']];check(literal);need(literal['mnemonic']=='mov'and literal['operands']==f'ecx, {hex(obj["address"])}','Exact source object identity')
  fields.append(dict(root=r['entry'],field=obj['address']+4,object=obj['address'],object_literal_PC=obj['pc'],strdup_CALL_pc=call['pc'],strdup_return_pc=start,field_store_PC=store['pc'],field_store_bytes=store['bytes'],relation_bytes=4,source=source['source'],NULinclusive_size=source['size'],source_result_flow='Literal EAX return to[ESI+4]; original and native BEFORE source models compute constructor ESI from this root ECX literal'))
 need(len(fields)==16 and len({x['field']for x in fields})==16,'Exactly16 disjoint source-established fields')
 imports={pe.image_base+x['iat_rva']:dict(library=g['library'],name=x.get('name'))for g in pe.imports()for x in g['symbols']}
 IATS={0x5bb4fc:('MSVCP50.dll','?Pinvalid@?$_Fpbase@N@std@@2NB',0x1df59c),0x5bb52c:('MSVCRT.dll','_onexit',0x1decb0),0x5bb530:('MSVCRT.dll','__dllonexit',0x1deca2),0x5bb6dc:('USER32.dll','SystemParametersInfoA',0x1df20c),0x5bb670:('MSVCRT.dll','_strdup',0x1df886)}
 iats=[]
 for address,(library,symbol,raw)in IATS.items():
  off,_=pe.rva_range(address-pe.image_base,4);need(struct.unpack_from('<I',pe.data,off)[0]==raw,'Exact raw IAT DWORD');actual=imports[address];need(actual['library'].lower()==library.lower(),'Actual owning module identity')
  # Preserve the original decorated numeric name from the PE rather than
  # imposing an inferred spelling. The four string/registration/SPI names
  # are independently exact source imports.
  if address!=0x5bb4fc:need(actual['name']==symbol,'Actual source import name')
  iats.append(dict(address=address,raw_DWORD=raw,original_PE_import=actual))
 for pc in(0x4e6a20,0x4e6a62,0x4e6a68,0x4e6a6a,0x49d1c0,0x49d1c7,0x49d1cf,0x49d1dd):check(allrows[pc])
 pin(__file__);report=dict(passed=True,scope='Independent narrow literal source scoping of five IAT identities,16 paired duplicate pointer fields and null descriptor route; no semantic rerun/coverage credit',paired_parent_sha256=sha(BASE/'paired-initialization-policy-r2/report.json'),fields=fields,IATs=iats,exact_instruction_rows_rechecked=len(bytechecks),null_constructor=dict(root=0x4e6a10,descriptor=0x60b868,load_PC=0x4e6a68,callee=0x49d1c0,branch_PC=0x49d1cf,actual_strdup_call=False),blanket_page_mask=False,source_pointer_arithmetic_byte_mask=False,observed_bytes_modified=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),fields=16,IATs=5,rows=len(bytechecks))))
if __name__=='__main__':main(sys.argv[1])
