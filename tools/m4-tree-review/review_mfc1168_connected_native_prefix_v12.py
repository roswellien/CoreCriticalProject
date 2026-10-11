"""The initializer's whole unique jump-only body also identifies its callee."""
from pathlib import Path
BASE12=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v11.py')
program=BASE12.read_text();old='partial=current_body_matches(rr,rl);assert len(partial)==1'
new="partial=current_body_matches(rr,rl)if any(r['symbol']['name']in bridge_targets for r in rl)else linked_candidates(image,rr,rl);assert len(partial)==1"
assert program.count(old)==1;program=program.replace(old,new)
program=program.replace('  pin(BASE);pin(V2);pin(V3);pin(V4);','  pin(BASE12);pin(BASE);pin(V2);pin(V3);pin(V4);')
exec(compile(program,str(BASE12),'exec'),globals())
