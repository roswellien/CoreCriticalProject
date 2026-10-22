"""Link player-generated native code against the project host, without an SDK."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from translate import need, resolve, sha


def link(tools, abi_path, object_manifest, object_root, output):
    need(not output.exists(), 'Use a fresh translated-runtime output directory')
    abi = json.loads(abi_path.read_text())
    objects = json.loads(object_manifest.read_text())
    need(abi['contract'] == 'mw3-native-host-abi-v1' and objects['contract'] == 'mw3-generated-link-inputs-v1', 'Unsupported native link contract')
    need(objects['host_abi_sha256'] == sha(abi_path), 'Generated code belongs to a different native host ABI')
    need(abi['object_count'] == len(objects['files']) == 37348, 'Complete native object set required')
    manifest = json.loads((tools / 'tools.json').read_text())
    for name, pin in manifest['files'].items():
        path = resolve(tools, name)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Native linker tool changed: '+name)
    inputs = {}
    for name, pin in abi['files'].items():
        path = resolve(abi_path.parent, name)
        need(sha(path) == pin['sha256'] and path.stat().st_size == pin['bytes'], 'Native ABI input changed: '+name)
        inputs[name] = path
    need(set(inputs) == {'authored-host.lib', 'translated.def'}, 'Unexpected native ABI payload')
    paths = []
    for index, (name, pin) in enumerate(objects['files'].items(), 1):
        need(name.endswith('.obj'), 'Unexpected generated input type')
        path = resolve(object_root, name)
        need(sha(path) == pin['sha256'], 'Generated native object missing or changed: '+name)
        paths.append(path)
        if index % 5000 == 0:
            print('Verified native link inputs: '+str(index)+'/'+str(len(objects['files'])), flush=True)
    output.mkdir(parents=True)
    target = output / 'MW3Translated.dll'
    arguments = [*paths, inputs['authored-host.lib'], '/nologo','/machine:x64','/DLL','/NOENTRY','/OPT:REF','/OPT:ICF',
        '/NODEFAULTLIB','/Brepro','/timestamp:0','/def:'+str(inputs['translated.def']),
        '/out:'+str(target),'/implib:'+str(output / 'translated.lib')]
    need(all(not any(c in str(p) for c in '\r\n"') for p in arguments), 'Invalid native linker argument')
    response = output / 'link.rsp'
    response.write_text('\n'.join('"'+str(p)+'"' for p in arguments)+'\n')
    # The player link deliberately receives no installed SDK environment or
    # implicit CRT library search path. Every external service is host owned.
    environment = {k:v for k,v in os.environ.items() if k.upper() not in ('LIB','LIBPATH','INCLUDE','CL','_CL_','LINK','_LINK_')}
    environment['PATH'] = str(Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32')
    result = subprocess.run([str(tools / 'llvm/lld-link.exe'), '@'+str(response)], cwd=output,
        env=environment, capture_output=True)
    (output / 'link.log').write_bytes(result.stdout+result.stderr)
    need(result.returncode == 0, 'Native code link failed; see link.log')
    for name, pin in objects['files'].items():
        need(sha(resolve(object_root, name)) == pin['sha256'], 'Generated input changed during native link')
    receipt = dict(contract='mw3-generated-native-module-v1', dll_sha256=sha(target), host_sha256=abi['host_sha256'],
        host_abi_sha256=sha(abi_path), object_manifest_sha256=sha(object_manifest), sdk_libraries=[],
        original_code_executed=False)
    (output / 'generation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('tools', 'abi', 'objects', 'object-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(link(args.tools.resolve(), args.abi.resolve(), args.objects.resolve(), args.object_root.resolve(), args.output.resolve()))
