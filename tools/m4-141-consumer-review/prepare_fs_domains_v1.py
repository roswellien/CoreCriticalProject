"""Static producer-domain correction; no canonical reader or source execution."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/FS-domain-preparation-r1';assert not out.exists();out.mkdir()
 dest=R/'reports/m4-startup141-source/preparation-r5';assert not dest.exists();dest.mkdir()
 files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 old=pin(R/'tools/m4-native141-source/final_observer141_v7.py','f21d92a16b2b82b9eeb92bbccb2e4936f2fac08130c834ffcf55a4ccca8020fa')
 helper=pin(R/'tools/m4-native141-source/constructor_fs_union141_v2.py');pin(R/'tools/m4-native141-source/constructor_fs_union141_v1.py')
 text=old.read_text();deltas=[]
 def change(old,new,count=1):
  nonlocal text
  assert text.count(old)==count;text=text.replace(old,new);deltas.append(dict(old=old,new=new,count=count))
 change('constructor_fs_union141_v1','constructor_fs_union141_v2',2)
 change(' pin(__file__)\n modules='," pin(__file__)\n current['files'][str((ROOT/'tools/m4-native141-source/constructor_fs_union141_v2.py').resolve())]='"+sha(helper)+"'\n modules=")
 reverse=text
 for d in reversed(deltas):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==old.read_text();ast.parse(text)
 observer=R/'tools/m4-native141-source/final_observer141_v8.py';assert not observer.exists();observer.write_text(text);pin(observer)
 parent=R/'reports/m4-startup141-source/preparation-r4';pin(parent/'report.json','2a95f9bcbf1374bd6594685ffa690d995582c00cb1e58fd6c45da0d4dfcd5d58')
 driver=pin(parent/'compare_provider141.py');text=driver.read_text();assert text.count('final_observer141_v7.py')==1;text=text.replace('final_observer141_v7.py','final_observer141_v8.py');ast.parse(text);assert text.replace('final_observer141_v8.py','final_observer141_v7.py')==driver.read_text()
 path=dest/'compare_provider141.py';path.write_text(text);pin(path)
 path=dest/'paired_exports.py';path.write_bytes(pin(parent/'paired_exports.py').read_bytes());pin(path)
 driver_deltas=json.loads(pin(parent/'driver-deltas.json').read_bytes());assert len(driver_deltas)==28
 found=0
 for d in driver_deltas:
  if 'final_observer141_v7.py'in d['new']:d['new']=d['new'].replace('final_observer141_v7.py','final_observer141_v8.py');found+=1
 assert found==1;reverse=text
 for d in reversed(driver_deltas):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 base=pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py');assert reverse==base.read_text()
 path=dest/'driver-deltas.json';path.write_text(json.dumps(driver_deltas,indent=2)+'\n');pin(path)
 path=out/'observer-deltas.json';path.write_text(json.dumps(deltas,indent=2)+'\n');pin(path)
 for name in ['fs_operations.inc','fs_contract.inc','container_contract.inc','vtable_contract.inc','lockit_contract.inc','tree_contract.inc','session_impl.inc','constructor-FS-contracts.json']:
  pin(R/'reports/m4-startup141-runway/service-preparation-r2'/name)
 for name in ['report.json','Constructor-carried-source-derivations.json','failure.txt']:pin(R/'reports/m4-startup141-source/combined-source-provider-r1'/name)
 pin(R/'reports/m4-startup141-root/validation-r1/report.json','00406b1d901fe996e0d15f9281048ff6222d6bae5ceaf1d3e721b5d0f271d610');pin(__file__)
 report=dict(passed=True,prepared_only=True,scope='Correct actual producer journal domains; inherited normal FS validation body unchanged, all21 constructor component events and14 full raw records reconstructed from pre-event native committed source writes.',exact_observer_inverse=True,immediate_observer_deltas=2,immediate_driver_deltas=1,composed_source6_driver_deltas=28,normal_frames=28,normal_raw_records=56,constructor_component_frames=7,constructor_component_events=21,constructor_committed_source_records=14,no_fabricated_normal_constructor_rows=True,actual_native_global_cardinality_diagnostic_pending=True,entrypoint=str(dest/'compare_provider141.py'),observer=str(observer),reviewer_authored_driver=True,ROOT_independent_admission_required=True,admitted=False,canonical_reader_opened=False,consumer_executed=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (dest/'report.json').write_text(json.dumps({**report,'FS_domain_preparation':str(out/'report.json'),'FS_domain_preparation_sha256':sha(out/'report.json')},indent=2)+'\n')
 print(json.dumps(dict(review=str(out/'report.json'),review_sha256=sha(out/'report.json'),preparation=str(dest/'report.json'),preparation_sha256=sha(dest/'report.json'))))
if __name__=='__main__':main()
