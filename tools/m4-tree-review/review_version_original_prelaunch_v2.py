"""Retain full observer admission with exact physical-source and Writer layouts."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch.py');t=p.read_text()
a='assert len(source)==132';assert t.count(a)==1;t=t.replace(a,'assert len(source)==109')
a="'out(argv[4],\"'+str((R/'reports').resolve()).replace('\\\\','/')+'\")'"
b="'version_transport_options.reports_root=std::filesystem::path(\"'+str((R/'reports').resolve()).replace('\\\\','/')+'\")','Writer out(argv[4],std::move(version_transport_options))'"
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace('pin(__file__);pin(sys.executable)',"pin(R/'tools/m4-tree-review/review_version_original_prelaunch.py');pin(__file__);pin(sys.executable)")
exec(compile(t,str(Path(__file__)),'exec'),globals())
