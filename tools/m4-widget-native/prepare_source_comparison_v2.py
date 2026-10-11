"""Add the unexecuted actual registry-source/tail comparer to the pure recipe."""
from pathlib import Path
import hashlib
P=Path(__file__).resolve().parent
prior=P/'prepare_source_comparison.py'
source=prior.read_text()
anchor="module.pin(path);G=module.load"
replacement="module.pin(path);registry=R/'tools/m4-widget-native/compare_registry.py';ast.parse(registry.read_text());module.pin(registry);sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as provider_responses;provider_responses.B.contracts();G=module.load"
assert source.count(anchor)==1
source=source.replace(anchor,replacement)
source=source.replace("source_provider_tail_full_comparison=False", "source_provider_tail_full_comparison_prepared=True,source_provider_tail_comparison=str(registry),source_provider_tail_comparison_sha256=sha(registry),source_provider_tail_full_comparison_executed=False")
source=source.replace("module.pin(__file__);module.pin(sys.executable)", "module.pin(prior);module.pin(__file__);module.pin(sys.executable)")
exec(compile(source,str(prior),'exec'),globals())
