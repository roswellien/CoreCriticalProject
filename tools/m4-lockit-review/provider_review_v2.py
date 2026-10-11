"""Bind corrected measured resource API index4 and final provider observer v6."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent;p=HERE/'provider_review.py';s=p.read_text(encoding='utf-8')
s=s.replace('tools/m4-lockit-source/compare_provider124_v5.py','tools/m4-lockit-source/compare_provider124_v6.py')
needle="            'tools/m4-lockit-source/responses.py', 'tools/m4-lockit-source/responses_v2.py',"
replacement=needle+"\n            'tools/m4-lockit-source/responses_v3.py', 'tools/m4-lockit-source/bridge_v2.py',"
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle="        pin(__file__); pin(Path(__file__).with_name('provider_exports.py'))"
replacement=needle+"; pin(ROOT/'tools/m4-lockit-review/provider_review.py')"
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle="        need(set(final_cases) == cases, 'All12 actual persistent provider cases sealed')"
extra="""
        for case in cases:
            first=[observed[case+(index,)] for index in range(6)]
            need(all(row['requested']=='InitializeCriticalSection'and row['witness_words'][31]==0 for row in first[:4]),
                 'Four genuine source CRT static lock APIs precede explicit resource association')
            need(first[4]['requested']=='InitializeCriticalSection'and first[4]['witness_words'][:5]==[1,4,0,0x78146190,0x866ce]
                 and first[4]['witness_words'][31]==1 and first[5]['requested']=='HeapAlloc'and first[5]['witness_words'][31]==0,
                 'Actual fifth resource Initialize index4 precedes source producer HeapAlloc index5 in every current case')
            counts['actual_index4_resource_association_identity_pairs']+=1
"""
assert s.count(needle)==1;s=s.replace(needle,needle+extra)
needle="generation == rel['generation'] > 0"
replacement="generation == rel['generation'] == 5"
assert s.count(needle)==1;s=s.replace(needle,replacement)
exec(compile(s,str(p),'exec'),globals())
