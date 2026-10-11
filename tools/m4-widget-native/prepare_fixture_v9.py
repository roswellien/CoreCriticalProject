"""Bind the exact completed literal epilogue tables without changing fixture code."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];previous=R/'tools/m4-widget-native/prepare_fixture_v8.py';s=previous.read_text()
for old,new in [('reports/m4-widget-native/preparation-r2','reports/m4-widget-native/preparation-r3'),('775828a192f57bf6e8fcf75fe629461402c7b8c367220f76ed9883c76c6f75b8','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5'),('reports/m4-widget-native/build-r4','reports/m4-widget-native/build-r5'),('ad9d4d5345d01429ff749bfabb9cce1e9cb6ff1d0b87716601083fa1a0c7d56c','9c053306dbf44a3a65ac1945dd4c2b0949ef064842004e05bf2e6cc29a22fada')]:s=s.replace(old,new)
s=s.replace("Path(__file__).resolve()]:bind(p)","previous,Path(__file__).resolve()]:bind(p)")
exec(compile(s,str(previous),'exec'),globals())
