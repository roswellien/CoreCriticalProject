"""Exact current producer64CRT domain routing; no model/import/raw reader."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/input-materialization-preparation-r3';assert not out.exists();out.mkdir();p=R/'tools/m4-original141-source/materialize_current_inputs_v2.py';q=p.with_name('materialize_current_inputs_v3.py');assert not q.exists();a=p.read_text()
 old="   if logical in reader.entries:b=reader.data(logical)\n"
 new="   if 0x78000000<=address<0x78040000:\n    need(address%4096==0 and side in('before','after')and V['counts']['widget_whole_CRT_phase_page_endpoints']==108288,'Exact current own64CRT source domain and all846 paired observations');logical=f'{stem}/CRT-{side}/{address}.bin';need(logical in reader.entries,'Exact producer own64CRT logical input/target, no page fallback');b=reader.data(logical)\n   elif logical in reader.entries:b=reader.data(logical)\n"
 assert a.count(old)==1;b=a.replace(old,new);q.write_text(b);assert b.replace(new,old)==a
 before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 assert len(d)==1;(out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n')
 reference=R/'reports/m4-original141/source-preparation-r6/reference.cpp';text=reference.read_text();source=[]
 for side in('before','after'):
  literal='for(unsigned i=0;i<64;++i)out.append(phase_stem+"/CRT-'+side+'/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);'
  assert text.count(literal)==1;source.append(dict(side=side,source_line=text[:text.index(literal)].count('\n')+1,exact_literal=literal,pages=64,base=0x78000000,end=0x78040000,bytes_per_page=4096))
 prior=R/'reports/m4-original141-source/input-materialization-preparation-r2/required-ordinary-files.json';files=json.loads(prior.read_bytes());assert str(p)in files;files.pop(str(p));files[str(q)]=sha(q);files[str(reference)]=sha(reference);files[str(Path(__file__).resolve())]=sha(Path(__file__));files[str(out/'inverse.json')]=sha(out/'inverse.json');(out/'required-ordinary-files.json').write_text(json.dumps(files,indent=2)+'\n')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,canonical_reader_opened=False,ordinary_export_opened=False,imports_executed=False,source_execution=False,initializer_credit=0,exact_whole_inverse=True,inverse_hunks=1,semantic_delta='For exact aligned current CRT64 domain only, use current actual phase CRT-before/CRT-after full4096 logical record before fixed43/extra26 branches. Missing genuineCRT record fails without fallback. Existing raw356992/page4096/own physical/export hash/declared source/chronology checks remain unchanged.',physical_CRT_source_extent=source,required_ordinary_files=str(out/'required-ordinary-files.json'),files={str(p):sha(p),str(p.with_name('materialize_current_inputs_v3.py')):sha(p.with_name('materialize_current_inputs_v3.py')),str(reference):sha(reference),str(prior):sha(prior),str(out/'inverse.json'):sha(out/'inverse.json'),str(out/'required-ordinary-files.json'):sha(out/'required-ordinary-files.json'),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
