"""Independent bounded formatter source/flag/byteflow review.

This reads sealed compact trace exports, physical PE bytes and the producing
source tools. It does not replay captured AFTER as a model input or open a
capture archive. Generic printf and native execution remain separate gates.
"""
import collections
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C

BITS = dict(CF=0, PF=2, AF=4, ZF=6, SF=7, DF=10, OF=11)
ARITH = {'CF', 'PF', 'AF', 'ZF', 'SF', 'OF'}
CONSUMED = dict(je={'ZF'}, jne={'ZF'}, ja={'CF','ZF'}, jae={'CF'}, jb={'CF'},
                jbe={'CF','ZF'}, jg={'ZF','SF','OF'}, jge={'SF','OF'}, jl={'SF','OF'},
                jle={'ZF','SF','OF'}, js={'SF'}, jns={'SF'}, jo={'OF'}, jno={'OF'},
                adc={'CF'}, sbb={'CF'}, scasb={'DF'})
REGS = dict(eax=0, ecx=1, edx=2, ebx=3, esp=4, ebp=5, esi=6, edi=7)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, C.pin(path))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sealed(report, path):
    path = Path(path).resolve()
    matches = [h for p,h in report['files'].items() if Path(p).resolve() == path]
    C.need(len(matches) == 1, 'Complete exact bounded producing proof pin')
    return C.read(path, matches[0])


def aliases(name, cpu):
    if name in REGS:
        return cpu[REGS[name]], 32
    if name in ('ax','cx','dx','bx','sp','bp','si','di'):
        return cpu[REGS['e'+name]] & 65535, 16
    if name in ('al','cl','dl','bl','ah','ch','dh','bh'):
        value = cpu[REGS['e'+name[0]+'x']]
        return (value >> (8 if name[1] == 'h' else 0)) & 255, 8
    raise ValueError('Independent selected source register alias')


def flag_domain(row, domain, cpu):
    """Independently derive only architectural definedness, never bit values."""
    out = dict(domain)
    op = row['mnemonic']; args = row['decoded_operands']; pc = row['pc']
    def define(names):
        for name in names:
            out.pop(name, None)
    def undef(name):
        out[name] = (pc, op)
    if op in ('add','adc','sub','sbb','neg','cmp'):
        define(ARITH)
    elif op in ('inc','dec'):
        define(ARITH - {'CF'})
    elif op in ('and','or','xor','test'):
        define(ARITH - {'AF'}); undef('AF')
    elif op in ('shl','shr','sar'):
        count = 1 if len(args) == 1 else (args[1]['value'] if args[1]['kind'] == 'immediate'
                                         else aliases(args[1]['register'], cpu)[0]) & 31
        # The selected physical path contains only32-bit count1/count4.
        C.need(args[0]['bits'] == 32 and count in (1,4), 'Finite selected shift domain; no narrow/wide-count projection')
        define({'CF','PF','ZF','SF'}); undef('AF')
        if count == 1:
            define({'OF'})
        else:
            undef('OF')
    elif op == 'scasb':
        C.need(cpu is not None, 'Actual compact SCASB architecture retained')
        if not row.get('repeat') or cpu[1]:
            define(ARITH)
    elif op in ('cld','std'):
        define({'DF'})
    return out


def causes(domain):
    return {name:(row['PC'], row['mnemonic']) for name,row in domain.items()}


def projected(cpu, domain):
    value = list(cpu)
    value[8] &= ~sum(1 << BITS[name] for name in domain)
    return value


def selected_extended(row, join, counts):
    """Independent selected SAR and SCASB result/control arithmetic."""
    op = row['mnemonic']; before = join['CPU_before']; after = join['CPU_after']
    if op == 'sar':
        args = row['decoded_operands']; n = args[1]['value'] & 31
        C.need(args[0] == {'kind':'register','register':'eax','bits':32} and n == 4,
               'Only actual selected SAR EAX,4 extension used')
        value = before[0]; signed = value - (1<<32) if value & (1<<31) else value
        result = (signed >> n) & 0xffffffff
        C.need(after[0] == result and after[1:8] == before[1:8], 'Independent exact signed shift and preserved source registers')
        flags = dict(CF=(value >> (n-1)) & 1, PF=int((result & 255).bit_count()%2 == 0),
                     ZF=int(result == 0), SF=(result >> 31) & 1)
        C.need(all((after[8] >> BITS[name]) & 1 == value for name,value in flags.items()), 'Every architecturally defined selected SAR result flag')
        counts['independent_SAR4_results'] += 1
    elif op == 'scasb':
        repeat = row.get('repeat'); C.need(repeat in (None,'repne','repnz'), 'Finite selected byte scan repeat')
        if repeat and before[1] == 0:
            C.need(after[:9] == before[:9], 'Zero-count REP scan preserves architecture')
        else:
            cells = [cell for cell in join['operands'] if cell['read']]
            C.need(len(cells) == 1 and cells[0]['width'] == 1 and cells[0]['address'] == before[7],
                   'Actual flatES SCASB reads incomingEDI byte')
            byte = cells[0]['before']; al = before[0] & 255; result = (al-byte) & 255
            flags = dict(CF=int(al < byte), PF=int(result.bit_count()%2 == 0),
                         AF=int(bool((al ^ byte ^ result)&16)), ZF=int(result == 0),
                         SF=int(bool(result&128)), OF=int(bool((al^byte)&(al^result)&128)))
            C.need(all((after[8] >> BITS[name]) & 1 == value for name,value in flags.items()), 'Independent exact SCASB arithmetic flags')
            delta = -1 if (before[8] >> 10) & 1 else 1
            expected = list(before[:8]); expected[7] = (before[7]+delta) & 0xffffffff
            if repeat:
                expected[1] = before[1]-1
            C.need(after[:8] == expected, 'Independent SCASB ECX/EDI update and all carried registers')
            continuation = bool(repeat and expected[1] and not flags['ZF'])
            C.need(join['next_PC'] == (row['pc'] if continuation else row['pc']+row['width']), 'Literal REP stream control from source count/ZF')
        counts['independent_SCASB_results'] += 1


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh additive formatting source review')
    out.mkdir(parents=True)
    passed = False; counts = collections.Counter(); findings = []
    try:
        C.pin(__file__); C.pin(C.__file__)
        path = ROOT / 'reports/m4-formatting-source/original-trace-source-r4/report.json'
        report = C.read(path, 'b3d0ca6d60d0393479d3dd315e3795d8c02a3770f8f4bfe89de0ef6a5ae98dc9')
        C.need(report['passed'] and report['reader_closed'] and report['write_operand_before_from_literal_backing'] and
               report['undefined_flag_control_denied'] and report['source_post_state_seed'] is False and
               report['native_executed'] is False and report['generic_formatter_closed'] is False and
               report['registration_lifecycle_executed_by_model'] is False, 'Exact original-only finite producing source scope')
        for relative in ('tools/m4-formatting-source/provider_model.py','tools/m4-formatting-source/flag_domain.py',
                         'tools/m4-formatting-source/compare_trace_v4.py',
                         'tools/m4-crt-locale-batch-model-review/interpreter_v2.py'):
            sealed_path = (ROOT / relative).resolve()
            C.pin(sealed_path, report['files'][str(sealed_path)])
            counts['executed_source_tools_reviewed'] += 1
        source = sealed(report, path.with_name('source-derivations.json'))
        joins = sealed(report, path.with_name('instruction-joins.json'))
        APIs = sealed(report, path.with_name('finite-API-inputs.json'))
        rec_path = ROOT / 'reports/m4-formatting-source/provider-recovery-r2/report.json'
        recovery = sealed(report, rec_path)
        provider = C.read(recovery['instructions'], recovery['instructions_sha256'])
        program = {row['pc']:row for row in provider['instructions']}
        allocator = sealed(report, ROOT / 'reports/m4-onexit-review/interface-r1/instruction-contracts.json')
        game = sealed(report, ROOT / 'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json')
        for row in allocator['instructions'] + game['instructions']:
            C.need(row['pc'] not in program or program[row['pc']] == row, 'Exact overlapping retained source rows')
            program[row['pc']] = row
        PE = load(ROOT / 'tools/analysis/pe.py', 'formatting_independent_PE')
        dll = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
        C.pin(dll, recovery['files'][str(dll)])
        image = PE.PEImage(dll.read_bytes())
        for row in provider['instructions']:
            offset, backing_end = image.rva_range(row['pc'] - image.image_base, row['width'])
            C.need(offset + row['width'] <= backing_end and image.data[offset:offset+row['width']].hex() == row['bytes_hex'], 'Each independent physical provider instruction span')
            counts['physical_provider_instruction_spans'] += 1
        tables = sealed(recovery, rec_path.with_name('tables.json'))
        for table in tables:
            offset,backing_end = image.rva_range(table['address']-image.image_base, table['bytes'])
            C.need(offset+table['bytes'] <= backing_end and image.data[offset:offset+table['bytes']].hex() == table['bytes_hex'], 'Whole exact static source control/classification table')
            counts['physical_whole_table_bytes'] += table['bytes']
        trace_gate_path = ROOT / 'reports/m4-formatting-original/trace-validation-r1/report.json'
        trace_gate = sealed(report, trace_gate_path)
        phases = sealed(trace_gate, trace_gate_path.with_name('actual-trace-phases.json'))
        for phase in phases:
            raw = bytes.fromhex(phase['raw_segments_hex'])
            C.need(len(raw) == 60, 'Every actual stopped-thread flat descriptor side')
            for offset in range(0,60,20):
                selector,base,limit,descriptor = struct.unpack_from('<III8s',raw,offset)
                C.need(selector == 0x2b and base == 0 and limit == 0xffffffff and len(descriptor)==8,
                       'Actual DS/ES/SS flat source addressing evidence')
                counts['actual_flat_segment_descriptors'] += 1
        C.need(len(source)==3 and len(joins)==2274 and len(APIs)==3, 'Exactly three complete genuine formatting prefixes')
        reached = set()
        for phase, result in enumerate(source):
            domain = {}; observed = [row for row in joins if row['phase']==phase]; index = 0
            string_index = 0
            C.need(result['phase']==phase and result['no_post_source_seed'] and
                   result['owner']['source_final_hex']==result['owner']['final_hex'], 'Same bounded source branch and complete capacity result')
            for pc in result['source_PCs']:
                row = program[pc]; current = observed[index] if pc in {r['pc'] for r in provider['instructions']} else None
                cpu = current['CPU_before'] if current else None
                if row['mnemonic'] == 'scasb':
                    iteration = result['string_iterations'][string_index]
                    C.need(iteration['PC'] == pc and iteration['ECX_before'] != 0, 'Exact ordered nonzero modeled scan input')
                    if current:
                        C.need(cpu[1] == iteration['ECX_before'], 'Actual traced scan count joins full modeled scan ledger')
                    else:
                        cpu = [None,iteration['ECX_before']]
                        counts['untraced_game_scan_definedness_joins'] += 1
                    string_index += 1
                C.need(not set(domain) & CONSUMED.get(row['mnemonic'],set()), 'No modeled control/string/carry consumes undefined architectural bits')
                counts['all_source_defined_flag_uses'] += int(bool(CONSUMED.get(row['mnemonic'])))
                following = flag_domain(row, domain, cpu)
                if current:
                    C.need(current['index']==index and current['PC']==pc and causes(current['undefined_flags_before'])==domain and
                           causes(current['undefined_flags_after'])==following, 'Independent complete flag cause/lifetime across every actual provider instruction')
                    C.need(projected(current['CPU_before'],domain)==projected(current['actual_CPU_before'],domain) and
                           projected(current['CPU_after'],following)==projected(current['actual_CPU_after'],following), 'All source-defined whole CPU values independent exact mask')
                    for cell in current['operands']:
                        expected = collections.Counter((cell['before'] if direction==0 else cell['after'],direction)
                                                       for direction,enabled in ((0,cell['read']),(1,cell['write'])) if enabled)
                        actual = collections.Counter((r[2],r[4]) for r in cell['source_rows'])
                        C.need(expected==actual and all(r[0]==pc and r[1]==cell['address'] and r[3]==cell['width'] for r in cell['source_rows']), 'Every exact source operand value/direction/width')
                        if cell['write']:
                            C.need(cell['source_before_value']==cell['before'], 'Literal-derived entire write preimage matches actual before bytes')
                            counts['literal_write_before_joins'] += 1
                        counts['exact_actual_source_operand_joins'] += 1
                    selected_extended(row,current,counts)
                    counts['whole_source_defined_CPU_sides'] += 2
                    counts['exact_flag_domain_instruction_joins'] += 1
                    reached.add(pc); index += 1
                domain = following
                if pc == 0x7800137f:
                    C.need(len(result['API_inputs'])==1 and result['API_inputs'][0]['source_CALL']==pc and
                           result['API_inputs'][0]['AFTER_machine_seed'] is False,
                           'Only measured true HeapAlloc supplies finite pointer/volatile/initial backing inputs')
                    domain = {}
            C.need(index==len(observed) and [d['index'] for d in result['dispatches']]==[1,7,1,7], 'Every provider observation exhausted and exact four narrow branches')
            C.need(string_index == len(result['string_iterations']), 'Entire modeled game/provider scan inventory exhausted')
            owner = result['owner']; C.need(owner['request']==(8,10,12)[phase] and owner['capacity']==16 and
                                           owner['actual_HeapAlloc_request']==16,
                                           'Actual source requested sizes versus measured allocator rounding/capacity')
            C.need(owner['final_hex'][2*owner['request']:] == owner['initial_hex'][2*owner['request']:], 'Entire private capacity tail carried unchanged')
            counts['whole_owned_capacity_byteflows'] += 1
        counts['unique_reached_provider_PCs'] = len(reached)
        C.need(counts['exact_flag_domain_instruction_joins']==2274 and counts['whole_source_defined_CPU_sides']==4548 and
               counts['exact_actual_source_operand_joins']==1221 and counts['literal_write_before_joins']==540 and
               counts['all_source_defined_flag_uses']==429 and len(reached)==238,
               'Complete independent bounded source/control/byteflow extent')
        implicit_sar = [row['pc'] for row in provider['instructions'] if row['mnemonic']=='sar' and len(row['decoded_operands'])==1]
        C.need(not set(implicit_sar)&reached, 'Dormant implicit-count SAR rows excluded from measured normal path')
        findings.append(dict(scope='Only measured238-PC normal paths reviewed; provider_model implicit-count SAR remains unsupported outside selected domain',
                             dormant_implicit_SAR_PCs=implicit_sar, generic_formatter_credit=False))
        passed = True
    finally:
        evidence = out / 'findings.json'; evidence.write_text(json.dumps(findings,indent=2)+'\n'); C.pin(evidence)
        target = out / 'report.json'
        target.write_text(json.dumps(dict(passed=passed,counts=dict(counts),capture_archives_opened=0,
                                        scope='Independent compact genuine instruction/source exports, physical provider bytes, selected SAR/SCASB arithmetic, flag provenance/lifetime and write-before byteflows',
                                        native_executed=False,generic_formatter_closed=False,initializer_credit=0,
                                        source_AFTER_seed=False,files=C.PINS),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))


if __name__=='__main__':
    main(sys.argv[1])
