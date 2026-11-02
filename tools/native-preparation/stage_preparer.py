"""Stage the private source-tool preparer trial; never includes translated game code."""
import argparse
import json
from pathlib import Path
import shutil

from translate import need, sha


def stage(root, trial, tools, template, bootstrap, original_root, output, *, host=None, module=None, abi=None, link_plan=None, signature=None):
    need(not output.exists(), 'Use a fresh source preparer directory')
    output.mkdir(parents=True)

    def copy(source, relative):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source,target)
        need(sha(source) == sha(target), 'Source changed during preparer staging')

    copy(bootstrap,'NativePreparer.exe')
    for name in ('prepare_runtime','translate','link_translated','original_codec','startup_entry','startup_small','startup_control','module_signature'):
        copy(root/f'tools/native-preparation/{name}.py',name+'.py')
    for file in tools.rglob('*'):
        if file.is_file() and '__pycache__' not in file.parts:
            copy(file,Path('Tools')/file.relative_to(tools))
    abi = abi or root/'local/native-preparation-20261022-r1/abi'
    for name in ('abi.json','authored-host.lib','translated.def'):
        copy(abi/name,'abi/'+name)
    recipe_paths = {
        'bodies':'r3/body-recipe.json','heap':'r9/heap-recipe.json','mainargs':'r10/mainargs-recipe.json',
        'initterm':'r11/initterm-recipe-v2.json','matherr':'r12/matherr-recipe.json','entry':'r8/entry-recipe.json',
        'capture':'r13/capture-recipe.json','commandline':'r13/cmd-recipe.json','control':'r14/control-recipe.json'}
    for name,relative in recipe_paths.items():
        copy(root/('local/native-preparation-20261021-'+relative),'recipes/'+name+'.json')
    runtime_manifest = json.loads((template/'runtime.json').read_text())
    excluded = {'profile.json','metadata/source-snapshot.json','startup/entry.obj','bin/entry_commandline.exe',
        'assets/resource-000/preview-registry.txt'}
    for name in runtime_manifest['files']:
        if name not in excluded:
            copy(template/name,Path('RuntimeBase')/name)
    host = host or trial/'SplitHost-r1/entry_commandline.exe'
    module = module or trial/'SdkFree-r1/MW3Translated.dll'
    copy(host,'RuntimeBase/bin/entry_commandline.exe')
    # Always stage current authored coordinators, including the new module pin.
    for file in (output/'RuntimeBase/coordinator').glob('*.py'):
        source = root/'tools/remaster-launcher'/file.name
        if source.is_file():
            copy(source,Path('RuntimeBase/coordinator')/file.name)
    # Added after the original runtime template; required by current coordinator.
    copy(root/'tools/remaster-launcher/startup_cache.py','RuntimeBase/coordinator/startup_cache.py')
    copy(root/'tools/remaster-launcher/surface_materials.py','RuntimeBase/coordinator/surface_materials.py')
    profile = json.loads((template/'profile.json').read_text())
    native = profile['native']
    host_sha = sha(host)
    module_sha = sha(module)
    native['executable_sha256'] = host_sha
    native['translated_module'] = '@runtime/bin/MW3Translated.dll'
    native['translated_module_sha256'] = module_sha
    native['verify_source_snapshot'] = False
    native['runtime_environment'].pop('MW34_REG_OVERLAY',None)
    (output/'RuntimeBase/profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (output/'RuntimeBase/metadata').mkdir(parents=True,exist_ok=True)
    (output/'RuntimeBase/metadata/source-snapshot.json').write_text(json.dumps(dict(
        contract='mw3-authored-host-with-local-translations-v1',executable_sha256=host_sha,
        translated_module_sha256=module_sha,original_code_in_host=False),indent=2)+'\n')
    names=['MECH3.EXE','MECH3MSG.DLL',*('native-inputs/'+n for n in ('MFC42.DLL','MSVCRT.DLL','MSVCP50.DLL','Ir50_32.dll'))]
    originals={n:dict(bytes=(original_root/n).stat().st_size,sha256=sha(original_root/n)) for n in names}
    plan=json.loads((link_plan or root/'local/native-preparation-20261021-r14/local-link-plan.json').read_text())
    prefixes=[(trial/'Bodies','Bodies'),
        (root/'local/native-preparation-20261021-r9/Heap','Heap'),
        (root/'local/native-preparation-20261021-r10/Mainargs','Mainargs'),
        (root/'local/native-preparation-20261021-r11/InitTerm-v2','InitTerm'),
        (root/'local/native-preparation-20261021-r12/Matherr','Matherr'),
        (root/'local/native-preparation-20261021-r8/entry','Entry'),
        (root/'local/native-preparation-20261021-r13/Cmd','Commandline'),
        (root/'local/native-preparation-20261021-r13/Capture','Capture'),
        (root/'local/native-preparation-20261021-r14/Control','Control')]
    objects={}
    for item in plan['inputs']:
        if item['kind']!='generated-from-original':continue
        source=Path(item['path'])
        matches=[(prefix,label) for prefix,label in prefixes if source.is_relative_to(prefix)]
        need(len(matches)==1,'Unknown generated component origin')
        prefix,label=matches[0]
        objects[label+'/'+source.relative_to(prefix).as_posix()]=dict(sha256=item['sha256'])
    groups=[dict(label=label,directory=directory,recipe='recipes/'+name+'.json') for label,directory,name in
        [('game code','Bodies','bodies'),('heap initialization','Heap','heap'),('arguments','Mainargs','mainargs'),
         ('initializer traversal','InitTerm','initterm'),('math registration','Matherr','matherr')]]
    startup=[dict(directory=directory,script=script,recipe='recipes/'+name+'.json',provider=provider) for directory,script,name,provider in
        [('Entry','startup_entry.py','entry',False),('Capture','startup_small.py','capture',False),
         ('Commandline','startup_small.py','commandline',True),('Control','startup_control.py','control',True)]]
    signature_data = None
    if signature:
        signature_data = json.loads(signature.read_text())
        need(signature_data['signed_sha256'] == module_sha, 'Module signature belongs to another release')
        copy(signature.parent/'module-certificates.bin','signatures/module-certificates.bin')
        signature_data['certificate_path'] = 'signatures/module-certificates.bin'
    runtime_files={p.relative_to(output/'RuntimeBase').as_posix():dict(bytes=p.stat().st_size,sha256=sha(p))
        for p in (output/'RuntimeBase').rglob('*') if p.is_file()}
    files={p.relative_to(output).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in output.rglob('*') if p.is_file()}
    config=dict(contract='mw3-source-runtime-v2',purpose='private-source-preparer-trial',original_inputs=originals,
        files=files,runtime_files=runtime_files,groups=groups,startup=startup,objects=objects,module_sha256=module_sha,
        entry_sha256=sha(root/'local/native-preparation-20261021-r8/entry/candidate-O2.obj'))
    if signature_data:
        config.update(module_signature=signature_data,unsigned_module_sha256=signature_data['unsigned_sha256'])
    (output/'preparation.json').write_text(json.dumps(config,indent=2)+'\n')
    # Refuse accidental proprietary input/output inclusion in this source kit.
    excluded_hashes={p['sha256'] for p in originals.values()} | {p['sha256'] for p in objects.values()} | {module_sha, config.get('unsigned_module_sha256',module_sha)}
    need(not any(pin['sha256'] in excluded_hashes for pin in files.values()), 'A source kit contains original or translated game material')
    return dict(files=len(files)+1,generated_game_files_included=0,bootstrap_sha256=sha(output/'NativePreparer.exe'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','trial','tools','template','bootstrap','originals','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('host','module','abi','link-plan','signature'):
        parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    print(stage(*(getattr(args,n).resolve() for n in ('root','trial','tools','template','bootstrap','originals','output')),
        **{n:getattr(args,n).resolve() if getattr(args,n) else None for n in ('host','module','abi','signature')},
        link_plan=args.link_plan.resolve() if args.link_plan else None))
