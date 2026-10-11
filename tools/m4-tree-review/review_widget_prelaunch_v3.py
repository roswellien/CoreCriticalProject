"""Exact physical new instruction overlays on inherited CC-only sparse bytes."""
from pathlib import Path
import hashlib
V2 = Path(__file__).with_name('review_widget_prelaunch_v2.py')
V2_SHA = '875632f69885f756e3421f72f6ebc5ed30fe843537eff3d37fc418de88ab4637'
if hashlib.sha256(V2.read_bytes()).hexdigest() != V2_SHA:
    raise ValueError('Immutable page-crossing reviewer')
program = V2.read_text()
anchor = "exec(compile(source, str(BASE), 'exec'), globals())"
if program.count(anchor) != 1:
    raise ValueError('One immutable checker invocation')
transform = r'''
old_parent = """        for address, value in parent_pages.items():
            eq(sparse_pages[address], value, 'All inherited genuine sparse inputs preserved')"""
new_parent = """        pin(V2, V2_SHA)
        declared = {}
        for row in rows:
            for index, value in enumerate(bytes.fromhex(row['bytes_hex'])):
                at = row['pc'] + index
                need(at not in declared or declared[at] == value, 'Shared physical source bytes agree')
                declared[at] = value
        overlays = []
        for address, (rights, old_bytes) in parent_pages.items():
            current_rights, current_bytes = sparse_pages[address]
            eq(current_rights, rights, 'Whole inherited sparse page right unchanged')
            for index, (before, after) in enumerate(zip(old_bytes, current_bytes)):
                if before != after:
                    at = address + index
                    need(rights == 1 and before == 0xcc and at in declared and declared[at] == after, 'Only exact new physical instructions replace inherited RX CC padding')
                    overlays.append(dict(address=at,before=before,after=after))
            counts['complete_inherited_page_relations'] += 1
        eq(len(overlays),1363,'Complete measured inherited instruction-padding overlay domain')
        eq(sorted(set(row['address'] & ~4095 for row in overlays)), [0x40e000,0x40f000,0x517000,0x51a000,0x59f000,0x5ac000], 'Exact six inherited RX source-extension pages')
        counts['source_proven_inherited_RX_padding_overlay_bytes'] = len(overlays)
        (out / 'inherited-padding-source-relations.json').write_text(json.dumps(overlays,indent=2)+'\\n')
        pin(out / 'inherited-padding-source-relations.json')"""
if source.count(old_parent) != 1:
    raise ValueError('One complete inherited page relation')
source = source.replace(old_parent, new_parent, 1)
exec(compile(source, str(BASE), 'exec'), globals())
'''
program = program.replace(anchor, transform, 1)
exec(compile(program, str(V2), 'exec'), globals())
