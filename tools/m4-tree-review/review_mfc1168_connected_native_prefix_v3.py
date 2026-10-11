"""Attribute the missing-block alias through its actual jump relocation."""
from pathlib import Path
PREVIOUS=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v2.py')
generator=PREVIOUS.read_text()
old="raw_c,relocs_c=C.function(symbols_c,sections_c,symbol);matches_c=C.linked_candidates(image,raw_c,relocs_c);assert len(matches_c)==1,symbol"
new="raw_c,relocs_c=C.function(symbols_c,sections_c,symbol);matches_c=C.linked_candidates(image,raw_c,relocs_c)\n    if len(matches_c)!=1:\n     direct=[r for r in relocs_c if r['symbol']['name']in bridge_targets];assert direct,symbol\n     matches_c=[(a,b)for a,b in matches_c if all(a+r['offset']+4+struct.unpack_from('<i',b,r['offset'])[0]==bridge_targets[r['symbol']['name']]for r in direct)]\n    assert len(matches_c)==1,symbol"
assert generator.count(old)==1
generator=generator.replace(old,new)
generator=generator.replace('pin(BASE);','pin(PREVIOUS);pin(BASE);')
exec(compile(generator,str(PREVIOUS),'exec'),globals())
