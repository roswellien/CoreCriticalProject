"""Stage the resource-capability coordinator into a new verified runtime copy.

No native compilation, source regeneration or modification of the input runtime.
The output must pass the launcher's runtime validator before delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import re

from content_capabilities import advertised


def pin(path):
    with path.open('rb') as stream:
        return {'bytes': path.stat().st_size, 'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}


def stage(source, output, version):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Use a fresh output outside the input runtime')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}', version):
        raise ValueError('Invalid runtime version')
    paths = list(source.rglob('*'))
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in [source, *paths]):
        raise ValueError('Linked runtime inputs are unsupported')
    manifest_bytes = (source / 'runtime.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    input_pins = dict(manifest['files'])
    observed = {p.relative_to(source).as_posix() for p in paths if p.is_file()}
    if observed != set(manifest['files']) | {'runtime.json'}:
        raise ValueError('Runtime closure differs from its manifest')
    if manifest.get('profile') not in input_pins or manifest.get('profile') == 'runtime.json':
        raise ValueError('Unregistered runtime profile')
    for name, expected in manifest['files'].items():
        if name not in observed or pin(source / name) != expected:
            raise ValueError('Runtime member changed: ' + name)
    profile = json.loads((source / manifest['profile']).read_text(encoding='utf-8-sig'))
    capabilities = advertised(profile['native'])
    if not capabilities:
        raise ValueError('No reviewed capability declaration for this runtime')
    shutil.copytree(source, output)
    profile['native']['content_capabilities'] = capabilities
    (output / manifest['profile']).write_text(json.dumps(profile, indent=2) + '\n')
    for name in ('play_remaster.py', 'prepared_mech_packs.py', 'prepared_environment_packs.py',
<<<<<<< HEAD
                 'prepared_skin_packs.py', 'prepared_chassis_packs.py', 'legacy_chassis_resources.py', 'legacy_chassis_skins.py', 'chassis_catalog.py', 'chassis_icons.py',
                 'reader_archive.py', 'zrd_document.py',
                 'presentation_policy.py', 'content_capabilities.py', 'legacy_content_capabilities.json'):
=======
                 'prepared_skin_packs.py', 'prepared_chassis_packs.py', 'chassis_appearances.py', 'surface_catalog_composition.py', 'legacy_chassis_resources.py', 'chassis_catalog.py', 'chassis_icons.py',
                 'reader_archive.py', 'zrd_document.py', 'normal_materials.py', 'normal_codec.py',
                 'content_capabilities.py', 'legacy_content_capabilities.json'):
>>>>>>> origin/roswellien/feature/126-atlas-visual-options
        shutil.copyfile(Path(__file__).with_name(name), output / 'coordinator' / name)
    manifest['version'] = version
    manifest['files'] = {p.relative_to(output).as_posix(): pin(p) for p in output.rglob('*')
                         if p.is_file() and p != output / 'runtime.json'}
    (output / 'runtime.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Recheck all input pins after copying. A concurrent writer invalidates this
    # attempt; incomplete output is retained for diagnosis and never activated.
    if (source / 'runtime.json').read_bytes() != manifest_bytes:
        raise ValueError('Input manifest changed during staging')
    for name, expected in input_pins.items():
        if pin(source / name) != expected:
            raise ValueError('Input runtime changed during staging: ' + name)
    return capabilities


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.source, args.output, args.version), sort_keys=True))
