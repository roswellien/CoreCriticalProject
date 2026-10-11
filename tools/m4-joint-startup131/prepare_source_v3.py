"""Exact raw paired equality exports from the same full source/provider pass."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True);parent=ROOT/'tools/m4-joint-startup131/compare_provider_v2.py';target=parent.with_name('compare_provider_v3.py');assert not target.exists();text=parent.read_text();changes=[]
 def one(a,b):
  nonlocal text
  assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b);changes.append(dict(before=a,after=b))
 one('import flag_consumers as FC','import flag_consumers as FC\nimport paired_exports as EX')
 one('loader_rows=[];flag_rows=[];ori=None;readers_closed=False','loader_rows=[];flag_rows=[];paired_exports=[];ori=None;readers_closed=False')
 one("  for level in ('O0','O2'):","  original_export=EX.Export(out/'paired','original',ori.path,pin)\n  try:original_export.copy(ori);paired_exports.append(original_export.finish())\n  finally:original_export.close()\n  for level in ('O0','O2'):")
 one('   finally:\n    a.close()',"   finally:\n    if len([r for r in rows if r['level']==level])==786:\n     export=EX.Export(out/'paired',level,a.path,pin)\n     try:export.copy(a);paired_exports.append(export.finish())\n     finally:export.close()\n    a.close()")
 one("need(len(flag_rows)==12,'Every persistent source lifecycle has explicit before-step architectural flag checks')","need(len(flag_rows)==12,'Every persistent source lifecycle has explicit before-step architectural flag checks');pin(ROOT/'tools/m4-joint-startup131/paired_exports.py');pin(ROOT/'tools/m4-joint-startup131/prepare_source_v3.py');need([r['branch']for r in paired_exports]==['original','O0','O2'],'All raw current paired branches retained in same canonical reader')")
 one('report=dict(passed=passed,executed_lineage=', 'report=dict(passed=passed,paired_exports=paired_exports,executed_lineage=')
 ast.parse(text);target.write_text(text);files={str(p.resolve()):sha(p)for p in(Path(__file__),parent,target,parent.with_name('paired_exports.py'))};report=dict(passed=True,scope='Unexecuted unchanged full131 source/provider with bounded raw equality targets for paired consumers; canonical reader and all source predicates unchanged',parent_preparation=str(ROOT/'reports/m4-joint-startup131-source/preparation-r2/report.json'),parent_preparation_sha256=sha(ROOT/'reports/m4-joint-startup131-source/preparation-r2/report.json'),tool=str(target),files=files,changes=changes,paired_raw_export=True,original_export_all_logical_entries=True,native_export_all_phase46pages=True,native_checkpoint_page_export_scope='Lowerstack saved-frame equality targets only; all current source/provider checkpoint pages remain compared in producing gate',candidate_AFTER_machine_seed=False,per_phase_BEFORE_machine_seed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
