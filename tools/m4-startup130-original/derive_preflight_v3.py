from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent;root=p.parents[1];s=(p/'preflight_v2.py').read_text();build=root/'reports/m4-startup130-original/build-r2/build.json';h=hashlib.sha256(build.read_bytes()).hexdigest()
for a,b in [('preparation-r1','preparation-r2'),('89e159e71b3ae0a367bb33ee32c161cccae1aea45c005c2498c7e4e6ffb51af6','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'),('build-r1','build-r2'),('f1d29a95e80d91d282017339e0c7afd4676725f516b7b4e03b9c6e94d294d872',h)]:
 assert a in s;s=s.replace(a,b)
a="need('101*4,\"Exact101callback vector extent\"'in ref"
b="need('Exact restored named formatting IAT byte'in ref and p['format_final_protected_IAT_bytes_use_exact_named_targets'],'Twelve declared loaded IAT bytes are explicitly compared to exact named targets')\n  "+a
assert a in s;s=s.replace(a,b)
(p/'preflight_v3.py').write_text(s)
