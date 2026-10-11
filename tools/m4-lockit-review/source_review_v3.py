"""Seal every source/native-integration review wrapper in the final light gate."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'source_review_v2.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(p),'exec'),globals())"
assert s.count(needle)==1;s=s.replace(needle,'compiled_source=s')
context={'__file__':__file__,'__name__':'source_review_deriver'};exec(compile(s,str(p),'exec'),context);source=context['compiled_source']
needle="        pin(__file__);pin(ROOT/'tools/m4-lockit-review/source_review.py');source_report=Path(source_report).resolve();report=read(source_report)"
extra="""
        pin(ROOT/'tools/m4-lockit-review/source_review_v2.py')
        for helper in (ROOT/'tools/m4-lockit-review').glob('native_integration_review*.py'):
            pin(helper);counts['bound_native_integration_review_wrappers']+=1
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
exec(compile(source,str(HERE/'source_review.py'),'exec'),globals())
