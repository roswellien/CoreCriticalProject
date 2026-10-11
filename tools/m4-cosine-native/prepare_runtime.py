"""Additive Runtime callback from the tested compound-FCOS source and IR."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, digest=None):
        path = Path(path).resolve()
        value = sha(path)
        assert digest is None or digest == value, path
        pins[str(path)] = value
        return path

    source_receipt = pin(AREA / 'fixture-source-r1/report.json',
        '7f8ed5dd50a62574ce404cdd2081e592ab4cd111cd4423e2ef668e5367929045')
    assert json.loads(source_receipt.read_bytes())['passed']
    comparison = pin(AREA / 'fixture-comparison-r3/report.json',
        'f65f414b929c9cedec5d34b6376b9e771a710a98f79e667550c28a143b950955')
    original_review = pin(ROOT / 'reports/m4-tree-review/cosine-original-r1/report.json',
        '159779a7126e49e0ec6a1487dc307fec1f04afe7894e45af3bf10e7a4d100b14')
    for path in (comparison, original_review):
        assert json.loads(path.read_bytes())['passed']
    base = AREA / 'fixture-preparation-r1'
    code = pin(base / 'native.cpp').read_text()
    code = code[:code.index('int main(')]
    assert code.count('#include "fixture_spec.hpp"') == 1
    code = code.replace('#include "fixture_spec.hpp"', '#include "' + (base / 'fixture_spec.hpp').as_posix() + '"')
    pin(base / 'fixture_spec.hpp')
    assert code.count('constexpr std::uint32_t frame=0x20001800,sentinel=0x410a80;') == 1
    code = code.replace('constexpr std::uint32_t frame=0x20001800,sentinel=0x410a80;',
                        'static thread_local std::uint32_t frame{},sentinel{};')
    before = 'if(!ok){fault();return 0;}++reads;log(address,value,8,0);return value;'
    assert code.count(before) == 1
    # Inputs are the physical default game doubles, never derived from an
    # observed trigonometric result. The later Runtime gate checks their carry.
    contract_path = pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/instruction-contracts.json')
    contracts = json.loads(contract_path.read_bytes())
    inputs = contracts['inputs']
    checks = 'switch(address){' + ''.join(
        'case ' + hex(item['address']) + ':if(value!=' + str(item['bits']) + 'ULL){fault();return 0;}break;'
        for item in inputs) + 'default:fault();return 0;}'
    code = code.replace(before, 'if(!ok){fault();return 0;}' + checks + '++reads;log(address,value,8,0);return value;')
    code = code.replace('mw34::m4_fp_cosine_native', 'mw34::m4_fp_compound_native')
    wrapper = '''
#include "joint_protocol.hpp"
namespace mw34::m4_mixed {
void compound_cosine(m4_runtime::Runtime &runtime){
 using namespace mw34::m4_fp_compound_native;
 require(runtime.domain()==m4_runtime::Domain::admitted_game&&runtime.remill_seeded(),"Compound cosine requires admitted persistent Runtime State");
 auto &state=*std::launder(reinterpret_cast<State *>(runtime.remill_state().data()));
 require(runtime.cpu().eip==0x4b64f0&&state.addr.ds_base.dword==0&&state.addr.ss_base.dword==0&&state.addr.fs_base.dword==runtime.fs_base().value,"Compound cosine source entry/segment domain rejected");
 frame=runtime.cpu().esp;sentinel=runtime.memory().load<unsigned>({frame});
 m4_mixed::overlay_cpu(state,runtime.cpu());validate_fp(runtime,state);
 const unsigned cw=state.x87.fxsave.cwd.flat,top=state.x87.fxsave.swd.flat>>11&7;
 require((cw==0x7f&&top==0)||(cw==0x37f&&top==7)||(cw==0xf7f&&top==0)||(cw==0x47f&&top==7)||(cw==0xa7f&&top==0)||(cw==0xe7f&&top==7),"Compound cosine finite original CW/TOP domain rejected");
 snapshot(runtime,state,true);Root root{0x4b64f0,0x5c93d0,0x5e8880};Context context(runtime.memory(),root);
 Result result{};result.cw=cw;
 {FpuScope isolation(static_cast<std::uint16_t>(cw));context.enter(state);
  require(!context.failed&&context.complete&&isolation.restored(result),"Compound cosine literal context/host restoration failed");
  m4_mixed::host(result.host_before.data(),result.host_after.data(),result.host_env_before.data(),result.host_env_after.data());}
 snapshot(runtime,state,false);auto &record=*observation;
 events(context.events,context.event_count);record.reads=context.reads;record.writes=context.writes;
 record.clears=context.clears;record.tests=context.tests;record.returns=context.returns;record.primitives=context.primitives;
 record.state_seeded=runtime.remill_seeded();
 const auto cpu=m4_mixed::cpu(state);runtime.cpu()={cpu.gpr[0],cpu.gpr[1],cpu.gpr[2],cpu.gpr[3],cpu.gpr[4],cpu.gpr[5],cpu.gpr[6],cpu.gpr[7],cpu.flags,cpu.pc};
 sync_fx(runtime,state);
}
}
'''
    code = '#include <memory>\n#include <algorithm>\n' + code + wrapper
    candidate = json.loads(pin(AREA / 'host-candidate-r1/report.json',
        '52fbe84a286e333d7c095be292088b922138eaabb661cf41d364bfab7c0ffb9e').read_bytes())
    ir_path = pin(candidate['host_IR'], candidate['host_IR_sha256'])
    ir = ir_path.read_text()
    bridges = [pin(base / 'raw80.cpp').read_text(), pin(base / 'store_test.cpp').read_text()]
    symbols = set(re.findall(r'\b(?:__remill_\w+|mw34_(?:actual_\w+|fp_store_exception_test|cosine_primitive_admit))\b',
                            code + ir + '\n'.join(bridges)))
    mapping = {symbol:'mw34_compound_' + symbol for symbol in symbols}

    def rename(text):
        for before, after in sorted(mapping.items(), key=lambda pair:-len(pair[0])):
            text = re.sub(r'\b' + re.escape(before) + r'\b', after, text)
        return text

    generated = rename(ir)
    recovered = generated
    for before, after in mapping.items():
        recovered = re.sub(r'\b' + re.escape(after) + r'\b', before, recovered)
    assert recovered == ir
    (out / 'compound.cpp').write_text(rename(code))
    (out / 'compound.ll').write_text(generated)
    for index, bridge in enumerate(bridges):
        (out / f'compound-bridge-{index}.cpp').write_text(rename(bridge))
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    commands, objects = [], {}
    for level in ('O0', 'O2'):
        selected = out / ('compound.ll' if level == 'O0' else 'compound-O2.ll')
        if level == 'O2':
            args = [pin(llvm / 'opt.exe'), '-passes=default<O2>,verify', '-S', out / 'compound.ll', '-o', selected]
            run = subprocess.run(list(map(str, args)), capture_output=True, timeout=60)
            (out / 'optimize.log').write_bytes(run.stdout + run.stderr)
            assert run.returncode == 0
            commands.append(dict(arguments=list(map(str, args)), exit_code=run.returncode))
        obj = out / f'compound-{level}.obj'
        args = [pin(llvm / 'llc.exe'), '-filetype=obj', '-' + level, selected, '-o', obj]
        run = subprocess.run(list(map(str, args)), capture_output=True, timeout=60)
        (out / f'compile-{level}.log').write_bytes(run.stdout + run.stderr)
        assert run.returncode == 0
        commands.append(dict(arguments=list(map(str, args)), exit_code=run.returncode))
        objects[level] = dict(path=str(obj), sha256=sha(obj))
    pin(__file__)
    for path in out.iterdir():
        pin(path)
    report = dict(passed=True, scope='Compound Runtime callback preparation; no Runtime execution credit',
                  root=0x4b64f0, slot=0x5e0160, CPP=str(out / 'compound.cpp'),
                  bridges=[str(out / f'compound-bridge-{i}.cpp') for i in range(2)],
                  objects=objects, names=mapping, bridge_namespace_change_reversible=True,
                  domain=dict(default_F64_inputs=inputs, CW_TOP_cases=[(0x7f,0),(0x37f,7),(0xf7f,0),(0x47f,7),(0xa7f,0),(0xe7f,7)],
                              required_output_RW_page=0x5e8000),
                  State_bytes=3504, CPU_bytes=40, FX_bytes=512, Native_bytes=159716,
                  fixed_protocol_pages=17, source_memory_pages=43, commands=commands,
                  Runtime_executed=False, source_after_seed=False, initializer_credit=0, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), objects=objects)))


if __name__ == '__main__':
    main(sys.argv[1])
