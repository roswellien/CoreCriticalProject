"""Package signed source tools, excluding original images and generated game code."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

from translate import need, resolve, sha


def package(source, output, powershell, signer, private_key, public_key, key_id, version, sequence):
    need(not output.exists(), 'Use a fresh source update output directory')
    config = json.loads((source/'preparation.json').read_text())
    need(config['contract'] == 'mw3-source-runtime-v2', 'Source-only preparer required')
    expected = dict(config['files'])
    expected['preparation.json'] = dict(bytes=(source/'preparation.json').stat().st_size,sha256=sha(source/'preparation.json'))
    observed = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    need(observed == set(expected), 'Unexpected or missing source toolkit file')
    forbidden = {p['sha256'] for p in config['original_inputs'].values()} | {p['sha256'] for p in config['objects'].values()} | {config['module_sha256'],config.get('unsigned_module_sha256',config['module_sha256'])}
    for name,pin in expected.items():
        path = resolve(source,name)
        need(sha(path) == pin['sha256'] and path.stat().st_size == pin['bytes'] and pin['sha256'] not in forbidden,
             'Changed or non-source toolkit input: '+name)
    output.mkdir(parents=True)
    preparation = output/'Preparation'
    preparation.mkdir()
    archive = preparation/'initial.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as target:
        for name in sorted(expected):
            target.write(resolve(source,name),name)
    manifest = dict(schema_version=1,version=version,sequence=sequence,minimum_launcher_version='1.0.17',
        preparation_contract='mw3-source-runtime-v2',package_url='',package_bytes=archive.stat().st_size,
        package_sha256=sha(archive),preparer='NativePreparer.exe',files=expected,original_inputs=config['original_inputs'])
    unsigned = output/'manifest.json'
    unsigned.write_text(json.dumps(manifest,separators=(',',':'))+'\n')
    result = subprocess.run([str(powershell),'-NoProfile','-File',str(signer),'--Manifest',str(unsigned),
        '--SigningKey',str(private_key),'--KeyId',key_id,'--OutputFile',str(preparation/'initial.mw3update')],capture_output=True)
    need(result.returncode == 0, 'Source package signing failed: '+result.stderr.decode(errors='replace')[-1000:])
    (output/'update-trust.json').write_text(json.dumps(dict(feed_url='',public_keys={key_id:public_key.read_text()}),indent=2)+'\n')
    receipt = dict(kind='private-source-preparation-preview',version=version,sequence=sequence,files=len(expected),
        source_package_bytes=archive.stat().st_size,source_package_sha256=sha(archive),original_images_included=0,
        generated_game_modules_included=0,public_feed_configured=False,clean_windows_verified=False)
    (output/'package.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','powershell','signer','private-key','public-key'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('key-id','version'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--sequence',type=int,required=True)
    a=parser.parse_args()
    print(package(a.source.resolve(),a.output.resolve(),a.powershell.resolve(),a.signer.resolve(),a.private_key.resolve(),
        a.public_key.resolve(),a.key_id,a.version,a.sequence))
