"""Admit the diagnostic-only revision while preserving every control predicate."""
from pathlib import Path

previous = Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v3.py')
program = previous.read_text()
anchor = "exec(compile(program,str(previous),'exec'),globals())"
assert program.count(anchor) == 1
diagnostic_checks = r'''
  import difflib
  previous_controls=pin(R/'tools/m4-mfc1168-native/connected_controls_v3.inc').read_text()
  old_line='  need(!guarded.completed&&context.failed()&&context.runtime().poisoned()&&context.completed==13&&records.size()==13&&!refusal.empty(),"Actual precise connected phase13 refusal after13complete roots");context.control_checkpoint("refused");'
  replacement=''' + repr('''  const auto actual_fault=context.fault();const unsigned terminal[]{1,mode,unsigned(guarded.completed),unsigned(context.failed()),unsigned(context.runtime().poisoned()),context.completed,unsigned(records.size()),unsigned(context.has_component()),actual_fault.phase,actual_fault.pc,actual_fault.address,actual_fault.step,actual_fault.kind};
  writer.append(prefix+"terminal-facts.bin",terminal,sizeof(terminal));
  const bool precise_refusal=!guarded.completed&&context.failed()&&context.runtime().poisoned()&&context.completed==13&&records.size()==13&&!refusal.empty();
  if(!precise_refusal){std::cerr<<"connected-control mode="<<mode<<" completed="<<guarded.completed<<" Context_failed="<<context.failed()<<" Runtime_poisoned="<<context.runtime().poisoned()<<" prior_roots="<<context.completed<<" retained_roots="<<records.size()<<" component="<<context.has_component()<<" reason="<<refusal<<'\\n';for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());const char failure[]="Connected assertion failed; partial facts only, no control completion or initializer credit\\n";writer.append("FAILED.txt",failure,sizeof(failure)-1);writer.finish();}
  need(precise_refusal,"Actual precise connected phase13 refusal after13complete roots");context.control_checkpoint("refused");''') + r'''
  assert previous_controls.count(old_line)==1
  assert controls==previous_controls.replace(old_line,replacement),''.join(difflib.unified_diff(previous_controls.splitlines(True),controls.splitlines(True)))
  counts['whole_diagnostic_only_delta']=1
'''
injection = "\nsource=source.replace('471ea9a86b44f9bc5c0453190421da0b00ab33c2d33a27cc3677700bbcbf2025','3f58e9ef746d10f77ccb34c7081dcc16aa007247d6c86fc3da6634b71036cd3c')\n"
injection += "source=source.replace('430db97c6b4f495a409288269f297faac8aab6e2d818c2f020bae71ed166ab51','ecfadc502d353d00afee039ff292733ee9c43601bb629969cd752c9a62debf48')\n"
injection += "source=source.replace('connected-controls-build-r3/build.json','connected-controls-build-r4/build.json').replace('connected_controls_v3.inc','connected_controls_v4.inc')\n"
injection += "source=source.replace(\"checks = r'''\",\"checks = r'''\"+" + repr(diagnostic_checks) + ")\n"
injection += "source=source.replace(\"pin(R/'tools/m4-mfc1168-native/run_connected_controls.py');\",\"pin(R/'tools/m4-mfc1168-native/run_connected_controls.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v3.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v4.py');\")\n"
v2_anchor = "exec(compile(source,str(parent),'exec'),globals())"
program = program.replace(anchor, "program=program.replace("+repr(v2_anchor)+","+repr(injection+v2_anchor)+");"+anchor)
exec(compile(program,str(previous),'exec'),globals())
