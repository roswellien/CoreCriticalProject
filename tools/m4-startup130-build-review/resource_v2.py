"""Reuse the actual accepted15-method resource audit and add current observers."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).resolve().parents[1] / 'm4-tree-build-review/resource_v2.py'
text = parent.read_text()
before = "tree_operations=pin(NPREP/'tree_operations.inc')"
assert text.count(before) == 1
text = text.replace(before, before + ";format_contract=pin(NPREP/'formatting_contract.inc');format_operations=pin(NPREP/'formatting_operations.inc');mixed_contract=pin(NPREP/'mixed_format_contract.inc');mixed_operations=pin(NPREP/'mixed_format_operations.inc')")
before = 'expected=[source,contract,operations,session,tree_contract,tree_operations,'
assert text.count(before) == 1
text = text.replace(before, 'expected=[source,contract,operations,session,tree_contract,tree_operations,format_contract,format_operations,mixed_contract,mixed_operations,')
before = "'Binding::tree_returned']"
assert text.count(before) == 1
text = text.replace(before, "'Binding::tree_returned','Binding::formatting_guard','Binding::formatting_enter','Binding::formatting_owner_before','Binding::formatting_owner_after','Binding::formatting_read','Binding::formatting_called','Binding::formatting_returned','Binding::mixed_format_enter','Binding::mixed_format_owner_before','Binding::mixed_format_called','Binding::mixed_format_returned']")
assert text.count('actual_defined_resource_methods=15') == 1
text = text.replace('actual_defined_resource_methods=15', 'actual_defined_resource_methods=26')
text = text.replace('Current compiled tree and Lockit resource dependencies', 'Current compiled formatting, mixed, tree and Lockit resource dependencies')
before = 'common(name);pin(__file__)'
assert text.count(before) == 1
text = text.replace(before, "common(name);pin(__file__);pin(ROOT/'tools/m4-tree-build-review/resource_v2.py');pin(ROOT/'tools/m4-startup130-build-review/review.py')")
exec(compile(text, str(parent), 'exec'), globals())
