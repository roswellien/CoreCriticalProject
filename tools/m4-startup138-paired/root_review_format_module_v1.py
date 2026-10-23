"""ROOT admission of finite formatter module partition; no capture reader."""
from pathlib import Path
import hashlib, importlib.util, json
R=Path(__file__).resolve().parents[2]
pins={}
def pin(p,h=None):
 p=Path(p).resolve()
 with p.open('rb') as f:v=hashlib.file_digest(f,'sha256').hexdigest()
 assert h is None or v==h,(str(p),v,h)
 pins[str(p)]=v
 return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def closure(p,h=None):
 v=read(p,h);assert v['passed']
 for q,s in v['files'].items():pin(q,s)
 return v
v=closure(R/'reports/m4-startup138-paired/format-module-preflight-r2/report.json','6499700d4d77dc7e6e0b15df5d948d7693230db9ba10fc492d156176abd1fbfc')
assert (v['original_source_cases'],v['native_source_cases'],v['typed_registrar_rows'],len(v['adverses']))==(24,48,72,504)
assert v['all_game_static_rows_retained'] and v['all_game_static_order_pairs_equal'] and not v['archive_reader_opened'] and not v['whole_pair_run']
new=pin(R/'tools/m4-startup138-paired/format_relations_v4.py','c1f7c77d823fc4926f2e25f45fa8610f48b08751f1cef91d29fadea1440c90a8')
text=new.read_text()
d=closure(R/'reports/m4-startup138-paired/format-module-preparation-r3/report.json')
old,newtext=d['delta']['old'],d['delta']['new'];assert text.count(newtext)==1;text=text.replace(newtext,old)
assert text==pin(R/'tools/m4-startup138-paired/format_relations_v3.py').read_text()
for version,target in ((2,'format_relations_v2.py'),(1,'../m4-startup131-paired/format_relations.py')):
 d=closure(R/f'reports/m4-startup138-paired/format-module-preparation-r{version}/report.json')
 delta=read(R/f'reports/m4-startup138-paired/format-module-preparation-r{version}/exact-delta.json')
 for old,newtext in reversed(delta):assert text.count(newtext)==1;text=text.replace(newtext,old)
 assert text==pin(R/'tools/m4-startup138-paired'/target).read_text()
# Retained literal source/provider gates independently remain closed.
closure(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052')
closure(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4')
# Independent second run authenticates physical PE ownership and all actual
# journals, not the recorded success boolean. Opens ordinary JSON/PE only.
p=pin(R/'tools/m4-startup138-paired/preflight_format_module_v2.py')
s=importlib.util.spec_from_file_location('root_format_preflight',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.main('format-module-root-measured-r1')
measured=closure(R/'reports/m4-startup138-paired/format-module-root-measured-r1/report.json')
assert measured['typed_registrar_rows']==72 and len(measured['adverses'])==504
pin(__file__)
out=R/'reports/m4-startup138-paired/format-module-root-review-r1';assert not out.exists();out.mkdir()
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope='Physical Game section ownership and exact three CRT publication roles; whole Game byte relations retained, separate whole CRT/source/provider gates remain mandatory',exact_inverse_restores_accepted131_helper=True,source_cases=48,separate_CRT_publications=72,refused_adverses=504,full_pair_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(pin(q))
