"""Fresh52 component pins actual DLL compiler and restored historical inputs."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];prior=R/'tools/m4-widget-native/prepare_v4.py';s=prior.read_text()
a="pin(__file__);pin(R/'tools/m4-widget-native/build_v3.py');pin(R/'tools/m4-widget-native/build_v3.ps1')"
b="pin(__file__);pin(prior);pin(R/'tools/m4-widget-native/build52_v2.py');pin(R/'tools/m4-widget-native/build52_v2.ps1');pin(R/'tools/m4-widget-native/build_v3.py','5d92064c4a7b8cf923a35ec22f15bb81760f983f7ad3366d926e21c4c6c68cef');pin(R/'tools/m4-widget-native/build_v3.ps1','9296567e295a538a635ba853ee4061c963c631a494fd4674c3cfb75098b91a9d');pin(R/'reports/m4-widget-native/compiler-wrapper-recovery-r1/report.json','2a493def893b90a189633a27460b2ef1b465acfa97346b5661d3bee3d2c4e1ba')"
assert s.count(a)==1
exec(compile(s.replace(a,b),str(prior),'exec'),globals())
