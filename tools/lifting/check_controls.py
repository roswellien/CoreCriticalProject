"""Opt-in rejection tests for original/lifted workers and LLVM host adapter."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile

from compare_fixture import HEADER, REQUEST, corpus
from host_adapter import adapt
from fixture_catalog import FIXTURES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--lifted', type=Path, action='append', default=[])
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--fixture-name', choices=FIXTURES, default='add')
    parser.add_argument('--llvm-dll', type=Path, required=True)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--bad-target-guest', type=Path)
    args = parser.parse_args()
    controls = []
    case = corpus(0x3434, 0, args.fixture_name)[0]
    valid = HEADER.pack(b'MW34REQ1', 1, 1, REQUEST.size, 32) + REQUEST.pack(*case)
    changed_entry, changed_flags, changed_stack = list(case), list(case), list(case)
    changed_entry[9] += 1
    changed_flags[8] |= 0x100  # Trap flag is unsafe in the capture trampoline.
    changed_stack[4] = 0
    mutations = {
        'truncated_header': b'MW34', 'truncated_request': valid[:-1],
        'trailing_input': valid + b'X',
        'bad_header': HEADER.pack(b'MW34REQ1', 2, 1, REQUEST.size, 32) + REQUEST.pack(*case),
        'bad_entry': valid[:HEADER.size] + REQUEST.pack(*changed_entry),
        'unsafe_flags': valid[:HEADER.size] + REQUEST.pack(*changed_flags),
        'unmapped_stack': valid[:HEADER.size] + REQUEST.pack(*changed_stack),
    }
    if args.fixture_name == 'memory':
        for name, pointer in (('unmapped_buffer', 0), ('crossing_buffer', 0x20002000 - 11),
                              ('wrapping_buffer', 0xfffffffc), ('return_frame_alias', case[4])):
            changed = list(case)
            changed[10] = pointer
            mutations[name] = valid[:HEADER.size] + REQUEST.pack(*changed)
    with tempfile.TemporaryDirectory(prefix='mw34-controls-') as directory:
        root = Path(directory)
        fixture = root / 'fixture.bin'
        workers = [('reference', args.reference)] + [
            (f'lifted-{index}', worker) for index, worker in enumerate(args.lifted)]
        for role, worker in workers:
            fixture.write_bytes(args.fixture.read_bytes())
            for name, data in mutations.items():
                input_file, output_file = root / 'input.bin', root / 'output.bin'
                input_file.write_bytes(data)
                result = subprocess.run([str(worker.resolve()), str(input_file),
                                         str(output_file), str(fixture)],
                                        capture_output=True, text=True, timeout=10)
                if result.returncode != 1 or not result.stderr.strip():
                    raise ValueError(f'{role}/{name}: expected an explicit worker rejection: {result}')
                controls.append({'role': role, 'name': name, 'outcome': 'rejected',
                                 'reason': result.stderr.strip()})
            fixture.write_bytes(args.fixture.read_bytes()[:-1] + b'\x90')
            result = subprocess.run([str(worker.resolve()), str(input_file),
                                     str(output_file), str(fixture)], capture_output=True, text=True, timeout=10)
            if result.returncode != 1 or 'fixture identity' not in result.stderr:
                raise ValueError(f'{role}: Changed fixture was not explicitly rejected')
            controls.append({'role': role, 'name': 'changed_fixture', 'outcome': 'rejected'})
            if role != 'reference':
                other = 'branch' if args.fixture_name != 'branch' else 'add'
                fixture.write_bytes(FIXTURES[other])
                result = subprocess.run([str(worker.resolve()), str(input_file), str(output_file),
                                         str(fixture)], capture_output=True, text=True, timeout=10)
                if result.returncode != 1 or 'compiled authored fixture identity' not in result.stderr:
                    raise ValueError(f'{role}: Wrong compiled fixture was accepted')
                controls.append({'role': role, 'name': 'wrong_compiled_fixture', 'outcome': 'rejected'})
                if args.fixture_name == 'memory':
                    result = subprocess.run([str(worker.resolve()), '--check-memory-bridges'],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode != 0 or '7 failure probes passed' not in result.stdout:
                        raise ValueError(f'{role}: Memory bridge probes failed: {result}')
                    controls.append({'role': role, 'name': 'memory_bridge_failures',
                                     'outcome': 'passed', 'failure_probes': 7, 'stdout': result.stdout.strip()})
        source = args.guest.read_text()
        ir_mutations = {
            'unknown_external': source.replace('__remill_read_memory_32', '__unapproved_read_memory_32'),
            'invalid_entry_width': source.replace('i32 %program_counter', 'i64 %program_counter'),
            'changed_state_layout': source.replace('[32 x %union.VectorReg]', '[31 x %union.VectorReg]'),
            'pointer_integer_cast': source.replace('  %SSBASE =', '  %bad = ptrtoint ptr %state to i64\n  %SSBASE ='),
        }
        if args.bad_target_guest:
            ir_mutations['unresolved_control_flow_target'] = args.bad_target_guest.read_text()
        for name, ir in ir_mutations.items():
            guest, host, record = root / 'guest.ll', root / 'host.ll', root / 'layout.json'
            guest.write_text(ir)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    adapt(args.llvm_dll, guest, host, record,
                          profile='shift' if args.fixture_name == 'shift' else 'fixture')
            except ValueError as error:
                if name == 'unresolved_control_flow_target' and '__remill_missing_block' not in str(error):
                    raise ValueError(f'Bad target rejected for an unexpected reason: {error}') from error
                controls.append({'role': 'llvm_adapter', 'name': name, 'outcome': 'rejected',
                                 'reason': str(error)})
            else:
                raise ValueError(f'Adapter accepted {name}')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({'version': 1, 'controls': controls,
                                      'x64_worker_controls': f'{len(args.lifted)} workers checked'}, indent=2) + '\n')
    print(f'{len(controls)} rejection/bridge checks passed')


if __name__ == '__main__':
    main()
