"""Exact existing connected builder, full131 composition/output namespace."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1]/'m4-mfc1168-native';parent=p/'build_connected_fixture_v3.py';source=parent.read_text()
old="text=text.replace(needle,edit+needle);exec(compile(text,str(parent),'exec'),globals())"
new="""edit+='text=text.replace(\"R/\\\'reports/m4-mfc1168-native\\\'/name\",\"R/\\\'reports/m4-joint-startup131\\\'/name\");text=text.replace(\"mw34_mfc1168_connected.exe\",\"mw34_joint_startup131.exe\");text=text.replace(\"Current130 derived connected14 prefix Context compiled O0/O2 with410 literal objects; no worker execution\",\"Full131 persistent Context compiled O0/O2 with410 reused literalobjects,101callbacks/132translations/134selectedcalls; no worker execution\");text=text.replace(\"pin(sys.executable)\",\"pin(R/\\\'tools/m4-joint-startup131/build.py\\\');pin(R/\\\'tools/m4-joint-startup131/build.ps1\\\');pin(sys.executable)\");\\n'
text=text.replace(needle,edit+needle);exec(compile(text,str(parent),'exec'),globals())"""
assert source.count(old)==1;source=source.replace(old,new)
exec(compile(source,str(parent),'exec'),globals())
