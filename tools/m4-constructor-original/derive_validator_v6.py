"""Distinguish literal MFC argument from physical CRT-rounded API request."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;t=(h/'validate_v5.py').read_text();out=h/'validate_v6.py'
if out.exists():raise ValueError('Fresh additive validator required')
a="        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)"
b="""        rounding=read(BASE/'request-rounding-r1/report.json',__ROUNDING_DIGEST__);need(rounding['passed'],'Whole physical CRT mode1 requested-size contract')
        for path,digest in rounding['files'].items():pin(path,digest)
        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)"""
from hashlib import sha256
digest=sha256((h.parents[1]/'reports/m4-constructor-original/request-rounding-r1/report.json').read_bytes()).hexdigest()
b=b.replace('__ROUNDING_DIGEST__',repr(digest))
if t.count(a)!=1:raise ValueError('Exact physical rounding binding')
t=t.replace(a,b,1)
a="need(v[6]==requested and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and requested bytes')"
b="""need(mode==rounding['admitted_heap_mode']and requested<=rounding['source_request_max'],'Exact finite observed mode1 normal source request domain')
                            rounded=((requested if requested else rounding['zero_normalization'])+rounding['rounding_addend'])&rounding['rounding_mask']
                            need(v[6]==api[22]==rounded and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and literal rounded API request')
                            row['source_MFC_requested']=requested;row['source_derived_HeapAlloc_requested']=rounded;counts['literal_CRT_request_rounding_joins']+=1"""
if t.count(a)!=1:raise ValueError('Exact one faulty request comparison')
t=t.replace(a,b,1)
a="pin(Path(__file__).with_name('derive_validator_v5.py'));pin(sys.executable);passed=True";b="pin(Path(__file__).with_name('derive_validator_v5.py'));pin(Path(__file__).with_name('validate_v5.py'));pin(Path(__file__).with_name('derive_validator_v6.py'));pin(sys.executable);passed=True"
if t.count(a)!=1:raise ValueError('Exact checker lineage')
t=t.replace(a,b,1);ast.parse(t);out.write_text(t)
