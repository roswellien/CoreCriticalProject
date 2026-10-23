"""Deferred additive current original admission; needs completed strict new validation."""
from pathlib import Path
import ast,hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
PARENT='7b26d9f9825aeb0443cf82735346fb0db200344f78487f16ae85a948b00ee4e2'
BUILD='da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'
PREP='9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def main(validation_path,validation_hash):
 parent=R/'reports/m4-joint-startup138-source/preparation-r8';assert sha(parent/'report.json')==PARENT
 validation_path=Path(validation_path).resolve();assert validation_path.name=='report.json'and sha(validation_path)==validation_hash
 v=json.loads(validation_path.read_bytes())
 for key,value in dict(passed=True,original_executed=True,native_executed=False,reader_closed=True,paired_export_readers_closed=True,record_bytes=356992,combined_pages=69,callbacks=108,initialized_state=2,state_seeded=False,per_phase_reseed=False,AFTER_machine_seed=False,initializer_credit=0,build_sha256=BUILD,preparation_sha256=PREP).items():assert v[key]==value,(key,v.get(key),value)
 counts=v['counts'];assert counts['phases']==828 and counts['widget_actual_root_phases']==42 and counts['widget_whole_source_page_endpoints']==114264 and counts['widget_whole_CRT_phase_page_endpoints']==105984 and counts['widget_whole_nonstack_carried_page_relations']==55896 and counts['widget_exact_MFC_CRT_transition_page_relations']==768
 measured=counts['actual_HeapReAlloc_initial_full_backing_witnesses'];assert isinstance(measured,int)and measured>=6
 old=json.loads((parent/'report.json').read_bytes());entry=parent/'compare_provider138.py';assert sha(entry)==old['files'][str(entry.resolve())]
 text=entry.read_text();changes=[]
 def one(a,b):
  nonlocal text
  assert text.count(a)==1;pos=text.index(a);changes.append(dict(position=pos,old=a,new=b));text=text[:pos]+b+text[pos+len(a):]
 one("build_sha256='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69',preparation_sha256='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'",f"build_sha256='{BUILD}',preparation_sha256='{PREP}'")
 anchor="  original_counts=original_validation['counts'];"
 one(anchor,"  need(sha(op)=="+repr(validation_hash)+",'Exact independently completed current realloc observation report');need(original_validation['counts']['actual_HeapReAlloc_initial_full_backing_witnesses']=="+str(measured)+",'Every measured current HeapReAlloc initial backing witness retained')\n"+anchor)
 reverse=text
 for d in reversed(changes):
  pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
 assert reverse==entry.read_text();ast.parse(text)
 assert text.index('Exact independently completed current realloc observation report')<text.index('ori=D.DirectSet(')
 out=parent.with_name('preparation-r9');assert not out.exists();out.mkdir()
 files=dict(old['files'])
 for p in parent.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json','compare_provider138.py'):shutil.copyfile(p,out/p.name)
 (out/'compare_provider138.py').write_text(text);(out/'current-original-admission-delta.json').write_text(json.dumps(changes,indent=2)+'\n')
 for p in out.iterdir():files[str(p.resolve())]=sha(p)
 for p in(parent/'report.json',validation_path,Path(__file__).resolve(),R/'reports/m4-138-validation-review/native138-api-preflight-r1/report.json'):files[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Current original138 strict observation identity/count-only admission derivative. All inherited native literal source gates retained.',entrypoint=str(out/'compare_provider138.py'),parent_preparation_sha256=PARENT,exact_inverse_restores_parent=True,original_validation_path=str(validation_path),original_validation_sha256=validation_hash,measured_HeapReAlloc_initial_full_backing_witnesses=measured,writer_executed=False,capture_archive_reader_opened=False,source_execution_performed=False,initializer_credit=0,changes=changes,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
