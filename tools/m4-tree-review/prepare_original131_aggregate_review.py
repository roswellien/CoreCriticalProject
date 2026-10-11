"""Preserve inherited source byteflow checks on current131 raw exports."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_original130_combined_v3.py';t=p.read_text();changes=[]
    def one(a,b):
        nonlocal t
        assert t.count(a)==1,(a,t.count(a));t=t.replace(a,b);changes.append(dict(before=a,after=b))
    one("p=R/'reports/m4-startup130-original/combined-source-r3/report.json';a=read(p,'2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624')", "p=Path(sys.argv[2]).resolve();a=read(p,sys.argv[3])")
    one("a['archive_sessions_opened']==1", "a['archive_sessions_opened']==0 and a['capture_archive_opened']is False")
    one("need(len(excluded)==1,'One retained current original capture, no reread')", "need(not excluded,'Current raw-export comparers opened/pinned no canonical archive')\n  producer=read(a['raw_export_report_path'],a['raw_export_report_sha256']);need(producer['passed']and producer['reader_closed']and producer['paired_export_readers_closed'],'Current full producing reader sealed all raw branches')\n  continuity=read(R/'reports/m4-startup131-original/inherited-source-preparation-r3/report.json','3f21fbc601dd3b8dfea3ea4354e425f3aa6a368f1e1ddd77f06958bed656be97');need(continuity['passed']and continuity['counts']['inherited_exact_source_spans']==3955 and continuity['counts']['current_root_table_pairs']==131,'Current inherited source/physical table continuity')\n  for path,digest in continuity['files'].items():pin(path,digest)\n  raw_export=next(row for row in producer['paired_exports']if row['branch']=='original');need(raw_export['capture_sha256']==v['original_capture_sha256'],'Whole canonical original identity retained by raw exporter')")
    one('reports/m4-startup130-original/validation-r2/fresh-cdecl.json','reports/m4-startup131-original/validation-r2/fresh-cdecl.json')
    one('tools/m4-startup130-original/format_source_v4.py','tools/m4-startup131-original/format_source_v4.py')
    one('tools/m4-startup130-original/current_source_v4.py','tools/m4-startup131-original/current_inherited_source_v2.py')
    one('tools/m4-startup130-original/tree_source.py','tools/m4-startup131-original/tree_source.py')
    one('"need(tree_phase==78"in tree','"need(tree_phase==79"in tree')
    one('asserted78','asserted79')
    one('reports/m4-startup130-original/preparation-r2/format_observer_x86.asm','reports/m4-startup131-original/preparation-r4/format_observer_x86.asm')
    one("case['phase']==78 and s['phase']==78", "case['phase']==79 and s['phase']==79")
    t=t.replace('current original130','current original131').replace('original130 source/FS','original131 source/FS')
    ast.parse(t);q=R/'tools/m4-tree-review/review_original131_combined.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted additive current131 raw-export original aggregate reviewer; inherited actual cdecl/FS input timing, whole owner byteflows and full tree source coverage unchanged',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
