"""Measure the actual native host against an independent file-to-image model.

Only image inspection and explicit unresolved-entry failure are exercised.
No game instructions, DLL loading or gameplay are executed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/analysis'))
from pe import PEImage

IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def verify(host, windows_probe, image_path, out):
    require(host.is_file(), 'Required native host unavailable')
    original = image_path.read_bytes()
    require(len(original) == 2384384 and sha(original) == IMAGE_SHA, 'Exact original image admission differs')
    require(not out.exists(), 'Refusing to overwrite M4 original-image observation')
    out.mkdir(parents=True)
    expected = PEImage(original)
    actual = subprocess.run([str(host), '--inspect-image', str(image_path)], capture_output=True, timeout=30)
    (out/'inspect.stdout.json').write_bytes(actual.stdout)
    (out/'inspect.stderr').write_bytes(actual.stderr)
    require(actual.returncode == 0 and not actual.stderr, 'Actual native image inspection failed')
    observed = json.loads(actual.stdout)
    for key, value in {'schema_version': 1, 'status': 'image_mapped_startup_not_executed',
                       'native_pointer_bits': 64, 'guest_pointer_bits': 32,
                       'image_sha256': IMAGE_SHA, 'image_base': expected.image_base,
                       'image_size': expected.size_of_image, 'size_of_headers': expected.size_of_headers,
                       'entry_point': expected.image_base+expected.entry_point_rva,
                       'entry_point_rva': expected.entry_point_rva,
                       'section_alignment': expected.section_alignment, 'file_alignment': expected.file_alignment,
                       'original_x86_executed': False, 'import_resolution_performed': False,
                       'native_startup_implemented': False, 'iat_values_preserved': True}.items():
        require(observed[key] == value, 'Native mapped metadata differs: '+key)
    # Construct an independent byte model from the exact admitted file. This
    # Python observer does not supply image bytes or expected results to C++.
    aligned = lambda n: (n+4095)&~4095
    regions = [(expected.image_base, aligned(expected.size_of_headers), 1,
                original[:expected.size_of_headers])]
    for section in expected.sections:
        permissions = ((1 if section['readable'] else 0) | (2 if section['writable'] else 0) |
                       (4 if section['executable'] else 0))
        size = aligned(max(section['virtual_size'], section['raw_size']))
        backed = original[section['raw_offset']:section['raw_offset']+section['raw_size']]
        regions.append((expected.image_base+section['virtual_address'], size, permissions, backed))
    require(len(observed['regions']) == len(regions) == 5, 'Native mapped region count differs')
    for record, (address, size, permissions, backed) in zip(observed['regions'], regions):
        require((record['address'], record['size'], record['permissions']) == (address, size, permissions),
                'Native region address, extent or permissions differ')
        expected_bytes = backed+bytes(size-len(backed))
        require(record['actual_mapped_sha256'] == sha(expected_bytes), 'Actual native full-region bytes differ')
    passive = subprocess.run([str(windows_probe), str(image_path)], capture_output=True, timeout=30)
    (out/'windows-passive-image.stdout.json').write_bytes(passive.stdout)
    (out/'windows-passive-image.stderr').write_bytes(passive.stderr)
    require(passive.returncode == 0 and not passive.stderr, 'Independent Windows passive image observation failed')
    windows = json.loads(passive.stdout)
    require(windows['source'] == 'Windows_SEC_IMAGE_NO_EXECUTE' and
            windows['original_x86_executed'] is False and windows['dll_loader_used'] is False and
            windows['imports_resolved'] is False and windows['image_sha256'] == IMAGE_SHA and
            len(windows['regions']) == 5, 'Passive Windows image provenance differs')
    for actual_region, windows_region in zip(observed['regions'], windows['regions']):
        require(actual_region['address']-expected.image_base == windows_region['rva'] and
                actual_region['size'] == windows_region['size'] and
                actual_region['actual_mapped_sha256'] == windows_region['actual_mapped_sha256'],
                'Native bytes differ from actual Windows passive image mapping')
    imports = expected.imports()
    symbols = [(library['library'], symbol) for library in imports for symbol in library['symbols']]
    require(observed['import_library_count'] == len(imports) == 18 and
            observed['unresolved_import_count'] == len(symbols) == len(observed['imports']) == 474,
            'Native unresolved import count differs')
    for actual_symbol, (library, expected_symbol) in zip(observed['imports'], symbols):
        require(actual_symbol['library'] == library, 'Native import library differs')
        for key, value in expected_symbol.items():
            require(actual_symbol[key] == value, 'Native import metadata differs: '+key)
        value = expected.rva_u32(expected_symbol['iat_rva'])
        require(actual_symbol['original_iat_value'] == value, 'Actual native IAT value changed')
        require(actual_symbol['iat_permissions'] == 1, 'Native MW3 IAT permission differs')
    unresolved = subprocess.run([str(host), '--image', str(image_path)], capture_output=True, timeout=30)
    (out/'unresolved.stdout').write_bytes(unresolved.stdout)
    (out/'unresolved.stderr.json').write_bytes(unresolved.stderr)
    reason = json.loads(unresolved.stderr)
    require(unresolved.returncode == 3 and not unresolved.stdout and reason['status'] == 'unresolved_native_startup' and
            reason['guest_pc'] == 0x5ac3a0 and reason['image_mapping_complete'] is True and
            reason['original_x86_executed'] is False, 'Required startup path did not fail visibly')
    negative = []
    for name, offset in (('changed_header', 0), ('changed_startup_code', expected.rva_range(expected.entry_point_rva, 1)[0])):
        changed = bytearray(original)
        changed[offset] ^= 1
        path = out/(name+'.exe')
        path.write_bytes(changed)
        run = subprocess.run([str(host), '--inspect-image', str(path)], capture_output=True, timeout=30)
        (out/(name+'.stdout')).write_bytes(run.stdout)
        (out/(name+'.stderr')).write_bytes(run.stderr)
        require(run.returncode == 1 and not run.stdout and b'Wrong M4 image identity' in run.stderr,
                'Modified real image did not reach identity rejection: '+name)
        negative.append({'name': name, 'input_sha256': sha(changed), 'exit_code': run.returncode,
                         'intended_identity_diagnostic': True, 'output_bytes': len(run.stdout)})
    report = {'schema_version': 1, 'passed': True, 'experiment': 'native_M4_PE_image_mapping_foundation',
              'host_path': str(host), 'host_sha256': sha(host.read_bytes()), 'image_path': str(image_path),
              'windows_probe_path': str(windows_probe), 'windows_probe_sha256': sha(windows_probe.read_bytes()),
              'image_sha256': IMAGE_SHA, 'mapped_regions_compared': 5,
              'mapped_bytes_compared': sum(r[1] for r in regions), 'imports_compared': 474,
              'defined_mapping_differences': 0, 'changed_image_rejections': negative,
              'unresolved_entry_verified': True, 'native_game_startup_or_menus_proven': False,
              'windows_passive_image_mapping_compared': True,
              'original_x86_executed': False, 'scripts': {
                  str(Path(__file__).resolve()): sha(Path(__file__).read_bytes()),
                  str(ROOT/'tools/analysis/pe.py'): sha((ROOT/'tools/analysis/pe.py').read_bytes())},
              'files': {str(p.resolve()): sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--windows-probe', type=Path, required=True)
    parser.add_argument('--image', type=Path, default=ROOT/'MW3/Mech3.exe')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.host.resolve(), args.windows_probe.resolve(), args.image.resolve(), args.out.resolve())
        print(json.dumps({'passed': result['passed'], 'regions': result['mapped_regions_compared'],
                          'mapped_bytes': result['mapped_bytes_compared'], 'imports': result['imports_compared'],
                          'unresolved_entry_verified': result['unresolved_entry_verified']}))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise SystemExit('M4 native mapping proof rejected: '+str(error))
