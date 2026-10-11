"""Bind provider v8 and prove its sole v7 delta is post-pass progress output."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'provider_review_v3.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(source,str(HERE/'provider_review.py'),'exec'),globals())"
assert s.count(needle)==1;s=s.replace(needle,'compiled_source=source')
context={'__file__':__file__,'__name__':'provider_review_deriver'};exec(compile(s,str(p),'exec'),context);source=context['compiled_source']
source=source.replace('tools/m4-lockit-source/compare_provider124_v7.py','tools/m4-lockit-source/compare_provider124_v8.py')
needle="        source_report = Path(source_report).resolve(); report = read(source_report)"
extra="""
        progress=read(ROOT/'reports/m4-lockit-source/provider-progress-preparation-r1/report.json',
                      'c50146d0ababecfd944f5268d7402379a6c6cbcbabea0e9be03846bdeab49874')
        need(progress['passed']and not progress['native_executed']and not progress['initializer_credit'],
             'Progress-only preparation has no execution or initializer credit')
        for toolpath,digest in progress['files'].items():pin(toolpath,digest)
        old=ROOT/'tools/m4-lockit-source/compare_provider124_v7.py';new=ROOT/'tools/m4-lockit-source/compare_provider124_v8.py'
        anchor="counts['persistent124_sequences']+=1;F.finish(machine,responses,expected_callbacks,G)"
        addition=";print(json.dumps(dict(provider_case_passed=True,level=level,sequence=seq,API_count=responses.index)),flush=True)"
        prior=old.read_text(encoding='utf-8');need(prior.count(anchor)==1 and new.read_text(encoding='utf-8')==prior.replace(anchor,anchor+addition),
             'Only actual v8 delta emits compact progress after existing entire lifecycle comparison')
        pin(ROOT/'tools/m4-lockit-review/provider_review_v3.py');counts['reviewed_progress_only_additions']+=1
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
exec(compile(source,str(HERE/'provider_review.py'),'exec'),globals())
