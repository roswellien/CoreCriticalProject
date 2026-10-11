"""Prepare the additive final FSTP C1 bridge; retain all compiled bodies."""
from pathlib import Path
import hashlib,json,re,sys,traceback
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-native'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    assert re.fullmatch('fixture-preparation-r[1-9][0-9]*',name)
    out=B/name;assert not out.exists();out.mkdir();pins={};passed=False
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or v==h,p
        assert str(p) not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
    try:
        previous=pin(B/'fixture-preparation-r4/report.json','d237d05453b2ba32a6b70678f057340a32b78ad2e839c7c3bff4815bf5e69993')
        j=json.loads(previous.read_bytes());assert j['passed']
        for p,h in j['files'].items():pin(p,h)
        for f in ('CMakeLists.txt','control_runtime.cpp','fixture_spec_O0.hpp','fixture_spec_O2.hpp','generated_bridges.inc','literal_dispatch.hpp'):
            (out/f).write_bytes(pin(previous.parent/f).read_bytes())
        (out/'fixture.cpp').write_bytes(pin(R/'tools/m4-hypot-native/fixture_v3.cpp').read_bytes())
        pin(R/'tools/m4-hypot-native/derive_fixture_v3.py');pin(__file__);pin(sys.executable)
        for p in out.iterdir():pin(p)
        for p,h in pins.items():assert sha(p)==h,p
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(j,passed=passed,files=pins,
            scope='Finite final FSTP raw80 hardware rounding-bit bridge;21 literal bodies retained unchanged',
            previous_preparation=str(previous),previous_preparation_sha256=sha(previous),
            final_FSTP_C1_repair=dict(PC=0x4b5905,address=0x60b2e8,
                raw80_input_from_current_State=True,actual_source_CW=True,
                original_AFTER_seed=False,exact_hardware_F32_comparison=True),
            writer_launched=False,native_executed=False,initializer_credit=0)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
