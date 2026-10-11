"""Independent current connected controls admission using physical whole functions."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).parent
v11 = SCRIPTS / 'review_mfc1168_connected_native_prefix_v11.py'
program = v11.read_text()
tail = "exec(compile(text,str(BASE),'exec'),globals())"
assert program.endswith(tail + '\n')
program = program[:-len(tail + '\n')]
program = program.replace('partial=current_body_matches(rr,rl);assert len(partial)==1', "partial=current_body_matches(rr,rl)if any(r['symbol']['name']in bridge_targets for r in rl)else linked_candidates(image,rr,rl);assert len(partial)==1")
program = program.replace('len(source_targets)==6', 'len(source_targets)>=6').replace("counts['actual_missing_thunk_source_CALL_targets']+=6", "counts['actual_missing_thunk_source_CALL_targets']+=len(source_targets)")
names = ('?owner@m4_nmx_integration@mw34@@3PEAVSession@12@EA', '?owner@m4_spi_connected@mw34@@3PEAVSession@12@EA', '?active@m4_mfc1168_connected@mw34@@3PEAVInvocation@12@EA', '?emitter@?A0xC7D6B430@m4_mfc1168_connected@mw34@@3UEmitter@?A0xC7D6B430@12@A')
anchor = "extra=literal(V4,'extra')"
assert program.count(anchor) == 1
program = program.replace(anchor, 'helper=helper.replace("TLS_names={",' + repr('TLS_names={' + ','.join(repr(n) for n in names) + ',') + ')\n' + anchor)
program = program.replace("sym['value']==0 and len(storage)in(8,24)", "sym['value']in(0,8) and len(storage)in(8,24)").replace('storage[:8]', "storage[sym['value']:sym['value']+8]")
scope = {'__file__': str(__file__), '__name__': 'generate_review_only'}
exec(compile(program, str(v11), 'exec'), scope)
text = scope['text']

checks = r'''
  controls=pin(folder/'connected_controls.inc').read_text()
  assert prep['control_cases']==12 and not prep['worker_executed'] and not prep['execution_admitted']
  assert controls==pin(R/'tools/m4-mfc1168-native/connected_controls_v3.inc').read_text()
  assert 'snapshot(r,c->s_,true);mfc_control_entry(r,c->s_);c->mfc_component_='in main
  assert 'if(p->retry)'in main and 'FaultReason::poisoned'in main
  assert 'control_cleanup(){if(mfc_component_)mfc_component_->cleanup_failed();}'in main
  assert 'if(phase!=13)return;'in controls
  assert re.findall(r'case (\d+):',controls)==[str(i)for i in range(1,13)]
  for token in ('+2184','0x5f401083','0x5f498330','0x7ffdee1c','0x33005014','0x3300200c','0x33005000','0x33007000','0x7802e0c8','0x780379c0','0x5f4cb008','+2120'):
   assert token in controls,token
  for token in ('put("State.bin",&s,3504)','put("CPU.bin",&r.cpu(),40)','put("FX.bin",r.fx().data(),512)','put("Native.bin",mw34::m4_mixed::observation','add(r.fs_base().value,4)','add(r.fs_base().value+4,8)','add(r.fs_base().value+0x18,4)','mfc_retry_snapshot(context,writer,prefix+"retry-before/")','mfc_retry_snapshot(context,writer,prefix+"retry-after/")','context.completed==13&&records.size()==13','context.control_cleanup();context.control_checkpoint("cleaned")','context.registry().finish();','writer.finish();'):
   assert token in controls,token
  assert controls.count('mfc_connected_hardware_call(')==2
  assert 'records,false,false' in controls and 'records,false,true' in controls
  counts['whole_authored_public_faults']=12
  counts['whole_true_source_entry_observer']=1
'''
physical = r'''
   for prefix in ('main','?mfc_mutate@@','?mfc_retry_snapshot@@','?mfc_control_entry@@'):
    candidates=[s['name']for s in sy.values()if s['name'].startswith(prefix)and s['section']>0 and s['type']==32]
    if not candidates:
     assert level=='O2'and prefix=='?mfc_control_entry@@';counts['entry_observer_inlined_in_whole_MFC_entry']+=1;continue
    assert len(candidates)==1,prefix
    raw,relocs=C.function(sy,se,candidates[0]);matches=linked_candidates(image,raw,relocs);assert len(matches)==1,(prefix,len(matches))
    TLS_relations(image,raw,matches[0][1],relocs,se)
    links.append(dict(level=level,symbol=candidates[0],address=matches[0][0],whole_bytes=len(raw),relocation_DWORDs=len(relocs)));counts['whole_linked_control_functions']+=1
'''
edits = [
 ("'7f426089ae1c974d4e2b5c3e5500efe283d8634a54e6d934a428710fe078d309'", "'471ea9a86b44f9bc5c0453190421da0b00ab33c2d33a27cc3677700bbcbf2025'"),
 ("'a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924'", "'430db97c6b4f495a409288269f297faac8aab6e2d818c2f020bae71ed166ab51'"),
 ('connected-fixture-build-r2/build.json','connected-controls-build-r3/build.json'),
 ('const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}}', 'mfc_control_entry(r,c->s_)'),
 ("  assert 'mfc_connected_hardware_call(&guarded,mfc_hardware.data())'in main and 'writer.append(prefix+\"MFC-caller-hardware.bin\"'in main", checks),
 ("   db=pin(bf/'.ninja_deps')", physical + "   db=pin(bf/'.ninja_deps')"),
 ("  pin(BASE);pin(V2);pin(V3);pin(V4);", "  pin(BASE);pin(V2);pin(V3);pin(V4);pin(R/'tools/m4-tree-review/review_mfc1168_connected_native_prefix_v11.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_native_prefix_v14.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_native_prefix_v15.py');pin(R/'tools/m4-mfc1168-native/run_connected_controls.py');"),
 ('Independent first positive connected14 prefix prelaunch only', 'Independent current connected12 refusal worker physical prelaunch'),
]
for before, after in edits:
 assert text.count(before)==1,(before,text.count(before))
 text=text.replace(before,after)
exec(compile(text,str(__file__),'exec'),globals())
