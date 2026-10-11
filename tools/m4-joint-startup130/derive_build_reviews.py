"""Derive additive130 ABI/link/resource checks from accepted125 tooling."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tools/m4-startup130-build-review'
OLD = ROOT / 'tools/m4-tree-build-review'


def one(text, before, after):
    assert text.count(before) == 1, (before, text.count(before))
    return text.replace(before, after)


def write(name, text):
    destination = OUT / name
    assert not destination.exists(), destination
    if destination.suffix == '.py':
        ast.parse(text)
    destination.write_text(text, encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    text = (OLD / 'review.py').read_text()
    substitutions = [
        ('actual root125 final-link review', 'actual root130 final-link review'),
        ("BASE=ROOT/'reports/m4-tree-build-review'", "BASE=ROOT/'reports/m4-startup130-build-review'"),
        ("PREP=ROOT/'reports/m4-joint-startup125/preparation-r4'", "PREP=ROOT/'reports/m4-joint-startup130/preparation-r1'"),
        ("PREPSHA='243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7'", "PREPSHA='21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f'"),
        ("NPREP=ROOT/'reports/m4-tree-native/preparation-r5'", "NPREP=ROOT/'reports/m4-formatting-native/preparation-r18'"),
        ("NPSHA='9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2'", "NPSHA='68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06'"),
        ("OLD=ROOT/'reports/m4-joint-startup124/preparation-r5'", "OLD=ROOT/'reports/m4-joint-startup125/preparation-r4'"),
        ("OLDSHA='7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7'", "OLDSHA='243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7'"),
        ("BUILD=ROOT/'reports/m4-joint-startup125/build-r1/build.json'", "BUILD=ROOT/'reports/m4-joint-startup130/build-r1/build.json'"),
        ("BUILDSHA='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165'", "BUILDSHA='4ccb1347bd85872f06ff6a57d1bd539effcd6d24de1c302b7cb2e4758b3ea976'"),
        ('Packed schema changed from accepted124', 'Packed schema changed from accepted125'),
        ('len(selected)==len(set(selected))==125', 'len(selected)==len(set(selected))==130'),
        ('len(registrations)==len(set(registrations))==97', 'len(registrations)==len(set(registrations))==101'),
        ('len(extra)==len(set(extra))==26', 'len(extra)==len(set(extra))==29'),
        ('=={0x4b7f70}', '=={0x4df610,0x4e0710,0x4e0810,0x4e1ca0,0x4b64f0}'),
        ("if x not in n['new_roots']", "if x not in p['new_roots']"),
        ('len(set(fixed+extra))==43', 'len(set(fixed+extra))==46'),
        ("ROOT/'tools/m4-tree-build-review/abi_witness.cpp'", "ROOT/'tools/m4-startup130-build-review/abi_witness.cpp'"),
        ("ROOT/'tools/m4-tree-build-review/build_abi.ps1'", "ROOT/'tools/m4-startup130-build-review/build_abi.ps1'"),
        ('packed_schema_identical_to_accepted124=True', 'packed_schema_identical_to_accepted125=True'),
        ('unique_whole_pages=43,selected_roots=125,registrations=97', 'unique_whole_pages=46,selected_roots=130,registrations=101'),
        ('len(objects)==371', 'len(objects)==397'),
        ('len(literal)==371', 'len(literal)==397'),
        ("assert len(added)==8 and all('/m4-tree-source/'in x.replace('\\\\','/')for x in added)",
         "expected_added={str(Path(row['objects'][level]['path']).resolve()).casefold()for row in n['formatting_bodies'].values()};cosine=json.loads(pin(ROOT/'reports/m4-cosine-native/runtime-preparation-r2/report.json','6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e').read_bytes());expected_added.add(str(Path(cosine['objects'][level]['path']).resolve()).casefold());assert len(added)==len(expected_added)==26 and {str(Path(x).resolve()).casefold()for x in added}==expected_added"),
        ('len(compiled)==27 and len(linked)==400', 'len(compiled)==30 and len(linked)==429'),
        ('literal_COFFs=371,added_literal_COFFs=8,compiled_objects=27', 'literal_COFFs=397,added_literal_COFFs=26,compiled_objects=30'),
        ('actual_linked_inputs=400', 'actual_linked_inputs=429'),
        ('Actual O0/O2 root125 final-link', 'Actual O0/O2 root130 final-link'),
        ('literal_COFF_links=742,compiled_objects=54,actual_linked_inputs=800', 'literal_COFF_links=794,compiled_objects=60,actual_linked_inputs=858'),
        ('pin(__file__);return out,pins,pin,p,n,old', "pin(__file__);pin(ROOT/'tools/m4-joint-startup130/derive_build_reviews.py');pin(ROOT/'tools/m4-tree-build-review/review.py');return out,pins,pin,p,n,old"),
    ]
    for before, after in substitutions:
        text = one(text, before, after)
    write('review.py', text)
    witness = (OLD / 'abi_witness.cpp').read_text()
    for before, after in [('entries.size()==125','entries.size()==130'),
                          ('registration_pages.size()==26','registration_pages.size()==29'),
                          ('registration_roots.size()==97','registration_roots.size()==101')]:
        witness = one(witness, before, after)
    write('abi_witness.cpp', witness)
    write('build_abi.ps1', (OLD / 'build_abi.ps1').read_text())
    resource = (OLD / 'resource.py').read_text()
    resource = one(resource, "tree_operations=pin(NPREP/'tree_operations.inc')",
        "tree_operations=pin(NPREP/'tree_operations.inc');format_contract=pin(NPREP/'formatting_contract.inc');format_operations=pin(NPREP/'formatting_operations.inc');mixed_contract=pin(NPREP/'mixed_format_contract.inc');mixed_operations=pin(NPREP/'mixed_format_operations.inc')")
    resource = one(resource, 'expected=[source,contract,operations,session,tree_contract,tree_operations,',
        'expected=[source,contract,operations,session,tree_contract,tree_operations,format_contract,format_operations,mixed_contract,mixed_operations,')
    resource = one(resource, 'Current compiled tree and Lockit resource dependencies',
        'Current compiled formatting, mixed, tree and Lockit resource dependencies')
    write('resource.py', resource)
    print('Derived130 compiler ABI, exact final link and resource checks')


if __name__ == '__main__':
    main()
