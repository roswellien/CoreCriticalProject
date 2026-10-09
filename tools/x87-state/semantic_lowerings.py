"""Exact static IR lowering for the four reviewed raw80 stack profiles.

The internal helpers operate on actual guest State and actual loaded bytes.
There is no request access, expected-result calculation or execution fallback.
"""
import hashlib
from pathlib import Path
import re

DESIGN_SHA256 = '77fbd3b2f13fa25f0401c48c39551a776f771670666b8a43964bb4868b71804e'
HELPERS_PATH = Path(__file__).with_name('semantic_helpers.ll')
POLICY = 'raw80_physical_tags_masked_stack_faults_sticky_de'
COMMON = 'mw34_x87_fault_flags'
NAMES = {kind:'mw34_x87_'+kind+'_prepare' for kind in ('push','pop','exchange','free')}
SITES = {
    'push': ('  %20 = load i64, ptr %1, align 8\n', 'before_loaded_raw80_unpack'),
    'pop': ('  %19 = load x86_fp80, ptr %ST0, align 1\n', 'before_actual_ST0_load'),
    'exchange': ('  call void @llvm.lifetime.start.p0(i64 10, ptr nonnull %1)\n', 'before_actual_exchange_moves'),
    'free': ('  store ptr %5, ptr %MEMORY, align 4\n', 'after_opcode_pointer_before_return'),
}
DE_SITE = '  store i8 %27, ptr %28, align 1\n'
DE_REPAIR = ('  %mw34_old_de = load i8, ptr %28, align 1\n'
             '  %mw34_sticky_de = or i8 %mw34_old_de, %27\n'
             '  store i8 %mw34_sticky_de, ptr %28, align 1\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def definitions(source):
    found = {}
    for match in re.finditer(r'^define internal void @(mw34_x87_\w+)\([^\n]+\) [^\n]*\{\n(.*?)^\}', source, re.M|re.S):
        require(match[1] not in found, 'Duplicate internal stack helper')
        found[match[1]] = match.group(0)
    return found


def normalized_body(definition):
    body = definition[definition.index('{')+1:definition.rindex('}')]
    # LLVM prints APInt constants signed, preserving the exact same 80 bits.
    body = re.sub(r'\bi80 (\d+)\b', lambda m:'i80 '+str(int(m[1])-(1<<80) if int(m[1]) >= 1<<79 else int(m[1])), body)
    return '\n'.join(' '.join(line.split()) for line in body.splitlines() if line.strip())


def helpers(kind):
    require(kind in NAMES, 'Unreviewed stack lowering profile')
    data = HELPERS_PATH.read_bytes()
    require(hashlib.sha256(data).hexdigest() == DESIGN_SHA256, 'Reviewed stack helper source changed')
    defs = definitions(data.decode())
    require(set(defs) == set(NAMES.values())|{COMMON}, 'Reviewed stack helper set differs')
    names = [NAMES[kind]] if kind == 'free' else [COMMON, NAMES[kind]]
    return {name:defs[name] for name in names}


def descriptor(kind, printed=None):
    defs = helpers(kind)
    hashes = {name:hashlib.sha256(normalized_body(body).encode()).hexdigest() for name,body in defs.items()}
    if printed is not None:
        actual = definitions(printed)
        require(set(actual) == set(defs), 'Generated stack helper set differs')
        require({name:hashlib.sha256(normalized_body(body).encode()).hexdigest() for name,body in actual.items()} == hashes,
                'Generated stack helper body differs')
        entry = re.search(r'^define .* @sub_10000000\([^\n]+\).*?\{\n(.*?)^\}', printed, re.M|re.S)
        require(entry is not None, 'Missing exact generated entry')
        call = 'call void @'+NAMES[kind]+'(ptr %state'+(', ptr %1' if kind=='push' else '')+')'
        require(entry[1].count(call) == 1, 'Generated stack helper call count differs')
        require(entry[1].count('call void @mw34_x87_') == 1, 'Unexpected generated stack helper call')
        require(('  '+call+'\n'+SITES[kind][0]) in entry[1], 'Generated stack helper insertion order differs')
        if kind == 'pop':
            require(entry[1].count('  %mw34_old_de = load i8, ptr %28, align 1') == 1 and
                    entry[1].count('  %mw34_sticky_de = or i8 %mw34_old_de, %27') == 1 and
                    entry[1].count('  store i8 %mw34_sticky_de, ptr %28, align 1') == 1,
                    'Generated pop sticky-DE lowering differs')
    return {'schema_version':1, 'policy':POLICY, 'design_sha256':DESIGN_SHA256,
            'helper_body_sha256':hashes, 'entry_helper_calls':{NAMES[kind]:1},
            'insertion_sites':{SITES[kind][1]:1}, 'sticky_DE_sites':int(kind=='pop')}


def lower(source, kind):
    defs = helpers(kind)
    require('@mw34_x87_' not in source, 'Input already contains stack semantic helper')
    site = SITES[kind][0]
    require(source.count(site) == 1, 'Stack semantic insertion site differs')
    call = '  call void @'+NAMES[kind]+'(ptr %state'+(', ptr %1' if kind=='push' else '')+')\n'
    result = source.replace(site,call+site,1)
    if kind == 'pop':
        require(result.count(DE_SITE) == 1, 'Pop sticky-DE insertion site differs')
        result = result.replace(DE_SITE,DE_REPAIR,1)
    result += '\n'+'\n\n'.join(defs.values())+'\n'
    descriptor(kind,result)
    return result
