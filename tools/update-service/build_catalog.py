"""Publish inputs for the signed online catalog; never include private signing material.

Run after the ordinary launcher/runtime builders. This packages discovery only;
individual update metadata/payloads remain unchanged and independently signed.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


def pin(path):
    with path.open('rb') as stream:
        return dict(bytes=path.stat().st_size, sha256=hashlib.file_digest(stream, 'sha256').hexdigest())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--launcher', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--base-url', required=True)
    p.add_argument('--sequence', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--signing-key', type=Path, required=True)
    p.add_argument('--key-id', required=True)
    p.add_argument('--trust-file', type=Path, required=True)
    p.add_argument('--launcher-notes-file', type=Path)
    p.add_argument('--runtime-notes-file', type=Path)
    a = p.parse_args()
    launcher_notes = a.launcher_notes_file.read_text(encoding='utf-8') if a.launcher_notes_file else None
    runtime_notes = a.runtime_notes_file.read_text(encoding='utf-8') if a.runtime_notes_file else None
    if any(notes is not None and (len(notes) > 16384 or '\0' in notes) for notes in (launcher_notes, runtime_notes)):
        raise ValueError('Release notes must be bounded plain text')
    address = urlsplit(a.base_url)
    if address.scheme != 'https' or not address.hostname or address.username or address.query or address.fragment or address.path not in ('', '/'):
        raise ValueError('Use the approved HTTPS update origin')
    if a.sequence < 1 or a.output.exists() or a.signing_key.resolve().is_relative_to(a.output.resolve()):
        raise ValueError('Use a fresh output, positive catalog sequence and an external signing key')
    a.output.mkdir(parents=True)
    objects, releases = [], []
    for source, target in ((a.launcher, 'launcher'), (a.runtime, 'mw3')):
        manifest = json.loads(base64.b64decode(json.loads(source.read_text(encoding='utf-8-sig'))['payload']))
        version = manifest['version']
        if not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('Online schema v1 requires an explicit numeric public release version')
        extension = 'ccupdate' if target == 'launcher' else 'mw3update'
        if source.name != version + '.' + extension:
            raise ValueError('Update metadata must retain the public release filename')
        package = source.with_suffix('.zip')
        package_pin = pin(package)
        if package_pin != dict(bytes=manifest['package_bytes'], sha256=manifest['package_sha256']):
            raise ValueError('Package does not match its signed metadata')
        if target == 'launcher':
            if manifest['product_id'] != 'corecritical' or manifest['update_type'] != 'launcher-inno-v1':
                raise ValueError('Unsupported launcher update')
        elif manifest.get('game_id', 'mw3') != 'mw3' or manifest['preparation_contract'] != 'mw3-local-runtime-v1' or 'Runtime/runtime.json' not in manifest['files']:
            raise ValueError('Online runtime delivery requires the precompiled MW3 package')
        references = []
        for file in (source, package):
            public_path = '/' + target + '/' + version + '/' + file.name
            identity = pin(file)
            objects.append(dict(source=str(file.resolve()), key='online-updates' + public_path, public_path=public_path, **identity))
            references.append(dict(url=a.base_url.rstrip('/') + public_path, filename=file.name, **identity))
        releases.append(dict(product_id='corecritical' if target == 'launcher' else 'mw3',
            game_id=None if target == 'launcher' else 'mw3', version=version,
            display_version=version + '-preview' if target == 'launcher' else version,
            numeric_version=version, sequence=manifest['sequence'], status='promoted', os='windows', architecture='x64',
            minimum_launcher_version=manifest['minimum_launcher_version'],
            contract=manifest.get('update_type', manifest.get('preparation_contract')),
            metadata=references[0], payload=references[1],
            release_notes=((launcher_notes or 'Updates inside Core Critical: signed online discovery, verified downloads with progress and resume, launcher restart, and separate runtime updates.')
                if target == 'launcher' else (runtime_notes or 'Cumulative precompiled native runtime with automatic additional chassis and skin support and the corrected Mech Lab preview camera. Existing audio, controller and performance repairs are retained.')),
            notes_url=None, dependencies=[]))
    # Verify existing package signatures using installed trusted public keys before signing discovery.
    verify = a.output / 'verify-inputs.ps1'
    verify.write_text('''param([string]$Trust,[string]$Launcher,[string]$Runtime)
$ErrorActionPreference='Stop'
$keys=(Get-Content -LiteralPath $Trust -Raw | ConvertFrom-Json).public_keys
foreach($file in @($Launcher,$Runtime)) {
 $e=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
 $pem=$keys.PSObject.Properties[$e.key_id].Value
 if(!$pem){throw 'Untrusted update key'}
 $rsa=[Security.Cryptography.RSA]::Create()
 try {
  $rsa.ImportFromPem($pem)
  if($rsa.KeySize -lt 3072 -or !$rsa.VerifyData([Convert]::FromBase64String($e.payload),[Convert]::FromBase64String($e.signature),[Security.Cryptography.HashAlgorithmName]::SHA256,[Security.Cryptography.RSASignaturePadding]::Pss)){throw 'Invalid update signature'}
 } finally {$rsa.Dispose()}
}
''', encoding='utf-8')
    subprocess.run(['pwsh', '-NoProfile', '-File', str(verify), '-Trust', str(a.trust_file), '-Launcher', str(a.launcher), '-Runtime', str(a.runtime)], check=True)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    document = dict(schema_version=1, type='corecritical-release-catalog-v1', channel='playtest', sequence=a.sequence,
        issued_utc=now.isoformat(), expires_utc=(now + timedelta(days=30)).isoformat(), releases=releases)
    manifest = a.output / 'catalog.manifest.json'
    manifest.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    envelope = a.output / 'catalog.json'
    signer = Path(__file__).resolve().parents[1] / 'mw3-remaster-launcher/sign_runtime_update.ps1'
    subprocess.run(['pwsh', '-NoProfile', '-File', str(signer), '-Manifest', str(manifest), '-SigningKey', str(a.signing_key), '-KeyId', a.key_id, '-OutputFile', str(envelope)], check=True)
    (a.output / 'publication.json').write_text(json.dumps(dict(objects=objects,
        catalog=dict(source=str(envelope.resolve()), key='online-updates/catalogs/playtest/catalog.json',
            archive_key=f'online-updates/catalogs/playtest/{a.sequence}.json', public_path='/channels/playtest/catalog.json', **pin(envelope))), indent=2) + '\n')
    print('Verified both signed package inputs and built signed catalog/publication inputs. No remote writes performed.')


if __name__ == '__main__':
    main()
