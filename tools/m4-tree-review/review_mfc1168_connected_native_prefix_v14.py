"""Bind inlined provider TLS cells in the actual optimized Context functions."""
from pathlib import Path
BASE14=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v11.py')
program=BASE14.read_text()
program=program.replace('partial=current_body_matches(rr,rl);assert len(partial)==1',"partial=current_body_matches(rr,rl)if any(r['symbol']['name']in bridge_targets for r in rl)else linked_candidates(image,rr,rl);assert len(partial)==1")
program=program.replace('len(source_targets)==6','len(source_targets)>=6').replace("counts['actual_missing_thunk_source_CALL_targets']+=6","counts['actual_missing_thunk_source_CALL_targets']+=len(source_targets)")
names=('?owner@m4_nmx_integration@mw34@@3PEAVSession@12@EA','?owner@m4_spi_connected@mw34@@3PEAVSession@12@EA','?active@m4_mfc1168_connected@mw34@@3PEAVInvocation@12@EA','?emitter@?A0xC7D6B430@m4_mfc1168_connected@mw34@@3UEmitter@?A0xC7D6B430@12@A')
anchor="extra=literal(V4,'extra')"
assert program.count(anchor)==1
program=program.replace(anchor,'helper=helper.replace("TLS_names={",'+repr('TLS_names={'+','.join(repr(n)for n in names)+',')+')\n'+anchor)
program=program.replace('  pin(BASE);pin(V2);pin(V3);pin(V4);','  pin(BASE14);pin(BASE);pin(V2);pin(V3);pin(V4);')
exec(compile(program,str(BASE14),'exec'),globals())
