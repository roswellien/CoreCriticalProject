"""Build owner-authorized private precompiled MW3 updates for existing launchers.

Uses the existing native-preparer contract. The launcher verifies originals,
signature, ZIP and files, runs the signed copy tool, validates the complete
runtime and atomically selects it. No compiler or original image is packaged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def pin(path):
    with path.open('rb') as stream:
        return dict(bytes=path.stat().st_size,
                    sha256=hashlib.file_digest(stream, 'sha256').hexdigest())


def package(runtime, preparer, game, output, version, sequence, signing_key, key_id,
            package_url='', minimum_launcher_version='1.0.24'):
    runtime, preparer, game, output = map(Path, (runtime, preparer, game, output))
    if output.exists() or sequence < 1:
        raise ValueError('Use a fresh output directory and positive sequence')
    for source in (runtime, game, preparer):
        if output.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(output.resolve()):
            raise ValueError('Update output must not overlap its inputs')
    if Path(signing_key).resolve().is_relative_to(output.resolve()):
        raise ValueError('The private signing key must stay outside the update output')
    from re import fullmatch
    if not fullmatch(r'\d+\.\d+\.\d+', minimum_launcher_version):
        raise ValueError('Invalid minimum launcher version')
    if not fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*)?', version):
        raise ValueError('Use the public release version for update filenames, for example 1.0.34.mw3update')
    for path in (runtime, preparer, game, *runtime.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Linked package inputs are unsupported')
    manifest = json.loads((runtime / 'runtime.json').read_text(encoding='utf-8-sig'))
    if manifest.get('precompiled_runtime_version') != 1:
        raise ValueError('An explicitly precompiled runtime is required')
    observed = {p.relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file()}
    if observed != set(manifest['files']) | {'runtime.json'}:
        raise ValueError('Runtime has missing or unregistered files')
    files = {'InstallPrecompiledRuntime.exe': pin(preparer)}
    sources = {'InstallPrecompiledRuntime.exe': preparer}
    for name in sorted(observed):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
            raise ValueError('Invalid runtime member')
        source = runtime / relative
        actual = pin(source)
        if name != 'runtime.json' and actual != manifest['files'][name]:
            raise ValueError('Runtime identity changed: ' + name)
        files['Runtime/' + name] = actual
        sources['Runtime/' + name] = source
    originals = {'MECH3.EXE': pin(game / 'MECH3.EXE')}
    if originals['MECH3.EXE']['sha256'] in {p['sha256'] for p in files.values()}:
        raise ValueError('Original executable must not be packaged')
    if sum(p['bytes'] for p in files.values()) > 2 * 1024**3:
        raise ValueError('Expanded update exceeds launcher limit')
    output.mkdir(parents=True)
    archive = output / (version + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        for name, source in sources.items():
            target.write(source, name)
    if any(pin(source) != files[name] for name, source in sources.items()):
        raise ValueError('Update inputs changed during packaging')
    archive_pin = pin(archive)
    if archive_pin['bytes'] > 512 * 1024**2:
        raise ValueError('Compressed update exceeds launcher limit')
    update = dict(schema_version=1, game_id='mw3', version=version, sequence=sequence,
                  minimum_launcher_version=minimum_launcher_version, preparation_contract='mw3-local-runtime-v1',
                  package_url=package_url, package_bytes=archive_pin['bytes'],
                  package_sha256=archive_pin['sha256'], preparer='InstallPrecompiledRuntime.exe',
                  files=files, original_inputs=originals)
    unsigned = output / 'manifest.json'
    unsigned.write_text(json.dumps(update, separators=(',', ':')) + '\n', encoding='utf-8')
    signer = Path(__file__).resolve().parents[1] / 'mw3-remaster-launcher/sign_runtime_update.ps1'
    subprocess.run(['pwsh', '-NoProfile', '-File', str(signer), '-Manifest', str(unsigned),
                    '-SigningKey', str(signing_key), '-KeyId', key_id, '-OutputFile',
                    str(output / (version + '.mw3update'))], check=True)
    receipt = dict(kind='private-precompiled-runtime-update', version=version,
                   sequence=sequence, files=len(files), package=archive_pin,
                   original_images_included=0, generation_required=False)
    (output / 'package.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('runtime', 'preparer', 'game', 'output', 'signing-key'):
        parser.add_argument('--' + key, required=True, type=Path)
    for key in ('version', 'key-id'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--sequence', required=True, type=int)
    parser.add_argument('--package-url', default='')
    parser.add_argument('--minimum-launcher-version', default='1.0.24')
    print(json.dumps(package(**vars(parser.parse_args())), indent=2))
