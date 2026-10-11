"""Seal finite registered numeric refusals and complete caller boundary."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-native'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    assert re.fullmatch('fixture-preparation-r[1-9][0-9]*',name)
    out=B/name;assert not out.exists();out.mkdir();pins={};passed=False;j={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or v==h,p
        assert str(p) not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
    try:
        previous=pin(B/'fixture-preparation-r5/report.json','e7a734792e14ac54d0e6504c9f657a548d9cff38eee7efff4b7ccd83c4672d86')
        j=json.loads(previous.read_bytes());assert j['passed']
        for p,h in j['files'].items():pin(p,h)
        for f in ('CMakeLists.txt','control_runtime.cpp','fixture_spec_O0.hpp','fixture_spec_O2.hpp','generated_bridges.inc','literal_dispatch.hpp'):
            (out/f).write_bytes(pin(previous.parent/f).read_bytes())
        (out/'fixture.cpp').write_bytes(pin(R/'tools/m4-hypot-native/fixture_v5.cpp').read_bytes())
        assembly=pin(R/'tools/m4-hypot-native/hardware_boundary.s')
        compiler=pin(R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang.exe')
        object_=out/'hardware_boundary.obj'
        args=list(map(str,[compiler,'--target=x86_64-pc-windows-msvc','-c',assembly,'-o',object_]))
        r=subprocess.run(args,cwd=R,capture_output=True,timeout=30,creationflags=0x08000000)
        (out/'hardware-compile.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
        pin(object_)
        for level in ('O0','O2'):j['objects'][level]=list(j['objects'][level])+[str(object_)]
        j['hardware_boundary_compile']=dict(arguments=args,exit_code=r.returncode,object_sha256=sha(object_))
        pin(R/'tools/m4-hypot-native/derive_fixture_v4.py');pin(__file__);pin(sys.executable)
        for p in out.iterdir():pin(p)
        for p,h in pins.items():assert sha(p)==h,p
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(j,passed=passed,files=pins,
            scope='Finite registered native numeric root, finalC1 correction,actual8 causal refusals with unchanged same-context retries and complete ASM caller hardware restoration',
            previous_preparation=str(previous),previous_preparation_sha256=sha(previous),
            refusal_modes={'1':'source read address','2':'source access width','3':'source current PC','4':'literal source CALL target','5':'guest versus actual hardware CW','6':'control State identity','7':'FP exception mask','8':'source saved return identity'},
            retry_scope='Same actual poisoned Runtime/Context before and after second invoke; complete State/CPU/FX/pages/operands/frames/APIs/routes/private context unchanged',
            hardware_boundary_bytes=1632,writer_launched=False,native_executed=False,initializer_credit=0)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
