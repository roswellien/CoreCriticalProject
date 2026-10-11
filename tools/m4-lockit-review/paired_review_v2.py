"""Bind every executed paired Python dependency and final strict source review."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'paired_review.py';source=p.read_text(encoding='utf-8')
needle="        report=read(paired_report);source=read(source_report)"
extra="""
        pin(ROOT/'tools/m4-lockit-review/paired_review.py')
        for toolpath,digest in report['files'].items():
            physical=Path(toolpath)
            if physical.suffix=='.py'and physical.resolve().is_relative_to(ROOT/'tools'):
                pin(physical,digest);counts['all_bound_paired_script_dependencies']+=1
        source_review=read(ROOT/'reports/m4-lockit-review/source-review-r1/report.json',
                           '9110f2838ddb908c3f3613e3c69862f25d40085556622abd4655c218ae748ee0')
        need(source_review['passed']and source_review['files'][str(source_report.resolve())]==sha(source_report),
             'Paired stack and whole native source observations bind exact independently reviewed final source gate')
"""
assert source.count(needle)==1;source=source.replace(needle,needle+extra)
exec(compile(source,str(p),'exec'),globals())
