"""Resolve reused body byte patterns using current typed bridge relocations."""
from pathlib import Path
BASE=Path(__file__).with_name('review_mfc1168_connected_native_prefix.py')
text=BASE.read_text()
anchor="   for j in lift['source_bodies'].values():"
assert text.count(anchor)==1
replacement=r'''   component_object=pin(bf/'CMakeFiles/mw34_mfc1168_connected.dir/connected_component.cpp.obj')
   symbols_c,sections_c=C.parse(component_object.read_bytes());bridge_targets={}
   for symbol in ('mw34_mfc1168_read8','mw34_mfc1168_read16','mw34_mfc1168_read32','mw34_mfc1168_read64','mw34_mfc1168_write8','mw34_mfc1168_write16','mw34_mfc1168_write32','mw34_mfc1168_write64','mw34_mfc1168_call','mw34_mfc1168_jump','mw34_mfc1168_missing','mw34_mfc1168_return'):
    raw_c,relocs_c=C.function(symbols_c,sections_c,symbol);matches_c=C.linked_candidates(image,raw_c,relocs_c);assert len(matches_c)==1,symbol
    bridge_targets[symbol]=matches_c[0][0];counts['whole_current_typed_bridge_functions']+=1
   def current_body_matches(raw,relocs):
    matches=C.linked_candidates(image,raw,relocs)
    attributed=[(a,b)for a,b in matches if all(a+r['offset']+4+struct.unpack_from('<i',b,r['offset'])[0]==bridge_targets[r['symbol']['name']] for r in relocs if r['symbol']['name']in bridge_targets)]
    assert any(r['symbol']['name']in bridge_targets for r in relocs),'Current body has a source bridge relocation'
    counts['whole_typed_bridge_relocation_targets']+=sum(r['symbol']['name']in bridge_targets for r in relocs)
    return attributed
   for j in lift['source_bodies'].values():'''
text=text.replace(anchor,replacement)
old="matches=C.linked_candidates(image,raw,relocs);assert len(matches)==1,j['symbol']"
assert text.count(old)==1
text=text.replace(old,"matches=current_body_matches(raw,relocs);assert len(matches)==1,j['symbol']")
old='  pin(R/\'tools/m4-mfc1168-native/run_connected_fixture.py\');pin(__file__);pin(sys.executable)'
assert text.count(old)==1
text=text.replace(old,"  pin(BASE);"+old.strip())
exec(compile(text,str(BASE),'exec'),globals())
