"""Add the omitted retained actual-link graph block to the immutable extraction."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('prepare_schema_checker_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f30f5e8eff6bf2f14a613871134a3c48371991b74ada71d92de9df0d8277a4bf'
s=p.read_text()
changes=[
 (" 'native-inputs.py':cut(s,", " 'native-graph.py':cut(s,\"   assert len(prep['objects']\",\"   component_object=pin(\"),\n 'native-inputs.py':cut(s,"),
 (" 'native-inputs.py':[], 'native-boundary.py':[]}"," 'native-inputs.py':[], 'native-boundary.py':[], 'native-graph.py':[]}"),
 ("check_schema138_v1.py","check_schema138_v2.py"),
 ("pins[str(Path(__file__).resolve())]=sha(__file__)","pins[str(Path(__file__).with_name('prepare_schema_checker_v1.py').resolve())]=sha(Path(__file__).with_name('prepare_schema_checker_v1.py'));pins[str(Path(__file__).with_name('check_schema138_v1.py').resolve())]=sha(Path(__file__).with_name('check_schema138_v1.py'));pins[str(Path(__file__).resolve())]=sha(__file__)")]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
