"""Keep exact full provider byte intervals; admit only authentic initialized path."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2];T=ROOT/'tools/m4-lockit-source'
source=(T/'provider_lift.py').read_text()
old="end=max(x['pc']+x['size']for x in g['instructions']);code=bytearray(b'\\xcc'*(end-entry))"
new="end=max(x['pc']+x['size']for x in g['instructions']);interval_offset,_=pe.rva_range(entry-pe.image_base,end-entry);code=bytearray(pe.data[interval_offset:interval_offset+end-entry])"
assert source.count(old)==1
source=source.replace(old,new)
source=source.replace("unique_decoded_bytes=sum(x['size']for x in g['instructions']),", "unique_decoded_bytes=sum(x['size']for x in g['instructions']),full_original_contiguous_interval=True,initialized_state2_only=True,unadmitted_cold_source_bytes_retained=True,")
source=source.replace('Exact initialized state2 MSVCP source/COFF preparation only, no initializer execution credit','Exact full original MSVCP contiguous source intervals and AMD64 COFF; admitted only authentic initializedstate2 17rows, no cold initialization/contended path or initializer execution credit')
(T/'provider_lift_v2.py').write_text(source)
print('Prepared exact physical provider interval lift; preserves failed sparse revision')
