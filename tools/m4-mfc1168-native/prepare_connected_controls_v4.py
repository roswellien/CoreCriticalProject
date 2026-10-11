"""Current controls with full true component-entry BEFORE retained."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;adapter=p/'prepare_connected_controls_v2.py';source=adapter.read_text();tail="exec(compile(text,str(parent),'exec'),globals())";assert source.endswith(tail+'\n')
scope={'__file__':str(adapter),'__name__':'prepare_adapter_only'};exec(compile(source[:-len(tail+'\n')],str(adapter),'exec'),scope);text=scope['text'];parent=scope['parent']
text=text.replace("R/'tools/m4-mfc1168-native/connected_controls.inc'","R/'tools/m4-mfc1168-native/connected_controls_v3.inc'")
marker="text=text[:text.index('int main(int argc,char**argv)')]"
insert="text=one(text,'namespace mc=mw34::m4_mfc1168_connected;','namespace mc=mw34::m4_mfc1168_connected;\\nstatic void mfc_control_entry(mw34::m4_runtime::Runtime&,State&);');text=one(text,'snapshot(r,c->s_,true);c->mfc_component_=','snapshot(r,c->s_,true);mfc_control_entry(r,c->s_);c->mfc_component_=');"+marker
assert text.count(marker)==1;text=text.replace(marker,insert)
text=text.replace("pin(sys.executable)","pin(R/'tools/m4-mfc1168-native/derive_connected_controls_v3.py');pin(R/'tools/m4-mfc1168-native/prepare_connected_controls_v4.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
