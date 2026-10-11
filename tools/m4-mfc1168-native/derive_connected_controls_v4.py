"""Retain exact terminal facts and partial capture on the first refused assertion.

No control, component, assertion, or admitted source behavior is changed.
"""
from pathlib import Path
import hashlib

p = Path(__file__).parent
source = p / 'connected_controls_v3.inc'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '2eefaa7925101ab1359f86b780ae3afd480b1a7aeccfb4573077abdf266365c5'
text = source.read_text()
old = '  need(!guarded.completed&&context.failed()&&context.runtime().poisoned()&&context.completed==13&&records.size()==13&&!refusal.empty(),"Actual precise connected phase13 refusal after13complete roots");context.control_checkpoint("refused");'
new = '''  const auto actual_fault=context.fault();const unsigned terminal[]{1,mode,unsigned(guarded.completed),unsigned(context.failed()),unsigned(context.runtime().poisoned()),context.completed,unsigned(records.size()),unsigned(context.has_component()),actual_fault.phase,actual_fault.pc,actual_fault.address,actual_fault.step,actual_fault.kind};
  writer.append(prefix+"terminal-facts.bin",terminal,sizeof(terminal));
  const bool precise_refusal=!guarded.completed&&context.failed()&&context.runtime().poisoned()&&context.completed==13&&records.size()==13&&!refusal.empty();
  if(!precise_refusal){std::cerr<<"connected-control mode="<<mode<<" completed="<<guarded.completed<<" Context_failed="<<context.failed()<<" Runtime_poisoned="<<context.runtime().poisoned()<<" prior_roots="<<context.completed<<" retained_roots="<<records.size()<<" component="<<context.has_component()<<" reason="<<refusal<<'\\n';for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());const char failure[]="Connected assertion failed; partial facts only, no control completion or initializer credit\\n";writer.append("FAILED.txt",failure,sizeof(failure)-1);writer.finish();}
  need(precise_refusal,"Actual precise connected phase13 refusal after13complete roots");context.control_checkpoint("refused");'''
assert text.count(old) == 1
text = text.replace(old, new)
target = p / 'connected_controls_v4.inc'
assert not target.exists()
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest())
