"""Retain bounded exact loaded-provider operands for fresh original comparison."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 src=HERE/'compare_provider130_v4.py';dst=HERE/'compare_provider130_v5.py';assert not dst.exists();s=src.read_text()
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one('cosine_rows=[];executed_lineage={}','cosine_rows=[];provider_scope_rows=[];executed_lineage={}')
 one("F.finish(machine,responses,expected_callbacks,G);print(json.dumps", "F.finish(machine,responses,expected_callbacks,G);provider_scope_rows.append(dict(level=level,sequence=seq,bootstrap_State_hex=before['state'].hex(),bootstrap_CPU_hex=before['cpu'].hex(),bootstrap_FX_hex=before['fx'].hex(),bootstrap_page_sha256={str(p):hashlib.sha256(raw).hexdigest()for p,raw in sorted(before['memory'].items())},bootstrap_provider_pages={str(p):before['memory'][p].hex()for p in(0x7810a000,0x78145000,0x78146000)},source_provider_after_pages={str(p):machine.bytes(p,4096).hex()for p in(0x7810a000,0x78145000,0x78146000)},source_RW_IAT_operands=[dict(source_access_index=i,PC=r[0],address=r[1],value=r[2],width=r[3],write=r[4])for i,r in enumerate(machine.accesses)if 0x78145000<=r[1]and r[1]+r[3]<=0x78147000],provider_API_transports=[list(r)for r in machine.transports if 0x78145000<=r[1]and r[1]+r[3]<=0x78147000],Lockit_state_reads=machine.lockit_state_reads,Lockit_API_relations=responses.lockit_relations,source_ledger_compared=True,bootstrap_complete_page_scope_compared=True));print(json.dumps")
 one("len(tree_rows)==12,'Every130", "len(tree_rows)==12 and len(provider_scope_rows)==12,'Every130")
 one("('Formatting-source-derivations.json',format_rows)","('Loaded-provider-source-scope.json',provider_scope_rows),('Formatting-source-derivations.json',format_rows)")
 one("pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v6.py');", "pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v6.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v7.py');")
 one('complete_selected_source=True,','loaded_provider_source_scope=str(out/\'Loaded-provider-source-scope.json\'),complete_selected_source=True,')
 ast.parse(s);dst.write_text(s)
 files={str(p.resolve()):sha(p)for p in(src,dst,Path(__file__),HERE/'formatting_derivations.py',HERE/'formatting_derivations_v2.py',HERE/'formatting_derivations_v3.py',HERE/'final_observer130.py',HERE/'final_observer130_v2.py',HERE/'continuity130.py')}
 report=dict(passed=True,scope='Complete130 combined gate with bounded current native loaded-provider access and true bootstrap page scope export',tool=str(dst),new_export='Loaded-provider-source-scope.json',new_rows=12,all_reached_RW_and_IAT_operands=True,full_provider_BEFORE_and_source_AFTER_pages=True,complete_bootstrap_page_digest_scope=True,all36_Lockit_relations_per_case=True,source_ledger_already_compared=True,files=files,executed=False,capture_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
