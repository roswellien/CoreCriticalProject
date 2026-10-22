"""Prepare one installed runtime from explicit verified player files and source tools."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from translate import need, resolve, sha


def prepare(bundle, game, output, version, previous=None, inputs_path=None):
    need(re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}', version) is not None, 'Invalid native runtime version')
    config_path = bundle / 'preparation.json'
    config = json.loads(config_path.read_text())
    need(config['contract'] == 'mw3-source-runtime-v2', 'Unsupported source runtime preparation')
    need(not output.is_relative_to(game) and not game.is_relative_to(output), 'Original game and generated runtime must be separate')
    paths = {}
    if inputs_path:
        need(inputs_path.stat().st_size < 65536, 'Excessive original input map')
        paths = json.loads(inputs_path.read_text())
    originals = {}
    for name, pin in config['original_inputs'].items():
        path = Path(paths[name]).resolve() if name in paths else resolve(game, name)
        need(not path.is_relative_to(output), 'An original input cannot belong to the generated runtime')
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Original input missing or changed: '+name)
        originals[name] = path
    for name, pin in config['files'].items():
        path = resolve(bundle, name)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Preparation input changed: '+name)
    output.mkdir(parents=True, exist_ok=True)
    work = output / '.generation'
    identity = dict(config_sha256=sha(config_path), version=version,
        originals={name:config['original_inputs'][name]['sha256'] for name in originals})
    work.mkdir(exist_ok=True)
    owner = work / 'owner.json'
    if owner.exists():
        need(json.loads(owner.read_text()) == identity, 'Incomplete generation belongs to different preparation inputs')
    else:
        need(not any(work.iterdir()), 'Unrecognized native preparation work')
        owner.write_text(json.dumps(identity)+'\n')
    target_module = output / 'bin/MW3Translated.dll'
    target_entry = output / 'startup/entry.obj'
    unsigned_module_sha = config.get('unsigned_module_sha256', config['module_sha256'])

    def matches(path, digest):
        return path.is_file() and not path.is_symlink() and sha(path) == digest

    reused = False
    reused_previous = False
    completed = output / 'preparation.json'
    if completed.exists() and matches(target_module,config['module_sha256']) and matches(target_entry,config['entry_sha256']):
        receipt = json.loads(completed.read_text())
        reused = receipt.get('source_tools_sha256') == identity['config_sha256'] and receipt.get('version') == version and receipt.get('original_inputs') == identity['originals']
        if reused:
            reused_previous = bool(receipt.get('reused_previous_native_code',False))
            print('Reusing verified native code from the interrupted preparation.',flush=True)
    if previous and not reused:
        need(previous != output, 'Previous and new runtime directories must be separate')
        module = resolve(previous, 'bin/MW3Translated.dll')
        entry = resolve(previous, 'startup/entry.obj')
        recovered = None
        matched_module = matches(module, config['module_sha256']) or matches(module, unsigned_module_sha)
        if not matched_module and config.get('module_signature') and module.is_file():
            from module_signature import recover_unsigned
            recovered = recover_unsigned(module, config['module_signature'])
        if (matched_module or recovered is not None) and matches(entry, config['entry_sha256']):
            print('Reusing verified native code from your previous runtime.', flush=True)
            target_module.parent.mkdir(parents=True, exist_ok=True)
            target_entry.parent.mkdir(parents=True, exist_ok=True)
            if recovered is None:
                shutil.copyfile(module, target_module)
            else:
                target_module.write_bytes(recovered)
            shutil.copyfile(entry, target_entry)
            reused = True
            reused_previous = True
    if not reused:
        original_root = work / 'Original'
        for name, source in originals.items():
            target = resolve(original_root, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not matches(target, config['original_inputs'][name]['sha256']):
                shutil.copyfile(source, target)
                need(sha(target) == config['original_inputs'][name]['sha256'], 'Original input changed while copying')
        from original_codec import rebase, OUTPUT_SHA256
        codec = original_root / 'native-inputs/Ir50_32.base11000000.dll'
        if not matches(codec, OUTPUT_SHA256):
            codec.write_bytes(rebase((original_root / 'native-inputs/Ir50_32.dll').read_bytes()))
        tools = bundle / 'Tools'
        environment = dict(os.environ, PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
        for name in ('PYTHONHOME','PYTHONPATH','LIB','LIBPATH','INCLUDE','CL','_CL_','LINK','_LINK_'):
            environment.pop(name, None)

        def run(script, arguments):
            result = subprocess.run([sys.executable, '-B', '-u', str(bundle / script), *map(str, arguments)],
                env=environment, cwd=bundle)
            need(result.returncode == 0, 'Native preparation failed: '+script)

        for group in config['groups']:
            target = resolve(work, group['directory'])
            print('Preparing '+group['label']+' from your original files.', flush=True)
            arguments = ['--tools',tools,'--recipe',resolve(bundle,group['recipe']),
                '--game',original_root,'--output',target,'--jobs','2']
            if target.exists():
                arguments.append('--resume')
            run('translate.py', arguments)
        for step in config['startup']:
            target = resolve(work,step['directory'])
            receipt = target / 'generation.json'
            expected_outputs = {n:p for n,p in config['objects'].items() if n.startswith(step['directory']+'/')}
            if receipt.exists() and all(matches(resolve(work,n),p['sha256']) for n,p in expected_outputs.items()):
                continue
            # A failed startup attempt has no final receipt. Preserve its evidence
            # under an owned retry name before invoking the fresh-only generator.
            if target.exists():
                attempt = 1
                while target.with_name(target.name+'-failed-'+str(attempt)).exists():
                    attempt += 1
                need(target.parent == work, 'Startup retry path outside generation workspace')
                target.rename(target.with_name(target.name+'-failed-'+str(attempt)))
            arguments = ['--tools',tools,'--recipe',resolve(bundle,step['recipe']),'--output',target]
            if step['script'] != 'startup_small.py' or step.get('provider',False):
                arguments += ['--provider',original_root/'native-inputs/MSVCRT.DLL'] if step['script'] != 'startup_entry.py' else []
            if step['script'] in ('startup_entry.py','startup_control.py'):
                arguments += ['--game',original_root/'MECH3.EXE']
            run(step['script'],arguments)
        objects = work / 'link-inputs.json'
        objects.write_text(json.dumps(dict(contract='mw3-generated-link-inputs-v1',
            host_abi_sha256=sha(bundle/'abi/abi.json'),files=config['objects']))+'\n')
        from link_translated import link
        linked = work / 'Linked'
        if not matches(linked/'MW3Translated.dll',unsigned_module_sha):
            need(not linked.exists(), 'Failed final link retained; use its logs before retrying this preparation')
            link(tools,bundle/'abi/abi.json',objects,work,linked)
        need(matches(linked/'MW3Translated.dll',unsigned_module_sha), 'Generated native module differs from this release')
        target_module.parent.mkdir(parents=True, exist_ok=True)
        target_entry.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(linked/'MW3Translated.dll',target_module)
        shutil.copyfile(work/'Entry/candidate-O2.obj',target_entry)
    if config.get('module_signature') and matches(target_module, unsigned_module_sha):
        from module_signature import apply_signature
        signature = config['module_signature']
        apply_signature(target_module, signature, resolve(bundle, signature['certificate_path']), work)
    need(matches(target_entry,config['entry_sha256']) and matches(target_module,config['module_sha256']), 'Prepared native output identity mismatch')
    for name,pin in config['runtime_files'].items():
        source = resolve(bundle/'RuntimeBase',name)
        need(sha(source) == pin['sha256'], 'Authored runtime payload changed: '+name)
        target = resolve(output,name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source,target)
    for name,path in originals.items():
        need(sha(path) == config['original_inputs'][name]['sha256'], 'Original input changed during preparation')
    # Delete only this producer's verified, owned scratch subtree after success.
    need(work.resolve().parent == output.resolve() and work.name == '.generation' and json.loads(owner.read_text()) == identity,
        'Preparation workspace ownership changed')
    shutil.rmtree(work)
    provenance = dict(contract=config['contract'],version=version,original_inputs=identity['originals'],
        source_tools_sha256=identity['config_sha256'],reused_previous_native_code=reused_previous,original_code_executed=False)
    (output/'preparation.json').write_text(json.dumps(provenance,indent=2)+'\n')
    files = {}
    for path in output.rglob('*'):
        if path.is_file() and path.name != 'runtime.json':
            files[path.relative_to(output).as_posix()] = dict(bytes=path.stat().st_size,sha256=sha(path))
    manifest = dict(schema_version=1,profile='profile.json',coordinator='coordinator/play_remaster.py',python='python/python.exe',
        native_modules=['bin/MW3Translated.dll'],files=files)
    (output/'runtime.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Native runtime preparation complete.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game','output','version'):
        parser.add_argument('--'+name,required=True,type=str if name=='version' else Path)
    parser.add_argument('--previous',type=Path)
    parser.add_argument('--original-inputs',type=Path)
    args = parser.parse_args()
    prepare(Path(__file__).resolve().parent,args.game.resolve(),args.output.resolve(),args.version,
        args.previous.resolve() if args.previous else None,args.original_inputs)
