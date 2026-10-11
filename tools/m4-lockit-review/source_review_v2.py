"""Review both resource seam and physical-provider PE name isolation fixes."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'source_review.py';s=p.read_text(encoding='utf-8')
s=s.replace('compare_connected_v6.py','compare_connected_v7.py')
needle="        paths={name:ROOT/'tools/m4-lockit-source'/name for name in ('compare_connected_v7.py','responses_v3.py','bridge_v2.py')}"
extra="""        image=read(ROOT/'reports/m4-lockit-source/image-preparation-r1/report.json')
        need(image['passed'],'Distinct physical provider PE image preparation')
        for prefix in ('connected','provider124'):
            before=ROOT/f'tools/m4-lockit-source/compare_{prefix}_v6.py'
            after=ROOT/f'tools/m4-lockit-source/compare_{prefix}_v7.py'
            old=pin(before,image['files'][str(before.resolve())]).read_text(encoding='utf-8')
            new=pin(after,image['files'][str(after.resolve())]).read_text(encoding='utf-8')
            expected=old.replace('cp=PE.PEImage(provider)','physical_provider_image=PE.PEImage(provider)').replace('cp.sections','physical_provider_image.sections').replace('cp.image_base','physical_provider_image.image_base')
            need(new==expected and new.count('physical_provider_image=PE.PEImage(provider)')==1,
                 'Only physical PE image variable rename; accepted numerical cp result and all semantics retained')
            counts['reviewed_physical_provider_name_isolations']+=1
"""
assert s.count(needle)==1;s=s.replace(needle,extra+needle)
needle="pin(path,association['files'][str(path.resolve())])"
replacement="pin(path,(association['files'] if str(path.resolve()) in association['files'] else image['files'])[str(path.resolve())])"
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle="        pin(__file__);source_report=Path(source_report).resolve();report=read(source_report)"
replacement="        pin(__file__);pin(ROOT/'tools/m4-lockit-review/source_review.py');source_report=Path(source_report).resolve();report=read(source_report)"
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle="        need(report['passed'],'Fresh actual persistent124 source proof passed')"
extra="""
        for toolpath,digest in report['files'].items():
            physical=Path(toolpath)
            if physical.suffix=='.py' and physical.resolve().is_relative_to(ROOT/'tools'):
                pin(physical,digest);counts['all_bound_source_script_dependencies']+=1
"""
assert s.count(needle)==1;s=s.replace(needle,needle+extra)
exec(compile(s,str(p),'exec'),globals())
