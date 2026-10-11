"""Exact instruction-local CW/wait replacements, with retained source proof."""
import re

SSA = r'%[A-Za-z0-9_.$]+'


def repair(text, graph):
    original = text
    records = []
    patterns = (
        ('wait', r'  ('+SSA+r') = call i32 @__remill_fpu_exception_test\(i32 noundef 127\) #\d+\n'
         r'  call void @__remill_fpu_exception_clear\(i32 noundef \1\) #\d+\n'
         r'  store ptr ('+SSA+r'), ptr %MEMORY, align 4',
         lambda m,k: f'  %hypot.wait.{k} = call ptr @mw34_hypot_wait(ptr %state, ptr {m[2]})\n'
                     f'  store ptr %hypot.wait.{k}, ptr %MEMORY, align 4'),
        ('fnstcw', r'  ('+SSA+r') = getelementptr inbounds nuw i8, ptr %state, i32 2768\n'
         r'  ('+SSA+r') = load i16, ptr \1, align 16\n'
         r'  ('+SSA+r') = call noundef ptr @__remill_write_memory_16\(ptr noundef ('+SSA+r'), '
         r'i32 noundef ('+SSA+r'), i16 noundef zeroext \2\) #\d+',
         lambda m,k: f'  {m[3]} = call ptr @mw34_hypot_store_cw(ptr %state, i32 {m[5]}, ptr {m[4]})'),
        ('fldcw', r'  ('+SSA+r') = getelementptr inbounds nuw i8, ptr %state, i32 2768\n'
         r'  ('+SSA+r') = call noundef zeroext i16 @__remill_read_memory_16\(ptr noundef ('+SSA+r'), '
         r'i32 noundef ('+SSA+r')\) #\d+\n'
         r'  store i16 \2, ptr \1, align 16\n'
         r'  ('+SSA+r') = lshr i16 \2, 10\n'
         r'  ('+SSA+r') = and i16 \5, 3\n'
         r'  ('+SSA+r') = zext nneg i16 \6 to i32\n'
         r'  call void @__remill_fpu_set_rounding\(i32 noundef \7\) #\d+\n'
         r'  store ptr \3, ptr %MEMORY, align 4',
         lambda m,k: f'  %hypot.load.cw.{k} = call ptr @mw34_hypot_load_cw(ptr %state, i32 {m[4]}, ptr {m[3]})\n'
                     f'  store ptr %hypot.load.cw.{k}, ptr %MEMORY, align 4'),
    )
    for instruction,pattern,lower in patterns:
        rows = [r for r in graph['instructions'] if r['pc'] >= graph['entry'] and
                r['mnemonic'] in ((instruction,'fwait') if instruction=='wait' else (instruction,))]
        matches = list(re.finditer(pattern,text))
        if len(matches) != len(rows):
            raise ValueError(f'Exact physical {instruction} instruction/IR count: {len(rows)} != {len(matches)}')
        if len(rows)>1:
            raise ValueError('Multiple CW instructions require explicit per-block PC proof')
        if matches:
            index = 0
            def replace(match):
                nonlocal index
                row = rows[index]
                replacement = lower(match,index)
                records.append(dict(instruction=instruction,physical_PC=row['pc'],
                    physical_bytes=row['bytes'],old_IR=match[0],new_IR=replacement,
                    guest_control_word_is_authority=True,
                    hardware_or_runtime_execution_verified=False))
                index += 1
                return replacement
            text = re.sub(pattern,replace,text)
            declaration = ('declare ptr @mw34_hypot_wait(ptr, ptr)' if instruction=='wait' else
                           'declare ptr @mw34_hypot_'+('store' if instruction=='fnstcw' else 'load')+'_cw(ptr, i32, ptr)')
            text += '\n'+declaration+'\n'
    text = re.sub(r'^declare[^\n]*@__remill_fpu_set_rounding\([^\n]+\n','',text,flags=re.M)
    if '@__remill_fpu_set_rounding' in text:
        raise ValueError('Unrepaired host rounding helper')
    restored = text
    for record in reversed(records):
        if restored.count(record['new_IR']) != 1:
            raise ValueError('Each replacement is an exact unique instruction seam')
        restored = restored.replace(record['new_IR'],record['old_IR'])
    # The exact source baseline is pinned independently; LLVM declarations are
    # the only non-instruction changes besides the retained replacements above.
    strip = lambda s: '\n'.join(x for x in s.splitlines() if x and not
        (x.startswith('declare') and ('@mw34_hypot_' in x or '@__remill_fpu_set_rounding' in x)))
    if strip(restored) != strip(original):
        raise ValueError('Instruction replacement must reverse to the whole baseline')
    return text, records
