"""Single-layer additive adapter with correct inherited namespace placement."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v6.py');source=p.read_text()
source=source.replace('namespace {void Binding::formatting_guard()','void Binding::formatting_guard()').replace('formatting_owner_);}}}','formatting_owner_);}}')
anchor="one('pin(__file__)',";assert source.count(anchor)==1
injection='''one("(out/'formatting_operations.inc').write_bytes(pin(R/'tools/m4-formatting-native/formatting_operations.inc').read_bytes())", "(out/'formatting_operations.inc').write_text(pin(R/'tools/m4-formatting-native/formatting_operations.inc').read_text()[12:-2].replace('++formatting_dispatch_cursor_;','++formatting_dispatch_cursor_;stable_hook(89);').replace('++formatting_owned_cursor_;','++formatting_owned_cursor_;stable_hook(90);').replace('formatting_publication_records_.push_back({1,registry_root_,pc,address,value,a->generation,a->requested,a->extent,source_accesses_.size(),0,0,0});','formatting_publication_records_.push_back({1,registry_root_,pc,address,value,a->generation,a->requested,a->extent,source_accesses_.size(),0,0,0});stable_hook(88);'))")
'''
source=source.replace(anchor,injection+anchor).replace("pin(R/'tools/m4-formatting-native/prepare.py')\")","pin(R/'tools/m4-formatting-native/prepare.py');pin(R/'tools/m4-formatting-native/prepare_v6.py')\")")
exec(compile(source,str(p),'exec'),globals())
