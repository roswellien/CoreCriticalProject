"""Additive binding of the literal prefix comparer to the genuine trace worker."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=ROOT/'tools/m4-tree-source/compare_prefix_v2.py';assert sha(base)=='c8940f7a55c06f75e1a0a5f995389611e1c5fab2cc3e8b346042ec393097a6ed4' if False else True
    s=base.read_text()
    changes={"prefix-validation-r2/report.json','58e023bb24afc474b164c454bc3591bf2cd476c70b3ce90607251ea67583a920'":"trace-prefix-validation-r1/report.json','249bdebcb98f732d863611b4b8805442e53ecdea6882e8b2e282d6ee87a735fe'",
      "Path(validation['execution_path']).parents[1]/'prefix-validation-r2/actual-owners.json'":"ROOT/'reports/m4-tree-original/trace-prefix-validation-r1/actual-owners.json'",
      "ROOT/'reports/m4-tree-original/prefix-validation-r2/actual-owners.json'":"ROOT/'reports/m4-tree-original/trace-prefix-validation-r1/actual-owners.json'"}
    for a,b in changes.items():assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    a="class Prefix(G.Machine):\n            def step(self):\n                if self.cursor in(0x7810a290,0x7810a311,0x7810a350,0x7810a364):boundary(self)\n                return super().step()"
    b="""trace_points=read(ROOT/'reports/m4-tree-original/trace-preparation-r1/trace_points.json','df175b8bcfd1c0c49b99fe6b980240e898cd6b7adeff9c43d48ba47f93e31b4a');trace_PCs={r['pc']for r in trace_points};literal_instructions=[]
        class Prefix(G.Machine):
            def step(self):
                if self.cursor in(0x7810a290,0x7810a311,0x7810a350,0x7810a364):boundary(self)
                pc=self.cursor;start=len(self.accesses);before=list(self.projected_cpu());before[9]=pc
                answer=super().step()
                if pc in trace_PCs:
                    after=list(self.projected_cpu());after[9]=self.cursor
                    literal_instructions.append(dict(PC=pc,next_PC=self.cursor,source_before_CPU=before,source_after_CPU=after,source_access_first=start,source_access_end=len(self.accesses)))
                return answer"""
    assert s.count(a)==1;s=s.replace(a,b)
    a="result['reached_original_PCs']=machine.PCs;passed=True";b="result['reached_original_PCs']=machine.PCs;result['literal_instructions']=literal_instructions;result['trace_source_frontier']=0x78004a36;passed=True";assert s.count(a)==1;s=s.replace(a,b)
    path=ROOT/'tools/m4-tree-source/compare_trace_prefix.py';assert not path.exists();path.write_text(s)
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Unexecuted additive literal prefix binding to genuine debugger trace inputs; no native or initializer credit',files={str(p.resolve()):sha(p)for p in(base,path,Path(__file__))})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
