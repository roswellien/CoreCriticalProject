"""Close the confirmed pre-audit three-helper gap, without opening captures."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/closure-preparation-r1';assert not out.exists();out.mkdir(parents=True)
 files={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 old=pin(R/'tools/m4-native141-source/final_observer141_v5.py','5101bfe7718ff314054eb22f794767285bff288965a7d2fa8de453acfca28453')
 extra='''

def pin_current_inputs(pin):
 """Authenticate all pre-audit child source before a capture reader opens."""
 receipt=ROOT/'reports/m4-native141-source/observer-preparation-r5/report.json'
 current=json.loads(pin(receipt,'ac0ff78b6038f3f47d2edfaaef5b923cd0a6dac6b8797e68f232f87297f06a7d').read_bytes())
 need(current['passed'] and current['source_only'] and not current['canonical_reader_opened'],'Exact current source-only observer preparation')
 for path,digest in current['files'].items():pin(path,digest)
 for path in (__file__,Association.__module__,install_named.__module__,_partition_normal_FS.__module__):
  source=sys.modules[path].__file__ if path in sys.modules else path
  pin(source)
 return dict(pinned_before_capture_open=True,physical_preparation=str(receipt),physical_files=len(current['files']),AFTER_seed=False)
'''
 child=R/'tools/m4-native141-source/final_observer141_v6.py';assert not child.exists();text=old.read_text()+extra;ast.parse(text);child.write_text(text);pin(child)
 assert text[:-len(extra)]==old.read_text()
 changes.append(dict(parent=str(old),child=str(child),edit='Append only explicit current physical observer preparation/helper closure',added=extra))
 parentprep=R/'reports/m4-startup141-source/preparation-r2'
 pin(parentprep/'report.json','c8be199dd1c7c9dc749907d9f2ed6bf15b7132ac8e0acb75ebf7fff9a784fcdb')
 parent=pin(parentprep/'compare_provider141.py','beb4665dc1a62c51374efb72089c9bcf4844216ba8c798f0ee2f76452ca0ac2f')
 dest=R/'reports/m4-startup141-source/preparation-r3';assert not dest.exists();dest.mkdir()
 deltas=[dict(old='final_observer141_v5.py',new='final_observer141_v6.py',count=1),dict(old=' try:\n  NI=load(',new=' try:\n  F.pin_current_inputs(pin)\n  NI=load(',count=1)]
 text=parent.read_text()
 for row in deltas:assert text.count(row['old'])==row['count'];text=text.replace(row['old'],row['new'])
 ast.parse(text);reverse=text
 for row in reversed(deltas):assert reverse.count(row['new'])==row['count'];reverse=reverse.replace(row['new'],row['old'])
 assert reverse==parent.read_text()
 p=dest/'compare_provider141.py';p.write_text(text);pin(p)
 p=dest/'paired_exports.py';p.write_bytes(pin(parentprep/'paired_exports.py').read_bytes());pin(p)
 p=dest/'closure-deltas.json';p.write_text(json.dumps(deltas,indent=2)+'\n');pin(p)
 inherited=json.loads(pin(parentprep/'driver-deltas.json').read_bytes());assert len(inherited)==27
 inherited[2]['new']=inherited[2]['new'].replace('final_observer141_v5.py','final_observer141_v6.py')
 inherited.append(deltas[1]);reverse=text
 for row in reversed(inherited):assert reverse.count(row['new'])==row['count'];reverse=reverse.replace(row['new'],row['old'])
 olddriver=pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py');assert reverse==olddriver.read_text()
 p=dest/'driver-deltas.json';p.write_text(json.dumps(inherited,indent=2)+'\n');pin(p)
 p=out/'observer-addition.json';p.write_text(json.dumps(changes,indent=2)+'\n');pin(p);pin(__file__)
 report=dict(passed=True,prepared_only=True,exact_parent_inverse=True,immediate_driver_deltas=2,composed_source6_driver_deltas=28,base_driver_deltas=27,three_new_helpers_hashed_before_capture=True,entrypoint=str(dest/'compare_provider141.py'),observer=str(child),reviewer_authored_driver=True,ROOT_independent_admission_required=True,admitted=False,canonical_reader_opened=False,consumer_executed=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (dest/'report.json').write_text(json.dumps({**report,'closure_preparation':str(out/'report.json'),'closure_preparation_sha256':sha(out/'report.json')},indent=2)+'\n')
 print(sha(out/'report.json'));print(sha(dest/'report.json'))
if __name__=='__main__':main()
