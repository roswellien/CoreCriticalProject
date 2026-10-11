"""Derive additive125 physical ABI/link/resource reviews from frozen124 tools."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tools/m4-tree-build-review'


def replace(text, old, new, count=1):
    assert text.count(old) == count, (old, text.count(old), count)
    return text.replace(old, new)


def write(name, text):
    destination = OUT / name
    assert not destination.exists(), destination
    if destination.suffix == '.py':
        ast.parse(text)
    destination.write_text(text, encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    old = ROOT / 'tools/m4-lockit-build-review'
    text = (old / 'review_v2.py').read_text()
    changes = [
        ('actual root124 final-link review', 'actual root125 final-link review'),
        ("BASE=ROOT/'reports/m4-lockit-build-review'", "BASE=ROOT/'reports/m4-tree-build-review'"),
        ("PREP=ROOT/'reports/m4-joint-startup124/preparation-r5'", "PREP=ROOT/'reports/m4-joint-startup125/preparation-r4'"),
        ("PREPSHA='7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7'", "PREPSHA='243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7'"),
        ("NPREP=ROOT/'reports/m4-lockit-native/preparation-r5'", "NPREP=ROOT/'reports/m4-tree-native/preparation-r5'"),
        ("NPSHA='965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1'", "NPSHA='9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2'"),
        ("OLD=ROOT/'reports/m4-joint-startup120/preparation-r3'", "OLD=ROOT/'reports/m4-joint-startup124/preparation-r5'"),
        ("OLDSHA='46e510f76d00722b2f46ef015d946a8ced3e0af0286e5ef8baf06e37797ff810'", "OLDSHA='7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7'"),
        ("BUILD=ROOT/'reports/m4-joint-startup124/build-r4/build.json'", "BUILD=ROOT/'reports/m4-joint-startup125/build-r1/build.json'"),
        ("BUILDSHA='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30'", "BUILDSHA='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165'"),
        ('Packed schema changed from accepted120', 'Packed schema changed from accepted124'),
        ('len(selected)==len(set(selected))==124', 'len(selected)==len(set(selected))==125'),
        ('len(registrations)==len(set(registrations))==96', 'len(registrations)==len(set(registrations))==97'),
        ('{0x411010,0x4dc140,0x500660,0x5968f0}', '{0x4b7f70}'),
        ("ROOT/'tools/m4-lockit-build-review/abi_witness.cpp'", "ROOT/'tools/m4-tree-build-review/abi_witness.cpp'"),
        ("ROOT/'tools/m4-lockit-build-review/build_abi.ps1'", "ROOT/'tools/m4-tree-build-review/build_abi.ps1'"),
        ('packed_schema_identical_to_accepted120=True', 'packed_schema_identical_to_accepted124=True'),
        ('selected_roots=124,registrations=96', 'selected_roots=125,registrations=97'),
        ('len(objects)==363', 'len(objects)==371'),
        ('len(literal)==363', 'len(literal)==371'),
        ("len(added)==12 and all('/m4-lockit-source/'in x.replace('\\\\','/')for x in added)", "len(added)==8 and all('/m4-tree-source/'in x.replace('\\\\','/')for x in added)"),
        ('len(linked)==392', 'len(linked)==400'),
        ('literal_COFFs=363,added_literal_COFFs=12', 'literal_COFFs=371,added_literal_COFFs=8'),
        ('actual_linked_inputs=392', 'actual_linked_inputs=400'),
        ('Actual O0/O2 root124 final-link', 'Actual O0/O2 root125 final-link'),
        ('literal_COFF_links=726', 'literal_COFF_links=742'),
        ('actual_linked_inputs=784', 'actual_linked_inputs=800'),
    ]
    for before, after in changes:
        text = replace(text, before, after)
    write('review.py', text)
    witness = (old / 'abi_witness.cpp').read_text()
    witness = replace(witness, 'entries.size()==124', 'entries.size()==125')
    witness = replace(witness, 'registration_roots.size()==96', 'registration_roots.size()==97')
    write('abi_witness.cpp', witness)
    wrapper = (old / 'build_abi_v2.ps1').read_text()
    write('build_abi.ps1', replace(wrapper, "'review_v2.py'", "'review.py'"))
    resource = (old / 'resource_v2.py').read_text()
    resource = replace(resource, 'from review_v2 import', 'from review import')
    resource = replace(resource, "session=pin(NPREP/'session_impl.inc')", "session=pin(NPREP/'session_impl.inc');tree_contract=pin(NPREP/'tree_contract.inc');tree_operations=pin(NPREP/'tree_operations.inc')")
    resource = replace(resource, "assert '#include \"lockit_contract.inc\"'in source.read_text()", "assert '#include \"lockit_contract.inc\"'in source.read_text() and '#include \"tree_contract.inc\"'in source.read_text()")
    resource = replace(resource, "assert '#include \"lockit_operations.inc\"'in pin(NPREP/'locale_batch_operations.inc').read_text()", "assert '#include \"lockit_operations.inc\"'in pin(NPREP/'locale_batch_operations.inc').read_text() and '#include \"tree_operations.inc\"'in pin(NPREP/'locale_batch_operations.inc').read_text()")
    resource = replace(resource, "expected=[source,contract,operations,session,", "expected=[source,contract,operations,session,tree_contract,tree_operations,")
    resource = replace(resource, "'Binding::dump_lockit']", "'Binding::dump_lockit','Binding::tree_enter','Binding::tree_role','Binding::tree_owner_before','Binding::tree_owner_after','Binding::tree_publish','Binding::tree_lockit_read','Binding::tree_lockit_called','Binding::tree_lockit_returned','Binding::tree_returned']")
    resource = replace(resource, 'actual_defined_resource_methods=7', 'actual_defined_resource_methods=16')
    resource = replace(resource, 'Current compiled Lockit resource dependencies', 'Current compiled tree and Lockit resource dependencies')
    write('resource.py', resource)
    print('Derived125 ABI/link/resource reviews and compiler witness')


if __name__ == '__main__':
    main()
