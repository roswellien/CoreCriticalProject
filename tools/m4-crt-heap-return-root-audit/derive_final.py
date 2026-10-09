"""Construct the fresh read-only final auditor from sealed audit bodies."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent


def frozen(path, expected):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, str(path)
    return raw.decode().replace('\r\n','\n')


def replace(text, old, new):
    assert old in text, old[:100]
    return text.replace(old, new)


def main():
    old = frozen(ROOT/'tools/m4-crt-heap-version-root-audit/final.py',
        'aed591a105cd1c3a43ecdf5d9ef4a8841a8053e584f3b00d248f72260a3cd2b9')
    draft = frozen(HERE/'audit.py',
        'fb28b101f656ecb196100afa8bd457acdd6bf217888e7ad998052cf617abf0c6')
    text = old.replace('heap-version-root-audit','heap-return-root-audit')
    text = text.replace("core = ROOT/'tools/m4-crt-heap-version-root'", "core = ROOT/'tools/m4-crt-heap-return-root'")
    constants = draft[draft.index('SOURCE_SHA = '):draft.index('\n\ndef need(')]
    text = text[:text.index('SOURCE_SHA = ')] + constants + '\n\n' + text[text.index('def need('):]
    text = replace(text, "ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json'", "ROOT/'reports/m4-crt-heap-return-recovery/recovery-r1/report.json'")
    text = replace(text, "source = read(source_path)\n    need(source['passed'] and source['schema'] == 'mw34-m4-heap-version-static-recovery-v1','Exact sealed source contract')", "return_source = read(source_path)\n    need(return_source['passed'] and return_source['schema'] == 'mw34-m4-heap-return-static-recovery-v1','Exact sealed source contract')\n    source = read(add(ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json',\n        '90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f'))")
    text = replace(text, "ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json'", "ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json'")
    text = replace(text, "ROOT/'reports/m4-crt-heap-version-root/draft-r2/report.json'", "ROOT/'reports/m4-crt-heap-return-root/draft-r1/report.json'")
    text = replace(text, 'c749a38bcf0f5f9912c36829c1801553bd47c84dbaa42d042526c0ca527ef676', '609a694c7060283c6092f36a99fbc1c4df07e053000ef52f62aa2dafec59f56f')
    text = replace(text, '467d6ae1a1c570bd68cd14baf23e778aa15e5d1435a3088a1679fb255bd55a45', 'b35a16b60aa9e77d2b450379f677706dfbe83775ba92ac324c00b5a6ec017b54')
    text = replace(text, "ROOT/'reports/m4-crt-heap-version'", "ROOT/'reports/m4-crt-heap-return'")
    text = replace(text, "ROOT/'reports/m4-crt-heap-version-root'", "ROOT/'reports/m4-crt-heap-return-root'")
    text = replace(text, "observer['heap_mode_global_published'] is False", "observer['heap_mode_global_published'] is True")
    text = replace(text, "observer['heap_initializer_RET'] is False", "observer['heap_initializer_RET'] is True and observer['ordinary_initializer_RET_sequences'] == 48 and observer['fragment_caller_executed'] is False")
    insertion = """    for filename,digest in (
        ('ownership.py','bb812c5474934f520d421ac8fcc30ec2239b1a2c367feaaa66763ec229ef930d'),
        ('positive.py','1e5ae8d9fc0a5f56eb86890a03e9b57e7d3ecd3a65e7ec74ea7b491674fc845a'),
        ('observe.py','96578ab1803bac025ad9ce319f0f20bb7860bcc771bec92a681df35d38c10af2'),
        ('derive_observer.py','9e6c864e8194486c7aa0c2695df2e6c902422840b9f9310622905d8c1bb19b54')):
        add(core/filename,digest)
    add(Path(__file__).with_name('derive_final.py'))
"""
    text = replace(text, '    execution_path = add(', insertion+'    execution_path = add(')
    lo,hi = draft.index("    for instruction in return_source['spans']"),draft.index('    def stage(')
    text = replace(text, '    def stage(state,fx,cpu,memory):', draft[lo:hi]+'    def stage(state,fx,cpu,memory):')
    # Reuse our independently written affine source effects, never root expected code.
    lo,hi = draft.index('    def affine('),draft.index('    payloads = ')
    oldlo,oldhi = text.index('    def affine('),text.index('    payloads = ')
    text = text[:oldlo]+draft[lo:hi]+text[oldhi:]
    text = replace(text, 'index+121', 'index+133')
    text = replace(text, 'heap-version-job.bin', 'heap-return-job.bin')
    text = replace(text, "need(len(data) == 256,'Complete64DWORD immutable version job')", "need(len(data) == 288,'Complete72DWORD immutable return job')")
    text = replace(text, "job = struct.unpack('<64I',data)", "job = struct.unpack('<72I',data)")
    # Row-root active files are new; phase files retain their deliberately older names.
    for name in ('witness','registry','query-witness','lower-input','accesses','api-accesses','output-accesses','events','scheduler','undefined'):
        text = text.replace("row/'heap-version-"+name+".bin'", "row/'heap-return-"+name+".bin'")
    text = replace(text, "('heap-version-witness.bin','heap-version-registry.bin','heap-version-query-witness.bin')", "('heap-return-witness.bin','heap-return-registry.bin','heap-return-query-witness.bin')")
    text = replace(text, "(row/'query-input.bin').read_bytes(),(row/'query-output.bin').read_bytes()", "(row/'heap-return-query-input.bin').read_bytes(),(row/'heap-return-query-output.bin').read_bytes()")
    for name in ('create','destroy','query'):
        text = text.replace("API_identity(row,'heap-version-"+name+"'", "API_identity(row,'heap-return-"+name+"'")
    text = replace(text, '(0,0x20001858,0x20001860,31,2,11,5,10,0,0x78003a7f,0x780039e8,', '(0,0x20001858,0x20001860,35,2,13,5,10,0,0x78003a0b,0x78001843,')
    text = replace(text, 'eq(job[24:],(', 'eq(job[24:64],(')
    text = replace(text, "        outcome = dict(", "        eq(job[64:],(1,1,1,1,1,1,8,4),'Private genuine return progress fields')\n        outcome = dict(")
    text = replace(text, "tag.startswith(('heap-create-','heap-mode-','heap-version-'))", "tag.startswith(('heap-create-','heap-mode-','heap-version-','heap-return-'))")
    text = replace(text, "tag.startswith('heap-version-')", "tag.startswith(('heap-version-','heap-return-'))")
    text = replace(text, "'heap-create-after','entry-after-fault','retry-after'):\n                q[14:16]", "'heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'):\n                q[14:16]")
    text = replace(text, "'heap-create-after','entry-after-fault','retry-after'):\n                q[16:18]", "'heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'):\n                q[16:18]")
    text = replace(text, 'Current exact40-checkpoint inventory', 'Current exact44-checkpoint inventory')
    text = replace(text, "eq(len(phases),40,'Forty complete independently calculated phases')", "eq(len(phases),44,'Forty-four complete independently calculated phases')")
    text = replace(text, '**query_phase(tag,actual,derived))', '**query_phase(tag,actual,derived),**progress_phase(tag,actual))')
    text = replace(text, "(11,0x78003a7f,0x780039e8,0x20001854))", "(11,0x78003a7f,0x780039e8,0x20001854),\n            (12,0x780039eb,0x78035004,1),(13,0x78003a0b,0x78001843,0x20001858))")
    text = replace(text, "M.SLOT,M.RAW,*([0]*13),1,0,0,0x78003a7f,0x780039e8", "M.SLOT,M.RAW,*([0]*13),1,0,0,0x78003a0b,0x78001843")
    text = replace(text, "('heap-create-registry.bin','heap-mode-registry.bin')", "('heap-create-registry.bin','heap-mode-registry.bin','heap-version-registry.bin')")
    text = replace(text, "('filename','commandline','parser','locale','heap','heap-create','heap-mode')", "('filename','commandline','parser','locale','heap','heap-create','heap-mode','heap-version')")
    text = replace(text, "('mainargs','heap-version')", "('mainargs','heap-return')")
    text = replace(text, 'Genuine selector returned; heap mode publication remains unadmitted', 'Genuine heap initializer returned; fragment caller continuation remains unadmitted')
    text = replace(text, '(0,0x78003a7f,0x780039e8)', '(0,0x78003a0b,0x78001843)')
    # Prepare extension hooks; the new file is mutable until final actual receipt.
    text = replace(text, '    def native_observation(', '    def progress_phase(tag,actual):\n        return {}\n\n    def native_observation(')
    target = HERE/'final.py'
    assert not target.exists(), 'Fresh final auditor only'
    ast.parse(text)
    target.write_text(text, newline='\n')


if __name__ == '__main__':
    main()
