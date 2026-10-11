"""Same bounded admission schema, bound to the actual measured GDI build4."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
base=R/'tools/m4-joint-startup138/admission_map.py';s=base.read_text()
for a,b in [('m4-joint-startup138/build-r3','m4-joint-startup138/build-r4'),('b4cbd387ba718b52a900c5ff527749829f1936706c1b49c9e3a79a9765042ab6','ddef4da1943c6285bd462158da0e7360dcbf6a3bab40efe2247d7dea6e7c985a'),('connected-component-preparation-r1','connected-component-preparation-r4'),('17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae','c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21'),('connected-component-build-r1','connected-component-build-r4'),('602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99','d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119')]:
 assert a in s;s=s.replace(a,b)
s=s.replace("pin(__file__);pin(sys.executable)","pin(__file__);pin(base);pin(sys.executable)")
s=s.replace("'mw34_widget_hardware_call']","'mw34_widget_hardware_call','mw34::m4_widget_native::observe_gdi_identity','mw34::m4_widget_native::Component::Impl::provider_identity']")
exec(compile(s,str(base),'exec'),globals())
