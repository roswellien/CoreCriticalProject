"""Independent finite control recipe review; no worker or captured output."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh independent control recipe review');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Exact source/build input '+str(p));pins[str(p)]=v;return p
 def read(p,h):
  d=json.loads(pin(p,h).read_bytes());need(d['passed'],'Passed current receipt');return d
 PH='47af86a27b82f00b38b5da26eeb1017058f997d32bb89cac5d4ac81fa7a45663';BH='63f6d56ce07bba98a5ec1decdbaf3e061751393807c15b3aa625292d38d34017'
 p=read(R/'reports/m4-widget-native/controls-preparation-r1/report.json',PH);b=read(R/'reports/m4-widget-native/controls-build-r2/build.json',BH);coff=read(R/'reports/m4-tree-review/widget8-controls-prelaunch-r1/report.json','0f4769b062736fc17386e9d28ec6b5a44bbac8909bb01dc60f6a81444020449b');need(b['preparation_sha256']==PH and coff['preparation_sha256']==PH and coff['build_sha256']==BH,'Exact physical worker admission')
 for d in(p,b,coff):
  for q,h in d['files'].items():pin(q,h)
 source=pin(R/'reports/m4-widget-native/controls-preparation-r1/fixture.cpp').read_text();component=pin(R/'reports/m4-widget-native/preparation-r6/component.cpp').read_text();runtime=pin(R/'tools/m4-runtime/runtime.cpp').read_text();memory=pin(R/'runtime/memory/guest_memory.cpp').read_text();asm=pin(R/'tools/m4-widget-native/native_api.s').read_text();session=pin(R/'reports/m4-widget-native/service-preparation-r3/session_impl.inc').read_text();contract=json.loads(pin(R/'reports/m4-widget-native/preparation-r6/contracts.json').read_bytes());rows={v['pc']:v for v in contract['instructions']}
 need(source.index('registry.bootstrap()')<source.index('W::Component component(')<source.index('if(mode==1)')<source.index('component.execute(target,hardware)'),'Actual resources and accepted component precede authored faults')
 exact={1:'s.addr.ds_base.dword=4;',2:'s.aflag.df=1;r.cpu().eflags|=0x400;s.rflag.flat|=0x400;',3:'r.memory().store<unsigned>({0x5bb070},0);',4:'r.memory().store<std::uint8_t>({0x40e250},b^1);',5:'protect_image(0x5f4d78,Permissions::read);',6:'r.memory().protect({0x20001000},Permissions::read);',7:'r.memory().protect(r.fs_base(),Permissions::read);',8:'mode==8?0x40ef50:0x40e250'}
 for mode,text in exact.items():need(source.count(text)==1,'Exact unique authored mode '+str(mode))
 need(rows[0x40e250]['bytes_hex']=='e80b000000'and rows[0x40e250]['mnemonic']=='call'and rows[0x40e250]['implicit_memory'][0]['kind']=='stack-write','Physical40E250 source CALL is observed by committed write callback, not a register-only row');ir=pin(R/'reports/m4-widget-native/preparation-r6/f_40e250-host.ll').read_text();need(ir.index('@mw34_widget_game_write32(')<ir.index('@mw34_widget_game_direct_40e260('),'Initial real CALL write executes byte guard before callee dispatch')
 need(component.index('instruction(pc);access(pc,a,value,n,true);')<component.index('r.memory().write({a},std::span(b.data(),n));'),'Attempted scalar/FS ledger precedes memory write; permission-denied final row is not committed');need('Check the entire transfer before touching storage' in memory,'Failed GuestMemory write leaves whole backing unchanged')
 need(runtime.index('calls_.push_back(')<runtime.index('image_.memory.store<std::uint32_t>(GuestAddress{frame_sp}, return_pc.value)')<runtime.index('cpu_.esp = frame_sp; cpu_.eip = target.value;'),'Actual stack permission mode has call record but no completed CPU/frame commit');need('if (poisoned_) fail(FaultReason::poisoned' in runtime,'Retry admission checks actual poisoned Runtime')
 need(source.index('retry-before/')<source.index('component.execute(target,retry)')<source.index('retry-after/'),'Same actual context complete exported bytes before/after retry');need('r.calls().size()==captured_calls' in source,'Call count cannot advance on poisoned retry')
 for prefix in('retry-before/','retry-after/'):need(source.count(prefix)==1,'Exactly one current retry side prefix')
 need('whole_hidden_Runtime_private_retry_claim' in pin(R/'tools/m4-widget-native/prepare_controls_v1.py').read_text()and p['whole_hidden_Runtime_private_retry_claim']is False and p['whole_permissions_retry_claim']is False,'Observable private exports scope excludes hidden call vectors/permissions')
 need(asm.index('callq mw34_widget_invoke_guarded')<asm.index('fxrstor64 0(%rbx)')<asm.index('fxsave64 1088(%rbx)'),'Actual1632B guarded invoke/caught-exception restore with final raw snapshot');need('if(r.poisoned()&&!failed)poison();\n  InvocationHostBoundary host;'in session,'External Runtime poison precedes cleanup binding/publication')
 controller=pin(R/'tools/m4-widget-native/run_controls.py');checker=pin(R/'tools/m4-widget-native/check_controls.py');ast.parse(controller.read_text());ast.parse(checker.read_text());pin(__file__)
 report=dict(passed=True,scope='Independent source/control timing and exact finite mutation review, bound to separately reviewed final COFF workers; no actual fault observations yet',preparation_sha256=PH,build_sha256=BH,root_COFF_admission_sha256=sha(R/'reports/m4-tree-review/widget8-controls-prelaunch-r1/report.json'),control_modes_reviewed=8,source_byte_guard_Calls=1,actual_source_byte_guard_PC=0x40e250,positive_component_and_service_unchanged=True,permission_rejected_write_can_be_final_attempted_ledger=True,same_poisoned_context_retry=True,hardware_scope='Complete raw512/28 before/restored inside actual ASM invoke/catch boundary; later outer C++ EH hardware is unobserved',hidden_Runtime_private_byte_equality=False,permission_byte_equality=False,bootstrap_or_cleanup_source_equality=False,actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])
