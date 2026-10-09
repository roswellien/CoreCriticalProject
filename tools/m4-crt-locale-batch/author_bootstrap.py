"""Create fresh mutable locale author sources; accepted allocator bytes stay read-only."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'reports/m4-crt-allocation/preparation-r7'
PAIRS={'allocation.hpp':'locale_batch.hpp','allocation_binding.inc':'locale_batch_binding.inc',
       'allocation_operations.inc':'locale_batch_allocator.inc','forward_identity.inc':'forward_identity.inc'}
for old,new in PAIRS.items():
 p=HERE/new
 if p.exists():raise RuntimeError(f'No overwrite: {p}')
 s=(OLD/old).read_text()
 s=s.replace('mw34::m4_crt_allocation','mw34::m4_crt_locale_batch')
 s=s.replace('#include "allocation_operations.inc"','#include "locale_batch_allocator.inc"')
 p.write_text(s)
