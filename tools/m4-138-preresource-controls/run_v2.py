"""Final compile4/preparation3 binding; no invocation during readiness."""
from pathlib import Path
p=Path(__file__).with_name('run_v1.py');s=p.read_text()
for a,b in [('build-r2/build.json','build-r4/build.json'),('ba6a26b3af64a351057380507397999bb42ceb34d87c33627f8acc80235c6b6b','9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'),('typed_COFf_CALL_TLS_ownership','typed_COFF_CALL_TLS_ownership')]:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
