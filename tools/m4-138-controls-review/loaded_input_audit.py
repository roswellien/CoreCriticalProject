"""Independent ordinary physical138 loaded-input and materialized reviewer audit."""
from pathlib import Path
import ast,hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rows(path):
 decoder=json.JSONDecoder();buf='';started=False;done=False
 with Path(path).open(encoding='utf-8')as f:
  while True:
   block=f.read(1024*1024)
   if block:buf+=block
   while True:
    buf=buf.lstrip()
    if not started:
     if not buf:break
     assert buf[0]=='[';buf=buf[1:];started=True;continue
    if buf.startswith(','):buf=buf[1:];continue
    if buf.startswith(']'):done=True;buf=buf[1:];assert not buf.strip();assert not f.read().strip();return
    try:v,n=decoder.raw_decode(buf)
    except json.JSONDecodeError:break
    yield v;buf=buf[n:]
   assert len(buf)<64*1024*1024,'Bounded one-row memory'
   if not block:assert done,'Complete top-level array';return
def main():
 out=R/'reports/m4-138-controls-review/loaded-input-audit-r1';target=R/'reports/m4-tree-review/loaded-input138-review-independent-preparation-r1';assert not out.exists()and not target.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.zip','.mwb');v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prep=read(R/'reports/m4-tree-review/loaded-input138-preparation-r1/report.json','a7fa318f52c5bd38a1500b39107f331c601e33c8bf951a90db189fc82f21afbb');widget=read(R/'reports/m4-tree-review/loaded-input138-original-widget-r1/report.json','b585eae9300dc1a3f32510f5061b994f5a92af16316617e7f6c1b3410984f22c');review=read(R/'reports/m4-tree-review/loaded-input138-review-preparation-r2/report.json','55796dd6c7b2b4c0c10288e819fdb4659d546490ff0096b1ad1f715ff572683c')
 assert all(v['passed']and v['initializer_credit']==0 for v in(prep,widget,review))
 declaration=read(prep['input_domain_path'],prep['input_domain_sha256']);ob=pin(prep['whole_original_input_page'],prep['whole_original_input_page_sha256']).read_bytes();nb=pin(prep['whole_native_input_page'],prep['whole_native_input_page_sha256']).read_bytes();assert len(ob)==len(nb)==4096
 diff=[dict(offset=i,address=0x78145000+i,original=a,native=b)for i,(a,b)in enumerate(zip(ob,nb))if a!=b];fields=sorted({x['offset']&~3 for x in diff});dwords=[dict(offset=i,address=0x78145000+i,original_DWORD=struct.unpack_from('<I',ob,i)[0],native_DWORD=struct.unpack_from('<I',nb,i)[0],original_bytes=ob[i:i+4].hex(),native_bytes=nb[i:i+4].hex(),differing_byte_offsets=[x['offset']for x in diff if i<=x['offset']<i+4])for i in fields]
 assert diff==declaration['differences']and dwords==declaration['differing_DWORDs']and len(diff)==48 and len(dwords)==25
 assert declaration['whole_original_hex']==ob.hex()and declaration['whole_native_hex']==nb.hex()and declaration['typed_CS24_hex']==ob[0x640:0x658].hex()and declaration['typed_state2_bytes']==ob[0x658:0x65c].hex()
 assert ob[0x640:0x65c]==nb[0x640:0x65c]and struct.unpack_from('<I',ob,0x658)[0]==2
 jp=read(R/'reports/m4-joint-startup138/preparation-r4/report.json',prep['broad_preparation_sha256']);build=read(R/'reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47');service=read(jp['borrowed_service_preparation'],jp['borrowed_service_preparation_sha256']);lib=pin(jp['native_library'],service['files'][str(Path(jp['native_library']).resolve())]);assert build['passed']and service['passed']and build['preparation_sha256']==sha(R/'reports/m4-joint-startup138/preparation-r4/report.json')and build['files'][str(lib)]==sha(lib)
 np=read(R/'reports/m4-formatting-native/preparation-r19/report.json',prep['native_preparation_sha256']);loader=read(np['loaded_original_bootstrap_report'],np['loaded_original_bootstrap_sha256']);assert loader['passed']and loader['files'][str(Path(prep['whole_native_input_page']).resolve())]==sha(prep['whole_native_input_page'])and Path(np['loaded_input_page']).resolve()==Path(prep['whole_native_input_page']).resolve()
 roots={0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0};ledger_path=R/'reports/m4-startup138-original/widget-complete-source-r1/source-derivations.json';pin(ledger_path,widget['files'][str(ledger_path.resolve())]);cases=[]
 for row in rows(ledger_path):
  ledger=row['source_accesses'];assert ledger and all(len(v)==5 and v[3]>0 and v[4]in(0,1,False,True)for v in ledger)
  assert not any(v[1]<0x78147000 and v[1]+v[3]>0x78145000 for v in ledger)
  cases.append(dict(sequence=row['sequence'],root=row['root'],entire_source_operand_rows=len(ledger),loaded_RW_IAT_consumed_operands=0))
 assert cases==widget['cases']and len(cases)==42 and {(x['sequence'],x['root'])for x in cases}=={(i,r)for i in range(6)for r in roots}and sum(x['entire_source_operand_rows']for x in cases)==widget['source_operands_checked']==153576
 entry=pin(review['entrypoint'],review['files'][review['entrypoint']]);code=entry.read_text();tree=ast.parse(code);assert entry.parents[3]==R and 'R=Path(__file__).resolve().parents[3];PINS={}'in code and 'import collections,hashlib,json,struct,sys,traceback'in code
 # Every producer-described delta is explicit and narrow. Preserve entire parent
 # reviewer and all inherited checks by adding guards, never deleting/replacing one.
 additions=[]
 def insert(anchor,new):
  nonlocal code
  assert code.count(anchor)==1;code=code.replace(anchor,new+anchor);additions.append(dict(anchor=anchor,insert=new))
 insert('  counts.update(whole_bootstrap_input_pages=',"  fields=sorted({r['offset']&~3 for r in diff})\n  actual_DWORDs=[dict(offset=i,address=0x78145000+i,original_DWORD=struct.unpack_from('<I',ob,i)[0],native_DWORD=struct.unpack_from('<I',nb,i)[0],original_bytes=ob[i:i+4].hex(),native_bytes=nb[i:i+4].hex(),differing_byte_offsets=[r['offset']for r in diff if i<=r['offset']<i+4])for i in fields]\n  need(actual_DWORDs==declaration['differing_DWORDs']and declaration['typed_CS24_hex']==ob[0x640:0x658].hex()and declaration['typed_state2_bytes']==ob[0x658:0x65c].hex(),'Every physical DWORD geometry/value/byte-subset and exact typed input field')\n")
 insert("  for branch,items in(('original',original_widgets),('native',native_widgets)):","  need({(r['sequence'],r['root'])for r in original_widgets}=={(s,r)for s in range(6)for r in roots},'Exact unique sixsequence sevenroot original widget coverage')\n  need({(r['level'],r['sequence'],r['root'])for r in native_widgets}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in roots},'Exact unique O0/O2 sixsequence sevenroot native widget coverage')\n")
 ast.parse(code);restored=code
 for a in reversed(additions):assert restored.count(a['insert']+a['anchor'])==1;restored=restored.replace(a['insert']+a['anchor'],a['anchor'])
 assert restored==entry.read_text();old_needs=sum(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'for n in ast.walk(tree));new_needs=sum(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'for n in ast.walk(ast.parse(code)));assert new_needs==old_needs+3
 out.mkdir(parents=True);target.mkdir(parents=True);q=target/'review.py';q.write_text(code);pin(q);delta=target/'additive-delta.json';delta.write_text(json.dumps(additions,indent=2)+'\n');pin(delta);pin(__file__);pin(sys.executable)
 receipt=dict(passed=True,scope='Independent ordinary physical loaded138 input/source/materialized reviewer audit; fresh additive reviewer preparation only, not actual combined-source disjointness or endpoint carry admission',parent_review_preparation=str(R/'reports/m4-tree-review/loaded-input138-review-preparation-r2/report.json'),parent_review_sha256='55796dd6c7b2b4c0c10288e819fdb4659d546490ff0096b1ad1f715ff572683c',entrypoint=str(q),exact_inverse_to_parent_review=True,inherited_need_calls=old_needs,current_need_calls=new_needs,new_need_calls=3,whole_physical_difference_bytes=48,whole_physical_difference_DWORDs=25,independently_checked_original_widget_cases=42,independently_checked_original_widget_operands=153576,actual_native84_widget_cases_checked=False,current_source_reader_not_opened=True,review_executed=False,source_machine_executed=False,native_executed=False,archive_reader_opened=False,endpoint_carry_acceptance=False,initializer_credit=0,files=pins)
 q=target/'report.json';q.write_text(json.dumps(receipt,indent=2)+'\n');pin(q)
 audit=dict(receipt,derivative_preparation=str(q),derivative_sha256=sha(q),files=pins);q=out/'report.json';q.write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),derivative=str(target/'report.json'),derivative_sha256=sha(target/'report.json'))))
if __name__=='__main__':main()
