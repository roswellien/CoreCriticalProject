"""Produce reviewable additive131->138 semantic checker; no acceptance run."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/acceptance138-machinery-preparation-r1';assert not out.exists();out.mkdir()
 parent=R/'tools/m4-joint-startup131/acceptance.py';s=parent.read_text();start=s.index('def semantic_checks(');end=s.index('\ndef main(',start);original=s[start:end];changes=[];t=original
 def change(before,after):
  nonlocal t
  assert t.count(before)==1,before;t=t.replace(before,after);changes.append(dict(before=before,after=after))
 change("'accepted130 identity'","'accepted131 identity'")
 change('connected_roots=130,remaining_inventory_roots=14','connected_roots=131,remaining_inventory_roots=13')
 change("prior=read(preparation['parent_joint130_preparation'],'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')","prior=read(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')")
 change("need(len(order)==131 and len({row['entry']for row in order})==131,'All131 distinct current selected roots')","need(len(order)==138 and len({row['entry']for row in order})==138,'All138 distinct current selected roots')")
 change("need([row for row in order if row['entry']!=0x5ae3e4]==prior['selected_order'],'All130 parent roots and relative order retained')","widgets={0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0}\n    need([row for row in order if row['entry']not in widgets]==prior['selected_order'],'All131 parent roots and relative order retained')\n    for phase,entry,slot in ((15,0x40e250,0x5e0048),(16,0x40ef50,0x5e004c),(17,0x40f000,0x5e0050),(47,0x479590,0x5e00cc),(134,0x5a3c30,0x5e0234),(135,0x5a3ff0,0x5e0238),(136,0x5a66f0,0x5e023c)):\n        need(order[phase]==dict(entry=entry,slot=slot),'Exact additive widget physical slot')")
 change("typed_equal(preparation['current_registration_callbacks'],101,'Current callback inventory')","typed_equal(preparation['current_registration_callbacks'],108,'Current callback inventory')")
 change("need(len(prior['registration_roots'])==101,'Entire parent callback inventory')","need(prior['current_registration_callbacks']==101,'Entire accepted parent callback inventory')")
 change("previous=Path(preparation['parent_joint130_preparation']).parent/leaf\n        need(sha(ROOT/current)==sha(previous),'Whole parent registration callbacks retained')","previous=ROOT/'reports/m4-joint-startup131/preparation-r1'/leaf\n        old_text=previous.read_text();new_text=(ROOT/current).read_text()\n        old_array=old_text.split('registration_roots = {',1)[1].split('};',1)[0].strip()\n        new_array=new_text.split('registration_roots = {',1)[1].split('};',1)[0].strip()\n        old_values=re.findall(r'0x[0-9a-fA-F]+',old_array);new_values=re.findall(r'0x[0-9a-fA-F]+',new_array)\n        need(len(old_values)==101 and len(new_values)==108 and new_values[:101]==old_values and [int(x,16)for x in new_values[101:]]==[0x40e420,0x40ef90,0x40f030,0x4795d0,0x5a3c60,0x5a4020,0x5a6720],'Entire parent callbacks retained with exact seven additions')")
 change('dict(phases=786,','dict(phases=828,')
 change('persistent131_sequences=12,persistent_phases=1572,whole_page_BEFORE=72312,whole_page_AFTER=72312','persistent138_sequences=12,persistent_phases=1656,whole_page_BEFORE=114264,whole_page_AFTER=114264')
 change("case['selected_used_bytes']==404 and capacity>=404 and capacity%4==0 and case['predicted_growth_replays']==case['actual_growth_replays']==(capacity-404)//4+1","case['selected_used_bytes']==432 and capacity>=432 and capacity%4==0 and case['predicted_growth_replays']==case['actual_growth_replays']==(capacity-432)//4+1")
 change("'Entire accepted130 proof retained'","'Entire accepted131 proof retained'")
 # All other accepted semantic predicates remain literally unchanged.
 restored=t
 for c in reversed(changes):assert restored.count(c['after'])==1;restored=restored.replace(c['after'],c['before'])
 assert restored==original
 target=R/'tools/m4-138-controls-review/acceptance138_semantics.py';assert not target.exists();target.write_text('"""Exact retained accepted131 semantic predicates plus finite138 delta."""\n'+t+'\n')
 ast.parse(target.read_text())
 delta=out/'source-delta.json';delta.write_text(json.dumps(dict(changes=changes,all_other_semantic_checks_whole_bytes_retained=True,inverse_restores_parent_semantic_checks=True),indent=2)+'\n')
 files={str(p.resolve()):sha(p)for p in(parent,target,delta,R/'tools/m4-138-controls-review/acceptance138_storage.py',Path(__file__))}
 report=out/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Source-only immutable semantic checker preparation, exact inverse restoration; no acceptance or union execution',parent_checker_sha256=sha(parent),semantic_checker_sha256=sha(target),changes=len(changes),inverse_restores_all_parent_semantic_checks=True,initializer_credit=0,worker_executed=False,capture_reader_opened=False,files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(report),semantic_checker_sha256=sha(target))))
if __name__=='__main__':main()
