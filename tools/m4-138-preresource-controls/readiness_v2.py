"""Final exact current four providers and complete carried journal scope."""
from pathlib import Path
p=Path(__file__).with_name('readiness_v1.py');s=p.read_text()
for a,b in [('readiness-r1','readiness-r2'),('preparation-r1/report.json','preparation-r3/report.json'),('153435fdcb184b64fe9a2b39e30bcb50b4e773dc02f0cd64f2efcfc239b91bbb','8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'),('build-r2/build.json','build-r4/build.json'),('ba6a26b3af64a351057380507397999bb42ceb34d87c33627f8acc80235c6b6b','9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f')]:assert s.count(a)==1;s=s.replace(a,b)
assert s.count('run_v1.py')==2;s=s.replace('run_v1.py','run_v2.py')
needle="for p in [Path(__file__).resolve(),"
s=s.replace(needle,"for p in [Path(__file__).with_name('readiness_v1.py'),R/'tools/m4-138-preresource-controls/run_v1.py',R/'tools/m4-138-criteria-frontier/prepare_preresource_v1.py',R/'tools/m4-138-criteria-frontier/prepare_preresource_v3.py',Path(__file__).resolve(),")
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
