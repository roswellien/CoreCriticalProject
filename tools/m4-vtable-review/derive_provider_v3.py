"""Observation-only release of closed canonical reader indexes between levels."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-vtable-review'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 parent=pin(R/'reports/m4-vtable-review/provider-preparation-r3/report.json','4823b78a269bf4f4d34a2fb3976aacd026eca2981c5442b71270ac2a35b4146d');v=json.loads(parent.read_bytes());assert v['passed']
 for k in ('files','generated'):
  for p,h in v[k].items():pin(p,h)
 old=pin(H/'observe120_v2.py').read_text();anchor='   finally:a.close();del a';assert old.count(anchor)==1
 replacement='   finally:\n    a.close()\n    a.entries.clear()\n    for closed_bundle in a.bundles:closed_bundle._entries.clear()\n    a.bundles.clear()\n    del a'
 new=old.replace(anchor,replacement);ast.parse(new)
 target=H/'observe120_v3.py';assert not target.exists();target.write_text(new)
 pin(R/'tools/m4-crt-allocation-root/run_v2.py');pin(R/'tools/m4-pipeline/capture_bundle.py');pin(__file__)
 report=dict(passed=True,parent=str(parent),parent_sha256=sha(parent),scope='After all complete per-level source and native comparisons, close canonical reader handles and release only its closed logical-name dictionaries. The held previous model observer can retain the small closed reader object; no live mapping or index survives into the next native level.',syntax_checked=True,source_semantics_unchanged=True,AFTER_seed_added=False,validation_before_close_unchanged=True,reader_writer_format_changed=False,initializer_credit=False,native_executed=False,files=pins,generated={str(target.resolve()):sha(target)})
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
