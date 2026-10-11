"""Admit only the explicitly proven 4B+4B TIB BEFORE representation join."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    old=ROOT/'tools/m4-startup131-paired/mfc_relations.py';new=old.with_name('mfc_relations_v2.py')
    assert sha(old)=='f867c5a82b6ec9e41bbb439c486e88e94883e361a62921714408788db7b3c858'and not new.exists()
    text=old.read_text();a="    b_memory = {int(a): bytearray.fromhex(b) for a, b in before['memory'].items()}"
    b=a+"""
    layout = native.get('TIB_region_representation', [])
    eq(len(layout), 1, 'One exact declared TIB representation adapter')
    adapter = layout[0]
    eq((adapter['address'], adapter['literal_extent']), (0x7ffde004, 8), 'Only source TIB004/008 may join')
    eq([(r['address'], r['bytes']) for r in adapter['original_parts']], [(0x7ffde004, 4), (0x7ffde008, 4)], 'Exact persistent four-byte parts')
    need(adapter['persistent_original_layout_restored'], 'Source restores original persistent region inventory')
    parts = []
    for part in adapter['original_parts']:
        raw = bytes(b_memory[part['address']])
        eq((len(raw), raw.hex()), (4, part['BEFORE_hex']), 'Each complete independent carried BEFORE part')
        parts.append(raw)
    joined = b''.join(parts)
    eq(joined.hex(), adapter['joined_BEFORE_hex'], 'Eight-byte literal input joins only computed BEFORE')
    b_memory[0x7ffde004] = bytearray(joined)
    del b_memory[0x7ffde008]"""
    assert text.count(a)==1;text=text.replace(a,b)
    a2="    native_fs = native['source_FS_writes']; original_fs = original['source_FS_writes']"
    b2="""    derived_tib = get(region_final, 0x7ffde004, 8)
    eq(derived_tib.hex(), adapter['source_AFTER_joined_hex'], 'Whole derived TIB endpoint joins source layout witness')
    eq([(r['address'], r['bytes'], r['source_AFTER_hex']) for r in adapter['source_AFTER_parts']], [(0x7ffde004, 4, derived_tib[:4].hex()), (0x7ffde008, 4, derived_tib[4:].hex())], 'Exact inverse persistent projection of the independently derived endpoint')
"""+a2
    assert text.count(a2)==1;text=text.replace(a2,b2)
    a3="        API_lifetimes=api_rows, native_whole_regions=region_rows, whole_module_input_relations=module_rows,"
    b3=a3+"\n        finite_TIB_region_representation=adapter,"
    assert text.count(a3)==1;text=text.replace(a3,b3);ast.parse(text);new.write_text(text)
    oldp=old.with_name('paired.py');newp=old.with_name('paired_v2.py');assert sha(oldp)=='145f5d9cb7442e6aac1869535d8072f34fd9e96d8522ff656bc970f8f978029e'and not newp.exists()
    s=oldp.read_text();pa="ROOT/'tools/m4-startup131-paired/mfc_relations.py'";pb="ROOT/'tools/m4-startup131-paired/mfc_relations_v2.py'";assert s.count(pa)==1;s=s.replace(pa,pb);ast.parse(s);newp.write_text(s)
    out=ROOT/'reports/m4-startup131-paired/comparer-preparation-r2';assert not out.exists();out.mkdir(parents=True)
    h=out/'hunks.json';h.write_text(json.dumps(dict(helper=[dict(old=a,new=b),dict(old=a2,new=b2),dict(old=a3,new=b3)],comparer=[dict(old=pa,new=pb)]),indent=2)+'\n')
    paths=[old,new,oldp,newp,old.with_name('tree_relations.py'),old.with_name('format_relations.py'),Path(__file__),h,ROOT/'reports/m4-startup131-paired/comparer-preparation-r1/report.json',ROOT/'tools/m4-startup131-original/export_reader.py']
    report=dict(passed=True,scope='Only finite independently computed BEFORE TIB004/008 join and exact derived inverse projection; accepted131 comparison obligations unchanged, no archive opened',comparer=str(newp.resolve()),comparer_sha256=sha(newp),helper=str(new.resolve()),helper_sha256=sha(new),files={str(p.resolve()):sha(p)for p in paths},capture_reader_opened=False,paired_executed=False,initializer_credit=0)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(q),comparer_sha256=sha(newp),helper_sha256=sha(new))))
if __name__=='__main__':main()
