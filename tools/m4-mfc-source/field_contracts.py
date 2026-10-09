"""Freeze all literal owned pointer stores and static byte header provenance."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mfc-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive field contract');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen causal field input');files[str(p)]=v;return p
 rec=json.loads(pin(BASE/'recovery-r4/report.json','b50217399d254eddc620ab39bf8d934fd2cc30233e575356a9d8c40761c33e0f').read_bytes());geo=json.loads(pin(BASE/'allocation-contracts-r4/report.json','30ef9954b16ba185294871d5cb419df502b656aab7f12fc521a4e3b09fe156f2').read_bytes());traces=json.loads(pin(BASE/'allocation-contracts-r4/derivations.json',geo['files'][str((BASE/'allocation-contracts-r4/derivations.json').resolve())]).read_bytes());contract=json.loads(pin(BASE/'recovery-r4/instruction-contracts.json').read_bytes());rows={r['pc']:r for r in contract['instructions']};sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 pe=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());fields=[];headers=[]
 def static(a):return any(pe.image_base+s['virtual_address']<=a<pe.image_base+s['virtual_address']+max(s['raw_size'],s['virtual_size'])and s['writable']for s in pe.sections)
 for trace in traces:
  root=trace['root'];accesses=trace['source_accesses']
  for owner in trace['allocations']:
   pointer=owner['declared_pointer'];found=[]
   for pc,a,v,n,w in accesses:
    if w and n==4 and static(a)and pointer<=v<=pointer+owner['requested_size']:
     row=rows[pc];need(row['mnemonic']=='mov'and row['explicit_memory_writes'],'Literal typed pointer source MOV');raw=bytes.fromhex(row['bytes_hex']);off,_=pe.rva_range(pc-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Exact primary PE pointer-store instruction')
     found.append(dict(root=root,CALL_pc=owner['CALL_pc'],object=owner['object'],primary_publication=owner['publication'],field=a,write_pc=pc,pointer_offset=v-pointer,requested_size=owner['requested_size'],is_one_past_end=v==pointer+owner['requested_size'],source_row=row))
   need(sum(r['pointer_offset']==0 and r['field']==owner['publication']for r in found)==1,'Exactly one primary live owner publication');fields.extend(found)
  for ai,(pc,a,v,n,w)in enumerate(accesses):
   if not(w and n==1 and static(a)):continue
   row=rows[pc];need(row['mnemonic']=='mov'and row['explicit_memory_writes'],'Literal static header byte source MOV');prior=[(ri,rp,ra,rv,rn)for ri,(rp,ra,rv,rn,rw)in enumerate(accesses[:ai])if not rw and rn==1 and 0x20001000<=ra<0x20002000];need(prior,'Actual header has explicit saved source byte read');ri,rp,ra,rv,rn=prior[-1];saves=[(si,sp,sa,sv,sn)for si,(sp,sa,sv,sn,sw)in enumerate(accesses[:ri])if sw and sa<=ra<sa+sn];need(saves,'Dominating literal stack store');si,sp,sa,sv,sn=saves[-1];need(((sv>>(8*(ra-sa)))&255)==rv==v,'Exact saved source byte flows to literal header')
   raw=bytes.fromhex(row['bytes_hex']);off,_=pe.rva_range(pc-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Exact primary PE header-store instruction');rootspec=next(r for r in rec['roots']if r['entry']==root);objects=[o['address']for o in rootspec['objects']if 0<=a-o['address']<=32];need(objects,'Header tied to literal static object');object_=max(objects)
   headers.append(dict(root=root,object=object_,field=a,object_offset=a-object_,write_pc=pc,research_value=v,read_pc=rp,read_address=ra,store_pc=sp,store_address=sa,store_value=sv,store_width=sn,byte_offset=ra-sa,source_row=row))
 need(len(fields)==39 and sum(r['is_one_past_end']for r in fields)==4 and len({r['field']for r in fields})==39,'35 primary pointers and4 exact vector endpoints');need(len(headers)==36 and len({r['field']for r in headers})==36,'Complete36 static byte headers including base+4 and extra object')
 for filename,value in(('pointer-fields.json',fields),('header-fields.json',headers)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
 pin(__file__);report=dict(passed=True,scope='Exact source-derived typed39 owned pointer stores and36 static byte header saved-byte provenance; no new execution or byte masking',pointer_fields=fields,header_fields=headers,primary_allocation_fields=35,one_past_end_fields=4,header_count=36,extra_object_root=0x587c90,AFTER_machine_seed=False,source_declaration_facts='Unchanged declared positive research pointers from frozen literal BEFORE geometry; genuine original/native execution proofs separately bind actual API owners',files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),fields=len(fields),headers=len(headers))))
if __name__=='__main__':main(sys.argv[1])
