"""Final provider observer v7 and complete bounded Python dependency seal."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'provider_review_v2.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(p),'exec'),globals())"
assert s.count(needle)==1;s=s.replace(needle,'compiled_source=s')
context={'__file__':__file__,'__name__':'provider_review_deriver'};exec(compile(s,str(p),'exec'),context);source=context['compiled_source']
source=source.replace('tools/m4-lockit-source/compare_provider124_v6.py','tools/m4-lockit-source/compare_provider124_v7.py')
needle="        source_report = Path(source_report).resolve(); report = read(source_report)"
extra="""
        for toolpath,digest in report['files'].items():
            physical=Path(toolpath)
            if physical.suffix=='.py' and physical.resolve().is_relative_to(ROOT/'tools'):
                pin(physical,digest);counts['all_bound_provider_script_dependencies']+=1
        pin(ROOT/'tools/m4-lockit-review/provider_review_v2.py')
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
exec(compile(source,str(HERE/'provider_review.py'),'exec'),globals())
