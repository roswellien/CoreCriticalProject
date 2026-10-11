"""Ensure export failure cannot leave a canonical reader open."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True);parent=ROOT/'tools/m4-joint-startup131/compare_provider_v3.py';target=parent.with_name('compare_provider_v4.py');assert not target.exists();text=parent.read_text()
 old="""   finally:
    if len([r for r in rows if r['level']==level])==786:
     export=EX.Export(out/'paired',level,a.path,pin)
     try:export.copy(a);paired_exports.append(export.finish())
     finally:export.close()
    a.close()"""
 new="""   finally:
    try:
     if len([r for r in rows if r['level']==level])==786:
      export=EX.Export(out/'paired',level,a.path,pin)
      try:export.copy(a);paired_exports.append(export.finish())
      finally:export.close()
    finally:a.close()"""
 assert text.count(old)==1;text=text.replace(old,new);text=text.replace('reader_closed=readers_closed,','reader_closed=readers_closed,paired_export_readers_closed=readers_closed,');ast.parse(text);target.write_text(text)
 report=dict(passed=True,scope='Unexecuted exact full131 source/provider/export with guaranteed canonical closure on export failure',parent_preparation=str(ROOT/'reports/m4-joint-startup131-source/preparation-r3/report.json'),parent_preparation_sha256=sha(ROOT/'reports/m4-joint-startup131-source/preparation-r3/report.json'),tool=str(target),changes=[dict(before=old,after=new)],files={str(p.resolve()):sha(p)for p in(Path(__file__),parent,target)},worker_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
