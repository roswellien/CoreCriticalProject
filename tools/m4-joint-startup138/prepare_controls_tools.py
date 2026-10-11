"""Seal unexecuted current owned-prefix controller and semantic checker.

The initial checker draft is retained: it assumed stock-only root40E250 had
owned fonts. This derivative binds the physically proved phase134 creations.
"""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(t,a,b):
 if t.count(a)!=1:raise ValueError('Exact additive tool hunk '+a[:130]+' count '+str(t.count(a)))
 return t.replace(a,b)
def main(name):
 out=R/'reports/m4-joint-startup138'/name
 if out.exists():raise ValueError('Fresh source-only tools preparation')
 out.mkdir();pins={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p)
  if p.suffix.lower()in('.mwb','.zip')or(h and h!=v):raise ValueError('Exact ordinary input '+str(p))
  if str(p)in pins and pins[str(p)]!=v:raise ValueError('Stable source identity')
  pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-joint-startup138/controls-preparation-r4/report.json','f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e');recipe=json.loads(pp.read_bytes());
 if not recipe['passed']or recipe['control_phase']!=135 or recipe['source_owned_font_create_calls']!=15:raise ValueError('Actual source-owned current prefix')
 controller=pin(R/'tools/m4-joint-startup138/run_context_controls.py');t=controller.read_text();subs=[('from stages import run_stage,verify_stage','from stages_capture_storage import run_stage,verify_stage\nfrom paths_capture_storage import STORAGE_ROOT'),("p['control_phase']==16 and p['completed_prefix_roots']==16","p['control_phase']==135 and p['completed_prefix_roots']==135 and p['source_owned_font_create_calls']==15"),('capture=out/level/f\'mode-{mode}\'','capture=STORAGE_ROOT/\'reports/m4-joint-startup138\'/name/level/f\'mode-{mode}\''),('timeout_seconds=180','timeout_seconds=420'),('inputs=list(pins));','inputs=list(pins),cwd=STORAGE_ROOT);'),('(1,1,1,1,16)','(1,1,1,1,135)'),('w[12]==16','w[12]==135'),('16*159716','135*159716'),('Sixteen complete selected prefix ABI records','135 complete selected prefix ABI records')]
 for a,b in subs:t=one(t,a,b);changes.append(dict(file='run_context_controls_v2.py',old=a,new=b))
 anchor="  b=json.loads(pin(build,build_sha).read_bytes());"
 storage="  storage_review=json.loads(pin(R/'reports/m4-tree-review/capture-storage-r1/report.json','74920256d02e000da908748ac96857a69cce60d20dad9ff9cd8e9ea87a3538b7').read_bytes());need(storage_review['passed']and storage_review['hash_index_payload_limits_and_stable_close_unchanged'],'Strict admitted fixed local storage root')\n  for q,h in storage_review['files'].items():pin(q,h)\n"
 t=one(t,anchor,storage+anchor);ast.parse(t);cp=R/'tools/m4-joint-startup138/run_context_controls_v2.py';
 if cp.exists():raise ValueError('Never replace existing controller')
 cp.write_text(t);pin(cp)
 checker=pin(R/'tools/m4-joint-startup138/check_context_controls.py');t=checker.read_text();t=t.replace('second-widget','post-creation widget').replace('eight-by-two','eight-by-two');t=one(t,"PH='0ef6894a8f17607d6c3d9908d618b3ce9516a1eae3c300390d67c2c11987da69'","PH='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'")
 # All occurrences here are actual explicit root or prefix identities.
 t=t.replace('0x40ef50','0x5a3ff0').replace('0x5fc838','0x736130').replace('0x5bb070','0x5bb52c')
 # The complete seven-slice inventory keeps the real second widget unchanged.
 t=one(t,"[0x40e250,0x5a3ff0,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0]","[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0]")
 replacements=[("p['control_phase']==16 and p['completed_prefix_roots']==16","p['control_phase']==135 and p['completed_prefix_roots']==135 and p['source_owned_font_create_calls']==15"),('second=roots[1];first=roots[0]','second=roots[5];first=roots[4];prefix_access_count=sum(v[12]for v in roots[:5]);prefix_GDI_count=sum(v[6]for v in roots[:5])'),('16*159716','135*159716'),("p['selected_order'][:16]","p['selected_order'][:135]"),('(1,1,1,1,16)','(1,1,1,1,135)'),('status[12]==16','status[12]==135'),('[1,1,0,16,0,status[3],0]','[1,1,0,135,0,status[3],0]'),('(1,mode,16,0x5a3ff0)','(1,mode,135,0x5a3ff0)'),('(1,1,1,16,0,status[3])','(1,1,1,135,0,status[3])'),('faultctx[7]==16','faultctx[7]==135'),('private[1]==1','private[1]==5'),("first[6]*1488","prefix_GDI_count*1488"),('len(owned)==5','len(owned)==15'),("len(start)==first[12]","len(start)==prefix_access_count"),('(0x5a013c,0x5bb52c,0,4,0)','(0x5ac11e,0x5bb52c,0,4,0)'),("counts['actual_owned_font_cleanup_calls']==80","counts['actual_owned_font_cleanup_calls']==240"),('summary[5]==16','summary[5]==Q(folder/\'retry-before/Registry/registry-summary.bin\',32)[5]')]
 for a,b in replacements:t=one(t,a,b);changes.append(dict(file='check_context_controls_v2.py',old=a,new=b))
 t=t.replace('five owned fonts','fifteen owned fonts').replace('Five actual current first-root owned fonts','Fifteen actual current source-created owned fonts').replace('All fifty actual first-root GDI source calls','All149 actual current prefix GDI source calls').replace('All and only five current manual','All and only fifteen current manual').replace('sixteen carried roots','135 carried roots').replace('Sixteen whole successful current Native records','135 whole successful current Native records').replace('Successful first-root','Successful pre-fault root')
 # A registry enter count is a provider-specific source count, not full table
 # root count. Require exact preservation, rather than mislabel that scalar.
 ast.parse(t);ck=R/'tools/m4-joint-startup138/check_context_controls_v2.py';
 if ck.exists():raise ValueError('Never replace existing semantic checker')
 ck.write_text(t);pin(ck);pin(R/'tools/m4-widget-growth-review/gdi_identity.py');pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Prepared unexecuted exact actual-owned-prefix controller and ordinary semantic checker; no fault observations or native acceptance',control_preparation=str(pp),control_preparation_sha256=sha(pp),controller=str(cp),controller_sha256=sha(cp),checker=str(ck),checker_sha256=sha(ck),exact_additive_substitutions=changes,owned_font_prefix_phase=134,owned_font_source_creations=15,control_phase=135,completed_prefix_roots=135,current_Context_fault_modes=8,full_ASM_hardware_restoration_bytes=[512,28],same_Context_full_observed_retry_required=True,partial_fault_register_prediction=False,storage_root='G:/Projects/MW34Recomp-Captures',archive_reader_opened=False,worker_launched=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
