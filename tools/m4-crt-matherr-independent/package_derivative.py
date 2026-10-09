"""Add public-safe root review derivatives without changing frozen evidence."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/m4-crt-matherr/public-package-derivative-r1'
TOOLS = ROOT / 'tools/m4-crt-matherr-independent'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert not OUT.exists()
    expected = {
        'original_model.py': '492647c15e2622078577f96f22de7af12c92a95158503da25e6bba71b97ee24d',
        'native_model.py': '1c3b67c819b4d5bfd200f1070c4a78f355b3db2457803585cc4835e0b02cb477',
    }
    for name, h in expected.items():
        assert sha(TOOLS / name) == h
    OUT.mkdir(parents=True)
    for name in expected:
        (OUT / name).write_bytes((TOOLS / name).read_bytes())
    text = (TOOLS / 'original_model.py').read_text()
    lines = text.splitlines()
    assert sum("need(source==bytes.fromhex(" in x for x in lines) == 1
    assert sum("need(at(game,game_raw,0x5ac423,11)==bytes.fromhex(" in x for x in lines) == 1
    lines = [x for x in lines if "need(source==bytes.fromhex(" not in x]
    for i, line in enumerate(lines):
        if "need(at(game,game_raw,0x5ac423,11)==bytes.fromhex(" in line:
            lines[i] = "    caller=at(game,game_raw,0x5ac423,11)\n    need(hashlib.sha256(caller).hexdigest()=='ed4e3e4ef3536ad0d20aab36b55f011878b9bc1e9bd9760631ee5a4fb5b4456e','Exact private static caller span identity')\n    need(caller[0]==0x68 and word(caller,1)==0x51e7b0 and caller[5]==0xff and caller[6]==0x15 and word(caller,7)==0x5bb50c,'Actual PUSH callback and named indirect CALL operands')"
    text = '\n'.join(lines) + '\n'
    anchor = "    dest=out/'provider-decode.txt';dest.write_text(result.stdout,encoding='utf-8');pin(dest)"
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + "\n    import re\n    decoded=[]\n    for line in result.stdout.splitlines():\n        match=re.match(r'^\\s*([0-9a-f]+):\\s*((?:[0-9a-f]{2}\\s+)+)\\s*([a-z][a-z0-9]*)\\s*(.*)$',line)\n        if match:\n            address=int(match[1],16);body=bytes.fromhex(match[2]);need(at(provider,provider_raw,address,len(body))==body,'Fresh decode matches exact private bytes');decoded.append((address,len(body),match[3],match[4].strip()))\n    need(decoded==[(ENTRY,4,'mov','eax, dword ptr [esp + 0x4]'),(ENTRY+4,7,'and','dword ptr [0x780392b8], 0x0'),(ENTRY+11,5,'mov','dword ptr [0x7803b0c4], eax'),(ENTRY+16,1,'ret','')],'Complete independently decoded four-instruction source operands')")
    original = TOOLS / 'original_model_safe.py'
    assert not original.exists()
    original.write_text(text, encoding='utf-8', newline='\n')
    native_text = (TOOLS / 'native_model.py').read_text()
    old = next(x for x in native_text.splitlines() if "spec_from_file_location('own_root_matherr_original'" in x)
    new = "        path=ROOT/'tools/m4-crt-matherr-independent/original_model_safe.py';spec=importlib.util.spec_from_file_location('own_root_matherr_original_safe',pin(path,'" + sha(original) + "'));original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)"
    native_text = native_text.replace(old,new)
    native = TOOLS / 'native_model_safe.py'
    assert not native.exists()
    native.write_text(native_text, encoding='utf-8', newline='\n')
    for name,h in expected.items():
        assert sha(TOOLS/name)==sha(OUT/name)==h
    report = dict(passed=True,scope='Additive public-source packaging repair; frozen technical evidence unchanged',historical=expected,derivatives={str(p):sha(p) for p in (original,native)},changes=['Private span hash and actual operand/decode checks replace public full instruction byte literals','Fresh native model imports only the new root-owned safe original model'],proof_execution_pending=True,whole_M4_complete=False)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'recipe-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(report))

if __name__ == '__main__':
    main()
