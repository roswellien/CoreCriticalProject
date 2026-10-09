"""Literal author-observer derivative: guest model unchanged, numerical host scope explicit."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2]
old=root/'tools/m4-fp-numeric-max-integration/observe.py'
pins=json.loads((root/'reports/m4-fp-numeric-max-integration/author-review-r1/pins.json').read_text())['files']
assert hashlib.sha256(old.read_bytes()).hexdigest()==pins[str(old)]
s=old.read_text()
changes=[
("out.parent==ROOT/'reports/m4-fp-numeric-max-integration'", "out.parent==ROOT/'reports/m4-fp-numeric-max-host-boundary'"),
("eq('full_actual_host_FX_restoration',n[45068:45580],n[45580:46092]);", "hb=n[45068:45580];ha=n[45580:46092];eq('direct_numerical_host_FX_before_cleanup',[hb[:5],hb[24:28]]+[hb[32+i*16:42+i*16] for i in range(8)],[ha[:5],ha[24:28]]+[ha[32+i*16:42+i*16] for i in range(8)]);eq('direct_host_BEFORE_CW_SW_tags_MXCSR',(u16(hb),u16(hb,2),hb[4],u32(hb,24)),(struct.unpack_from('<10I',n)[3],0x3a20,0x81,0x1f80));eq('direct_host_BEFORE_raw80',[hb[32+i*16:42+i*16] for i in range(8)],[struct.pack('<QH',0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0)) for i in range(8)]);eq('direct_host_BEFORE_legacy_ENV',n[46092:46120],struct.pack('<7I',0xffff0000|struct.unpack_from('<10I',n)[3],0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b));"),
("eq('full_actual_host_ENV_restoration'", "eq('direct_actual_host_ENV_before_cleanup'"),
("45580+400,", "45580+24,"),
("'scope':'Shared-r9 numeric-max compiled author model and offline original observations; no original process run, full startup incomplete'", "'scope':'New explicit Session-owned outer invoke numerical boundary; direct capture before harness cleanup; guest model and original BEFORE projections unchanged; full startup incomplete'"),
("'original_after_execution_inputs':False", "'host_boundary':'Required Session.invoke status-return API catches internally then restores x87/raw80/legacy ENV/CW/status/MXCSR. Direct Runtime calls and construction/borrow exceptions outside it have no preservation claim. Volatile SIMD and reserved FX storage are observed only.', 'original_after_execution_inputs':False"),
]
for a,b in changes:
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b)
needle=" report={'passed':not any(r['differences'] for r in reports)"
assert s.count(needle)==1
s=s.replace(needle,"""  # Positive scope control: volatile SIMD and reserved FX storage may change.
  for off in (45580+400,45580+5,45580+500):
   q=bytearray(sample);q[off]^=1;assert not check(q,bytes(expected_before),previous[28684:45068]);control_count+=1
"""+needle)
out=Path(__file__).with_name('observe.py');assert not out.exists();out.write_text(s)
print(hashlib.sha256(out.read_bytes()).hexdigest())
