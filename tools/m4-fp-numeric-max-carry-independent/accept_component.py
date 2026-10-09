"""Root closure for the canonical numeric component; no joint startup credit."""
import hashlib,importlib.util,json,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def stage(name,rh,ph):
    base=ROOT/'reports/m4-fp-numeric-max-carry'/name;r=json.loads(pin(base/'report.json',rh).read_text());assert r['passed']
    pins=json.loads(pin(base/'pins.json',ph).read_text())['files']
    for p,h in pins.items():pin(p,h)
    return r
def main(out):
    assert out.parent==ROOT/'reports/m4-fp-numeric-max-carry' and not out.exists();out.mkdir();(out/'acceptance-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        author=stage('author-canonical-review-r1','624cedf34d980780016afac8de7234e9d3aa8cd29269c82f644caff276506ae7','e1beea2b51f3059897da62bc2aec85832a12ff5cdd19fd767cdfa8b3353c7f10')
        peer=stage('independent-canonical-closure-r1','4bba2d6167d14e371153b78ed12261209951fb0271e494f1601362ada6214395','296cad9283fb38266e2aa7f3157ea4a7977a98f1552a3358f6deb422412a9cf3')
        carry=stage('independent-carry-model-r3','3abf644643a492bdd25f1e51a72f11df0da848ad26607452f890ac22b8f2c5f0','ba9b8c41bfb5d9c13a9a03f4917b93963131dd50f49b90f5b415541807903b5b')
        narrow=stage('independent-narrow-persistent-r1','23c58213350a85d7876bd203a865f6650bd9ea7aed3a715044b5dff4d67f2dce','12ffdd431fac6bcb7003270ee5cf3547329a9bc5ea9f8239a9bfee6725b189c8')
        replay=stage('independent-narrow-replay-r1','5998adc521615d520c4639ed0a5dd02ae701b209babbe3181e10df78c948d113','6ff278f2906cd0c067c13bca10f55cc622af603f211a1fcd6ba386cfb23768cb')
        assert (carry['native_records'],narrow['native_records'],replay['native_records'])==(41472,864,14688)
        assert peer['actual_compiled_checks']==136208 and peer['malformed_shadow_cases']==176 and peer['direct_hardware_records']==2832
        delta=author['source_delta'];before=pin(delta['previous'],delta['previous_sha256']).read_text();after=pin(delta['candidate'],delta['candidate_sha256']).read_text()
        canonical='for(const auto byte:std::array<std::uint8_t,11>{s_.sw.ie,s_.sw.de,s_.sw.ze,s_.sw.oe,s_.sw.ue,s_.sw.pe,s_.sw.sf,s_.sw.c0,s_.sw.c1,s_.sw.c2,s_.sw.c3})if(byte>1)deny("Noncanonical FP shadow flag byte rejected");'
        assert after.count(canonical)==1 and after.replace(canonical,'')==before,'Exactly eleven-byte admission check before projection, no normalization'
        assert after.index(canonical)<after.index('auto sw=status(s_),top=(sw>>11)&7;')
        assert 's_.sw.c1=0; /* FLD has no stack overflow in this admitted domain. */' in after
        for token in ('fxsave64','fnstenv','fninit','fldcw','ldmxcsr','fxrstor64','fldenv','bool invoke(','noexcept'):assert token in after
        model_path=pin(ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/persistent_model.py','86fa5de668633b1073415ebfc6cbbabc82557df4d677fe308ad5df13d1d364a8')
        spec=importlib.util.spec_from_file_location('root_accept_host',model_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        controls=[];positive=[];spans=list(range(5))+list(range(24,28))+[32+16*i+j for i in range(8) for j in range(10)]
        for level in ('O0','O2'):
            path=pin(ROOT/f'reports/m4-fp-numeric-max-carry/native-canonical-r1/unit-{level}/carry.bin')
            with path.open('rb') as f:f.seek(24);row=f.read(46688)
            cw=struct.unpack_from('<I',row,12)[0];m.host_boundary(row,cw)
            for offset in [45068+i for i in spans]+[45580+i for i in spans]+list(range(46092,46148)):
                bad=bytearray(row);bad[offset]^=1
                try:m.host_boundary(bad,cw)
                except ValueError:controls.append(dict(level=level,offset=offset,rejected=True))
                else:raise AssertionError('Direct numerical host corruption accepted')
            for offset in (45580+160,45580+166,45580+42,45580+480):
                b=bytearray(row);b[offset]^=1;m.host_boundary(b,cw);positive.append(dict(level=level,offset=offset,volatile_or_padding_scope=True))
        tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a');decodes=[]
        for level in ('O0','O2'):
            path=pin(ROOT/f'reports/m4-fp-numeric-max-carry/native-canonical-r1/native-{level}.obj');command=[str(tool),'-dr','--unwind-info',str(path)]
            cp=subprocess.run(command,capture_output=True);(out/f'{level}-guest-coff.txt').write_bytes(cp.stdout);(out/f'{level}-guest-coff.stderr').write_bytes(cp.stderr);assert cp.returncode==0
            text=cp.stdout.decode();assert 'coff-x86-64' in text and 'mw34_nmx_fld_commit' in text and 'mw34_nmx_fstp_commit' in text
            decodes.append(dict(level=level,path=str(path),sha256=sha(path),command=command))
        for path in (ROOT/'tools/m4-runtime/runtime.hpp',ROOT/'tools/m4-runtime/runtime.cpp'):pin(path)
        for p in (ROOT/'reports/m4-fp-numeric-max-carry/root-component-acceptance-r1').iterdir():
            if p.is_file():pin(p)
        pin(ROOT/'docs/m4-fp-numeric-max-canonical-acceptance.md');pin(__file__);pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,component_accepted=True,scope='Root bounded canonical numeric component acceptance only; full initializer integration remains unaccepted',native_phases=57024,events=1254528,routes=171072,original_BEFORE_seeded_native_replays=14688,carry_phases=41472,persistent_boundaries=carry['persistent_boundaries'],authored_hardware_checkpoints=carry['own_authored_hardware_checkpoint_comparisons'],independent_compiled_checks=136208,independent_malformed_shadow_denials=176,independent_direct_host_records=2832,own_additional_host_controls=controls,own_additional_scope_positives=positive,exact_canonical_source_delta=True,fresh_root_COFF_associations=decodes,physical_bindings=len(PINS),production_header_sha256=delta['candidate_sha256'],shared_runtime_r9_unchanged=True,original_process_executed_by_this_checkpoint=False,accepted_invocation_scope='Owned Session.invoke; raw Runtime.call_direct is outside caller numerical preservation scope',identity_scope='Current disk/source/header associations; not complete execution-time process/dependency attestation',domain='16binary32/12maskedIC0CW/TOP0or7/depth0or1or7/sticky0orDEorPEorDEPE/C1{0,1}',selected_joint_initializer_roots=26,new_joint27_preparation_allowed=True,joint27_execution_still_requires_concrete_recipe_review=True,full_CRT=False,full_startup=False,frontend=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,component_accepted=True,physical_bindings=len(PINS),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
