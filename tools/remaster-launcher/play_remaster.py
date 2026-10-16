"""Launch a local remaster profile using freshly published asset registrations."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'local/remaster/launcher.json'
REGISTRY=ROOT/'local/remaster/models.json'

def read_json(path):
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError) as exc:raise RuntimeError(f'Cannot read completed manifest {path}: {exc}') from exc

def plan(backend=None,original_models=False):
    config=read_json(CONFIG);backend=backend or config['backend']
    registry=read_json(REGISTRY)
    if registry['schema_version']!=1:raise RuntimeError('Unsupported model registry version')
    banks=read_json(ROOT/'local/work-ahead/texture-launcher-audit-v2/configured-banks.json')
    if not banks:raise RuntimeError('Texture pack manifest is empty')
    statuses={'runtime-ready'}
    if backend=='native' and config['native'].get('include_runtime_candidates',False):
        statuses.add('runtime-candidate')
    ready=[m for m in registry['models'] if m['status'] in statuses and m['backend']==backend]
    offline=[m['name'] for m in registry['models'] if m not in ready]
    if original_models:
        ready=[]
        offline=[]
    graphics=config['graphics']
    if backend=='d7vk':
        command=[sys.executable,str(ROOT/'mw3_launcher.py'),'--no-gui','--resolution','1920x1440 (1440p 4:3 Equivalent)','--aa','8x MSAA','--af','16x','--textures','ai']
        supported=True;limitations=['D7VK runs the original executable and original models; native model replacements are not compatible with this backend.']
    elif backend=='native':
        profile=config['native'];caps=profile['graphics_capabilities']
        executable=ROOT/profile['executable']
        if not executable.is_file():raise RuntimeError('Registered native executable is missing')
        if profile.get('executable_sha256'):
            with executable.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            if digest.lower()!=profile['executable_sha256'].lower():raise RuntimeError('Native executable changed; publish its completed validation/profile before launching')
        unknown=[m['name'] for m in ready if m.get('id') not in profile.get('model_ids',[])]
        if unknown:raise RuntimeError('Published models need a compatible native host: '+', '.join(unknown))
        mesh_versions=profile.get('mesh_payload_versions',[1,2])
        incompatible=[m['name'] for m in ready if m.get('required_native_mesh_format',1) not in mesh_versions]
        if incompatible:raise RuntimeError('Published models need a newer native mesh format: '+', '.join(incompatible))
        choices=profile.get('supported_graphics_values',{})
        supported=all(caps.get(k)==v or v in choices.get(k,[]) for k,v in graphics.items())
        command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/remaster-launcher/play_native.ps1'),'-Profile',str(CONFIG)]
        limitations=['Native renderer does not yet implement this complete requested graphics profile.'] if not supported else []
        if profile.get('cumulative_texture_banks') is not True:
            supported=False;limitations.append('Native cumulative texture-bank redirection has not been connected to this profile.')
    else:raise RuntimeError('Unknown renderer backend '+str(backend))
    for model in ready:
        for asset in model['required_files']:
            if not (ROOT/asset).is_file():raise RuntimeError(f"Published model {model['name']} is incomplete: {asset}")
    music=None
    if backend=='native' and config['native'].get('local_cd_audio',False):
        from local_music import configuration
        music=configuration(ROOT)
    return dict(backend=backend,graphics=graphics,supported=supported,texture_banks=len(banks),models=ready,offline_models=offline,limitations=limitations,command=command,music=music)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=['native','d7vk'])
    parser.add_argument('--original-models',action='store_true',help='Use original MW3 geometry while retaining registered texture banks and graphics settings')
    parser.add_argument('--check',action='store_true',help='Read current profiles/assets without launching or changing files')
    parser.add_argument('--prepare-only',action='store_true',help='Verify and prepare registered native assets without launching')
    parser.add_argument('--frames',type=int,default=0)
    parser.add_argument('--dump',type=int,default=0)
    args=parser.parse_args()
    try:
        p=plan(args.backend,args.original_models)
        g=p['graphics']
        aa='AA off' if g['aa']==1 else 'FXAA' if g['aa']=='fxaa' else str(g['aa'])+'-sample SSAA'
        af='AF off' if g['af']==1 else str(g['af'])+'x AF'
        aspect='43:18 ultrawide' if (g['width'],g['height'])==(3440,1440) else '4:3' if g['width']*3==g['height']*4 else 'native aspect'
        print(f"Play MW3Remaster requested profile: {g['width']}x{g['height']} ({aspect}), {aa}, {af}")
        print(f"Renderer: {p['backend']}; current texture pack: {p['texture_banks']} banks")
        if p['backend']=='native':print('Native build: '+read_json(CONFIG)['native']['executable'])
        if p['backend']=='native':print('Scenery draw distance: '+str(g.get('draw_distance',800))+' units')
        print('Runtime models: '+(', '.join(m['name'] for m in p['models']) or 'original game models'))
        if p['music']:print('Music: local MW3 tracks 01 and 02; original game music controls')
        candidates=[m['name'] for m in p['models'] if m['status']=='runtime-candidate']
        if candidates:print('Enabled test candidates (weapon/damage/LOD checks pending): '+', '.join(candidates))
        if p['offline_models']:print('Models awaiting compatible runtime integration: '+', '.join(p['offline_models']))
        for limitation in p['limitations']:print(limitation)
        if args.check:return 0
        if not p['supported']:raise RuntimeError('Requested graphics/assets are not supported by this native profile. No settings were silently disabled and no backend fallback was used.')
        # All launch paths share the same singleton game identity; preserve an existing session.
        if not args.prepare_only:
            result=subprocess.run(['powershell.exe','-NoProfile','-Command',"if(Get-Process -Name entry_commandline,Mech3 -ErrorAction SilentlyContinue){exit 2}"],capture_output=True)
            if result.returncode:raise RuntimeError('A game session is already running. Close it normally before launching Remaster.')
        environment=os.environ.copy()
        for key in list(environment):
            if key.startswith('MW34_'):environment.pop(key,None)
        if p['backend']=='native':
            from native_assets import prepare
            environment.update(prepare(ROOT,p['models']))
            if p['music']:
                from local_music import prepare_music
                environment.update(prepare_music(ROOT))
            for key,value in p['graphics'].items():environment['MW34_REMASTER_'+key.upper()]=str(value)
            p['command']+=['-Frames',str(args.frames),'-Dump',str(args.dump)]
        if args.prepare_only:return 0
        return subprocess.call(p['command'],cwd=ROOT,env=environment)
    except (RuntimeError,OSError,ValueError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
