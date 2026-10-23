"""Separate native Session entry counter from full108 callback vector length."""
from pathlib import Path
import ast,hashlib,json,shutil
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
parent=R/'reports/m4-joint-startup138-source/preparation-r10'
assert sha(parent/'report.json')=='2fd057d3f8c8e72332973952af2d3a663eee97e267a01234095123d2d40f8f63'
buildpath=R/'reports/m4-joint-startup138/build-r5/build.json'
assert sha(buildpath)=='7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'
build=json.loads(buildpath.read_bytes())
service=R/'reports/m4-fps-native/service-preparation-r3/session_impl.inc'
assert sha(service)==build['files'][str(service.resolve())]
raw=service.read_text()
borrow=raw[raw.index(' void borrow_widget_onexit('):raw.index('\n void finish(){')]
assert '++roots' not in borrow and 'registry-replay-' not in borrow
assert raw.count('++roots;')==2
assert 'capture("registry-replay-"+std::to_string(roots)+"-before")'in raw
out=R/'reports/m4-joint-startup138-source/preparation-r11';assert not out.exists();out.mkdir()
files={}
for p in parent.iterdir():
    if p.is_file()and p.name!='report.json':
        q=out/p.name;shutil.copyfile(p,q);files[str(q.resolve())]=sha(q)
q=out/'final_observer138.py';before=q.read_text()
old=".replace('registry-replay-{101+n}','registry-replay-{108+n}')"
assert before.count(old)==1
after=before.replace(old,'')
assert "len(roots)==108"in after and "selected_registration_closures']+=108"in after
q.write_text(after);files[str(q.resolve())]=sha(q)
for p in out.glob('*.py'):ast.parse(p.read_text())
for p in(parent/'report.json',parent/'final_observer138.py',service,buildpath,Path(__file__)):
    files[str(p.resolve())]=sha(p)
report=dict(passed=True,scope='Exact observer checkpoint naming only; full108 source callback vector, replay count/API/wholeState/FX/pages/cleanup guards retained',entrypoint=str(out/'compare_provider138.py'),parent_preparation_sha256=sha(parent/'report.json'),native_Session_entries=101,source_selected_callbacks=108,borrowed_widget_callbacks=7,source_callback_count_unchanged=True,checkpoint_inverse_restores_parent=after.replace(".replace(\"COUNTS['selected_registration_closures']+=101\",\"COUNTS['selected_registration_closures']+=108\")",old+".replace(\"COUNTS['selected_registration_closures']+=101\",\"COUNTS['selected_registration_closures']+=108\")")==before,archive_reader_opened=False,source_execution_performed=False,initializer_credit=0,files=files)
assert report['checkpoint_inverse_restores_parent']
rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');print(rp,sha(rp))
