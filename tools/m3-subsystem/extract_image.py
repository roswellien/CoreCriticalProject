"""Recover both complete private game functions and all consumer CFG edges."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage, read_binary

IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PROFILES = {
    'setter': {'entry': 0x558290, 'end': 0x5582bb, 'bytes': 43, 'instructions': 11,
               'offset': 0x157690, 'sha256': 'fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa'},
    'consumer': {'entry': 0x55a560, 'end': 0x55a5d7, 'bytes': 119, 'instructions': 46,
                 'offset': 1415520, 'sha256': '072fed4d6b5efe0ff7c3bfa1733c848a11f3ba5402fd05d18c2f1ebf8ff57adf'},
}
EDGES = {0x55a573: [0x55a582, 0x55a575], 0x55a580: [0x55a584],
         0x55a595: [0x55a5cf, 0x55a597], 0x55a59d: [0x55a5b4, 0x55a59f],
         0x55a5b2: [0x55a5a5, 0x55a5b4], 0x55a5cd: [0x55a59b, 0x55a5cf]}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def instruction_graph(instructions, profile):
    """Static actual-disassembly CFG; fail closed outside the reviewed edges."""
    by_pc = {row['pc']: row for row in instructions}
    edges = {}
    for row in instructions:
        pc, mnemonic = row['pc'], row['mnemonic']
        following = pc + row['size']
        if mnemonic.startswith('j'):
            match = re.fullmatch(r'0x([0-9a-f]+)(?: <\.text\+0x[0-9a-f]+>)?', row['operands'])
            require(match is not None, 'Unreviewed indirect/out-of-image branch')
            target = int(match[1], 16)
            require(target in by_pc, 'Branch target is not an admitted instruction boundary')
            require(mnemonic in ('jmp', 'jne', 'jle'), 'Unreviewed branch family')
            edges[pc] = [target] if mnemonic == 'jmp' else [target, following]
        elif mnemonic == 'ret':
            require(pc == profile['end'] - row['size'], 'Unexpected early/shared return')
        else:
            require(mnemonic not in ('call', 'syscall', 'sysenter', 'int'), 'Unresolved outgoing dependency')
    expected = {} if profile['entry'] == 0x558290 else EDGES
    require(edges == expected, 'Complete reviewed branch-site/target set changed')
    leaders = {profile['entry']}
    for destinations in edges.values():
        leaders.update(destinations)
    blocks = []
    ordered = sorted(leaders)
    for i, start in enumerate(ordered):
        end = ordered[i+1] if i+1 < len(ordered) else profile['end']
        rows = [row for row in instructions if start <= row['pc'] < end]
        require(rows and rows[-1]['pc'] + rows[-1]['size'] == end, 'Incomplete recovered block')
        tail = rows[-1]
        successors = edges.get(tail['pc'], [] if tail['mnemonic'] == 'ret' else [end])
        blocks.append({'start_va': start, 'end_va': end, 'instructions': len(rows), 'successors': successors})
    require(len(blocks) == (1 if not expected else 10), 'Complete CFG block count differs')
    reachable, pending = set(), [profile['entry']]
    graph = {row['start_va']: row['successors'] for row in blocks}
    while pending:
        pc = pending.pop()
        if pc not in reachable:
            require(pc in graph, 'CFG edge lacks a complete block')
            reachable.add(pc)
            pending.extend(graph[pc])
    require(reachable == set(graph), 'Unreachable/unrecovered instruction block')
    return blocks, edges


def extract(image_path, output, objdump):
    output = output.resolve()
    require(output.is_relative_to((ROOT / 'reports/m3-subsystem').resolve()), 'Private output must remain under ignored subsystem reports')
    require(not (output / 'extraction.json').exists(), 'Refusing to replace earlier extraction identity')
    raw = read_binary(image_path)
    require(hashlib.sha256(raw).hexdigest() == IMAGE_SHA, 'Wrong admitted MW3 image SHA256')
    image = PEImage(raw)
    require(image.image_base == 0x400000 and image.size_of_image == 0x5f5000, 'Private image mapping changed')
    result = {'schema_version': 1, 'image_path': str(image_path.resolve()), 'image_sha256': IMAGE_SHA,
              'image_bytes': len(raw), 'image_base': image.image_base, 'image_size': image.size_of_image,
              'functions': {}, 'global_page': {'base': 0x72c000, 'size': 4096, 'initial': 'PE virtual zero-fill', 'permissions': 'rw'},
              'source_tools': {str(Path(__file__).resolve()): sha(__file__),
                               str(ROOT / 'tools/analysis/pe.py'): sha(ROOT / 'tools/analysis/pe.py'),
                               str(objdump.resolve()): sha(objdump)},
              'scope': 'Actual complete entries and shared data only; offline operation sequence, no gameplay call-chain claim'}
    global_section = next((s for s in image.sections if s['virtual_address'] <= 0x32c000 < s['virtual_address'] + s['virtual_size']), None)
    require(global_section and global_section['name'] == '.data' and global_section['readable'] and global_section['writable'] and
            0x32c000 >= global_section['virtual_address'] + global_section['raw_size'] and
            0x32d000 <= global_section['virtual_address'] + global_section['virtual_size'], 'Global page lacks complete writable zero-fill admission')
    output.mkdir(parents=True, exist_ok=True)
    for kind, profile in PROFILES.items():
        offset, _ = image.rva_range(profile['entry'] - image.image_base, profile['bytes'])
        section = next((s for s in image.sections if s['virtual_address'] <= profile['entry'] - image.image_base and
                        profile['end'] - image.image_base <= s['virtual_address'] + s['virtual_size']), None)
        require(offset == profile['offset'] and section and section['readable'] and section['executable'] and not section['writable'], 'Complete code RX mapping changed')
        body = raw[offset:offset + profile['bytes']]
        require(hashlib.sha256(body).hexdigest() == profile['sha256'], 'Complete function identity differs: ' + kind)
        run = subprocess.run([str(objdump), '--disassemble', '--x86-asm-syntax=intel',
                              '--start-address=' + str(profile['entry']), '--stop-address=' + str(profile['end']),
                              str(image_path)], capture_output=True, text=True, check=True, timeout=30)
        rows = []
        for line in run.stdout.splitlines():
            match = re.fullmatch(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(\S+)(?:\s+(.*))?', line)
            if match:
                code = bytes.fromhex(match[2])
                rows.append({'pc': int(match[1], 16), 'size': len(code), 'mnemonic': match[3],
                             'operands': match[4] or '', 'instruction_sha256': hashlib.sha256(code).hexdigest()})
        require(len(rows) == profile['instructions'], 'Instruction count differs: ' + kind)
        pc = profile['entry']
        for row in rows:
            require(row['pc'] == pc, 'Complete instruction extent has a gap/overlap')
            pc += row['size']
        require(pc == profile['end'], 'Complete instruction extent differs')
        blocks, edges = instruction_graph(rows, profile)
        code_path, disassembly = output / (kind + '.bin'), output / (kind + '-private-disassembly.txt')
        code_path.write_bytes(body)
        disassembly.write_text(run.stdout)
        result['functions'][kind] = {**profile, 'code_path': str(code_path), 'section': section,
                                    'instruction_records': rows, 'blocks': blocks, 'branch_edges': edges,
                                    'outgoing_targets': [], 'all_instructions_reachable': True,
                                    'disassembly_path': str(disassembly), 'disassembly_sha256': sha(disassembly)}
    page = output / 'global-page-initial.bin'
    page.write_bytes(bytes(4096))
    result['global_page'].update({'section': global_section, 'initial_path': str(page), 'initial_sha256': sha(page)})
    record = output / 'extraction.json'
    record.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'extraction_sha256': sha(record), 'functions': {kind: value['sha256'] for kind, value in PROFILES.items()}}))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'output', 'objdump'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    extract(args.image, args.output, args.objdump)
