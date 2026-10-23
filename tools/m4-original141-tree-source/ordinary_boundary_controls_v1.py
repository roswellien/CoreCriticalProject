"""Actual production pin boundary controls, no file input reader."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/ordinary-boundary-controls-r1';out.mkdir();q=R/'tools/m4-original141-tree-source/tree_source_v3.py';tree=ast.parse(q.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='pin');checks=[n.value.args[0]for n in fn.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='need'];assert len(checks)==2;compiled=[compile(ast.Expression(c),str(q),'eval')for c in checks];ordinary={str(Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original/'+n).resolve())for n in ('index.json','payload.bin')};results=[]
 def test(name,p,want,allow=ordinary):
  got=all(bool(eval(c,dict(path=Path(p).resolve(),ORDINARY_EXPORT_PATHS=allow)))for c in compiled);assert got==want,name;results.append(dict(name=name,passed=True,expected_accept=want))
 test('D_source_preserved',R/'tools/m4-tree-source/game_model_v4.py',True);test('D_physical_metadata_preserved',R/'reports/m4-original141/root-compiled-review-r2/report.json',True)
 for p in ordinary:test('exact_current_'+Path(p).name,p,True)
 for suffix in ('.mwb','.mwi','.zip'):test('reject_archive_'+suffix,R/('test'+suffix),False)
 test('reject_D_transport',R/'transport.json',False);test('reject_G_transport','G:/Projects/MW34Recomp-Captures/transport.json',False);test('reject_other_G_index','G:/Projects/MW34Recomp-Captures/other/index.json',False);test('reject_other_G_raw','G:/Projects/MW34Recomp-Captures/other/raw.bin',False)
 p='G:/Projects/MW34Recomp-Captures/canonical.mwb';test('archive_cannot_be_whitelisted',p,False,{str(Path(p).resolve())});p='G:/Projects/MW34Recomp-Captures/transport.json';test('transport_cannot_be_whitelisted',p,False,{str(Path(p).resolve())})
 files={str(q.resolve()):hashlib.sha256(q.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};p=out/'report.json';p.write_text(json.dumps(dict(passed=True,controls=results,production_AST_only=True,canonical_reader_opened=False,ordinary_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
