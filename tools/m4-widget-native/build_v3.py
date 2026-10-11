"""Use the same DLL CRT linkage as the accepted caller-context COFFs."""
from pathlib import Path
p=Path(__file__).resolve().parent;v2=p/'build_v2.py';base=p/'build.py'
s=v2.read_text()
s=s.replace('exec(compile(s,str(base),\'exec\'),globals())',"s=s.replace(\"'-fexceptions','-fcxx-exceptions'\",\"'-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll'\")\ns=s.replace(\"for p in (clang,lib,nm,base,\",\"for p in (clang,lib,nm,v2,R/'tools/m4-widget-native/build_v3.ps1',base,\")\nexec(compile(s,str(base),'exec'),globals())")
exec(compile(s,str(v2),'exec'),globals())
