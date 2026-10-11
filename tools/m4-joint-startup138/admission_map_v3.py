"""Same finite machine map, bound to measured GDI and actual growth build5."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
base=R/'tools/m4-joint-startup138/admission_map.py';s=base.read_text()
for a,b in [('m4-joint-startup138/build-r3','m4-joint-startup138/build-r5'),('b4cbd387ba718b52a900c5ff527749829f1936706c1b49c9e3a79a9765042ab6','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'),('connected-component-preparation-r1','connected-component-preparation-r4'),('17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae','c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21'),('connected-component-build-r1','connected-component-build-r4'),('602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99','d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119'),('m4-fps-native/service-preparation-r2','m4-fps-native/service-preparation-r3'),('d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2','cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9')]:
 assert a in s;s=s.replace(a,b)
s=s.replace("pin(__file__);pin(sys.executable)","pin(__file__);pin(base);pin(sys.executable)")
s=s.replace("'mw34_widget_hardware_call']","'mw34_widget_hardware_call','mw34::m4_widget_native::observe_gdi_identity','mw34::m4_widget_native::Component::Impl::provider_identity']")
s=s.replace("source_service=services['native_library'],","source_service=services['native_library'],source_service_preparation_sha256='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9',source_service_symbols=['mw34::m4_onexit::SessionImpl::borrow_widget_onexit'],")
exec(compile(s,str(base),'exec'),globals())
