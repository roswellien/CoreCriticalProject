"""Exact admitted physical provider paths (MSVCP50, staged CRT/MFC)."""
from pathlib import Path
p=Path(__file__).with_name('prepare_preresource_v1.py');s=p.read_text()
for a,b in [("m4-138-preresource-controls/preparation-r1","m4-138-preresource-controls/preparation-r2"),("MW3/MSVCP60.dll","local/mw3-staged/Shared_DLLs/MSVCP50.DLL"),("MW3/MSVCRT.dll","local/mw3-staged/Shared_DLLs/MSVCRT.DLL"),("MW3/MFC42.dll","local/mw3-staged/Shared_DLLs/MFC42.DLL")]:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
