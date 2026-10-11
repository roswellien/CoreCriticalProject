"""Reuse source-derived registry suffix for the newly included whole registry page."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2];files={};changes=[]
def pin(p):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip')and p.name not in('index.json','payload.bin','transport.json')
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 files[str(p)]=h;return p
prep=R/'reports/m4-startup138-original/inherited-source-preparation-r2/report.json';q=json.loads(pin(prep).read_text());assert q['passed']and q['exact_inverse_restores_parents']
for p,h in q['files'].items():assert files.get(str(pin(p)))==h
failure=pin(R/'reports/m4-startup138-original/inherited-source-r1-formatter4/report.json');f=json.loads(failure.read_text());assert not f['passed']
pin(failure.parent/'failure.txt')
parent=R/'tools/m4-startup138-original/format_source_v4_r2.py';original=pin(parent).read_text()
a="""            for page in preparation['observed_pages']+preparation['extra_whole_source_pages']:
                if page==0x20001000:continue
                after=raw[178404+preparation['observed_pages'].index(page)*4096:178404+(preparation['observed_pages'].index(page)+1)*4096]if page in preparation['observed_pages']else bundle.data(f'phase/{sequence}/{phase}/extra-after/{page}.bin');eq(machine.bytes(page,4096),after,'Whole literal mixed nonstack source page '+hex(page));counts['whole_literal_nonstack_pages']+=1
"""
assert original.count(a)==1;t=original.replace(a,'')
anchor="            for page,protect,type_ in meta:\n                predicted=bytearray(machine.bytes(page,4096))"
z="""            # The root endpoint follows registration; reuse the separately proven
            # literal cursor/begin suffix for the newly included CRT registry page.
            # Compare every untouched byte; source machine state is never seeded.
            for page in preparation['observed_pages']+preparation['extra_whole_source_pages']:
                if page==0x20001000:continue
                predicted=bytearray(machine.bytes(page,4096))
                if page==0x78037000:struct.pack_into('<II',predicted,0x888,new_begin+used+4,new_begin)
                after=raw[178404+preparation['observed_pages'].index(page)*4096:178404+(preparation['observed_pages'].index(page)+1)*4096]if page in preparation['observed_pages']else bundle.data(f'phase/{sequence}/{phase}/extra-after/{page}.bin');eq(bytes(predicted),after,'Whole literal mixed nonstack source page plus independently proven registry suffix '+hex(page));counts['whole_literal_nonstack_pages']+=1
"""
assert t.count(anchor)==1;t=t.replace(anchor,z+anchor)
inverse=t.replace(z,'');assert inverse.count(anchor)==1
# Restore the original loop at its exact original insertion point.
restore="            eq(machine.bytes(root['object'],root['object_extent'])"
assert inverse.count(restore)==1;inverse=inverse.replace(restore,a+restore);assert inverse==original
ast.parse(t);target=parent.with_name('format_source_v4_r3.py');assert not target.exists();target.write_text(t);pin(target)
aggregate=R/'tools/m4-startup138-original/current_inherited_source_v2_r2.py';old=pin(aggregate).read_text();text=old.replace('format_source_v4_r2.py','format_source_v4_r3.py').replace('inherited-source-preparation-r2','inherited-source-preparation-r3');assert text.replace('format_source_v4_r3.py','format_source_v4_r2.py').replace('inherited-source-preparation-r3','inherited-source-preparation-r2')==old
new=aggregate.with_name('current_inherited_source_v2_r3.py');assert not new.exists();new.write_text(text);pin(new);pin(__file__);pin(sys.executable)
out=R/'reports/m4-startup138-original/inherited-source-preparation-r3';assert not out.exists();out.mkdir()
delta=out/'formatter-registry-page-delta.json';delta.write_text(json.dumps(dict(parent=str(parent),target=str(target),removed_loop=a,inserted_loop=z,whole_page_gate_retained=True,expected_two_DWORDs_source_derived=True,source_machine_state_seeded=False,exact_inverse_restores_parent=True),indent=2)+'\n');pin(delta)
report=dict(passed=True,scope='Additive inclusion of current whole69 registry page after existing independent literal registration suffix proof',exact_inverse_restores_parent=True,capture_reader_opened=False,source_comparison_executed=False,initializer_credit=0,files=files)
p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
