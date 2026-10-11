"""Retain finite genuine registry growth as a separate suffix relation."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-original/format_source.py';new=old.with_name('format_source_v2.py');assert not new.exists();body=old.read_text();hunks=[]
 def one(a,b):
  nonlocal body
  assert body.count(a)==1,a[:150];body=body.replace(a,b);hunks.append(dict(old=a,new=b))
 a="""            need(prevmeta[0]==current_begin and prevmeta[1]==current_next and aftermeta[0]==current_begin and aftermeta[1]==current_next+4 and prevmeta[2]==aftermeta[2] and current_next-current_begin+4<=prevmeta[2],'Separate actual original registry suffix takes the literal no-growth append domain')
            expected_vector=bytearray(previous[356480:356480+prevmeta[2]]);struct.pack_into('<I',expected_vector,current_next-current_begin,root['registration']['callback']);eq(bytes(expected_vector),raw[356480:356480+aftermeta[2]],'Whole genuine registry backing from preceding carried BEFORE plus one physical callback store')
"""
 b="""            need(prevmeta[0]==current_begin and prevmeta[1]==current_next and current_next>=current_begin,'Whole actual preceding registry input is current source BEFORE')
            used=current_next-current_begin;new_begin=current_begin;growth=[]
            if used+4>prevmeta[2]:
                growth=[(i,f)for i,f in enumerate(API)if f[24]==3 and f[22]==current_begin]
                need(len(growth)==1,'One actual original registry HeapReAlloc response at literal growth branch');ai,fact=growth[0]
                need(fact[21]==0 and fact[23]==prevmeta[2]+16 and fact[10]and aftermeta[2]>=fact[23],'Exact registry source capacity+16 request, genuine response scalar and actual extent');new_begin=fact[10];counts['separate_original_registry_growth_scalar_inputs']+=1
            else:need(aftermeta[2]==prevmeta[2],'No-growth capacity is carried exactly')
            need(aftermeta[0]==new_begin and aftermeta[1]==new_begin+used+4,'Separate physical registry pointer/cursor stores from genuine BEFORE and finite API scalar')
            expected_vector=bytearray(previous[356480:356480+prevmeta[2]]);struct.pack_into('<I',expected_vector,used,root['registration']['callback'])if used+4<=len(expected_vector)else expected_vector.extend(struct.pack('<I',root['registration']['callback']))
            eq(bytes(expected_vector),raw[356480:356480+len(expected_vector)],'Every preserved original registry input byte plus new literal callback store');counts['separate_original_registry_preserved_backing_bytes']+=len(expected_vector)
"""
 one(a,b)
 one("if page==0x78037000:struct.pack_into('<I',predicted,0x888,current_next+4)","if page==0x78037000:struct.pack_into('<II',predicted,0x888,new_begin+used+4,new_begin)")
 one("registration_suffix=dict(before_begin=current_begin,before_next=current_next,after_next=current_next+4,callback=", "registration_suffix=dict(before_begin=current_begin,before_next=current_next,source_derived_after_begin=new_begin,source_derived_after_next=new_begin+used+4,finite_HeapReAlloc_response=[dict(API_index=i,actual_words=list(f))for i,f in growth],new_unused_growth_tail_observed_only=bool(growth),callback=")
 one("separate literal registration cursor store ","separate literal registration pointer/cursor stores ")
 one("Separate no-growth registry cursor/vector relation", "Separate finite registry growth-or-carry cursor/vector relation")
 new.write_text(body);out=R/'reports/m4-startup130-original/format-source-preparation-r2';assert not out.exists();out.mkdir(parents=True);p=out/'hunks.json';p.write_text(json.dumps(hunks,indent=2)+'\n');pins={str(p.resolve()):sha(p)for p in [old,new,Path(__file__),p]};report=dict(passed=True,scope='Unexecuted original130 formatter proof with separate finite true registry HeapReAlloc scalar response and literal callback/pointer/cursor stores; new unwritten growth tail is retained outside constructor-prefix scope',files=pins,capture_reader_opened=False,executed=False);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
