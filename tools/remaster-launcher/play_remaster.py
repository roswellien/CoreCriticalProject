"""Launch a local remaster profile using freshly published asset registrations."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'local/remaster/launcher.json'
REGISTRY=ROOT/'local/remaster/models.json'

def read_json(path):
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError) as exc:raise RuntimeError(f'Cannot read completed manifest {path}: {exc}') from exc

def plan(backend=None,original_models=False,*,config_path=None,registry_path=None):
    selected_config=(Path(config_path) if config_path is not None else CONFIG).resolve()
    selected_registry=(Path(registry_path) if registry_path is not None else REGISTRY).resolve()
    config=read_json(selected_config);backend=backend or config['backend']
    registry=read_json(selected_registry)
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
    graphics=dict(config['graphics'])
    # Settings UI persists the named off choice; the native sampler contract
    # uses one raster sample for disabled AA.
    if graphics.get('aa')=='off':graphics['aa']=1
    if backend=='d7vk':
        command=[sys.executable,str(ROOT/'mw3_launcher.py'),'--no-gui','--resolution','1920x1440 (1440p 4:3 Equivalent)','--aa','8x MSAA','--af','16x','--textures','ai']
        supported=True;limitations=['D7VK runs the original executable and original models; native model replacements are not compatible with this backend.']
    elif backend=='native':
        profile=config['native'];caps=profile['graphics_capabilities']
        detail_env=profile.get('runtime_environment',{})
        detail_roles=[]
        if detail_env.get('MW34_WATER_DETAIL')=='1':detail_roles+=['water','surf']
        if detail_env.get('MW34_CLOUD_DETAIL')=='1':detail_roles+=['cloud']
        if detail_roles and 1 not in profile.get('surface_detail_versions',[]):
            raise RuntimeError('Sky/water detail requires a validated compatible native host')
        for role in detail_roles:
            detail_path=ROOT/detail_env.get('MW34_'+role.upper()+'_NORMALS','')
            pin=profile.get('surface_detail',{}).get('packs',{}).get(role,{})
            if not detail_path.is_file() or not 0<detail_path.stat().st_size<=16*1024*1024:
                raise RuntimeError('Missing or excessive surface detail pack: '+role)
            with detail_path.open('rb') as stream:detail_hash=hashlib.file_digest(stream,'sha256').hexdigest()
            if detail_hash!=pin.get('sha256'):raise RuntimeError('Surface detail pack changed: '+role)
        world_normals=profile.get('runtime_environment',{}).get('MW34_WORLD_NORMALS')
        if world_normals:
            if 1 not in profile.get('world_normal_page_versions',[]):
                raise RuntimeError('World normal pages require a validated compatible native host')
            if not (ROOT/world_normals).is_file():raise RuntimeError('Configured world-normal manifest is missing')
        authored_normals=profile.get('runtime_environment',{}).get('MW34_SURFACE_NORMALS')
        if authored_normals:
            authored_path=ROOT/authored_normals
            if not authored_path.is_file():raise RuntimeError('Configured authored-normal catalog is missing')
            with authored_path.open('rb') as stream:authored_magic=stream.read(8)
            if authored_magic==b'MW34SNA1' and 1 not in profile.get('authored_normal_catalog_versions',[]):
                raise RuntimeError('Paged authored normals require a validated compatible native host')
            if authored_magic not in (b'BWSNR2\0\0',b'MW34SNA1'):
                raise RuntimeError('Unsupported authored-normal catalog')
        if any('normal_textures' in m for m in ready) and 2 not in profile.get('normal_map_formats',[]):
            raise RuntimeError('Registered material normals require a validated BWNRM2 native host')
        executable=ROOT/profile['executable']
        if profile.get('runtime_environment',{}).get('MW34_EFFECT_LIGHTS')=='1':
            if 1 not in profile.get('effect_lighting_versions',[]):
                raise RuntimeError('Effect lighting requires a validated compatible native host')
            catalog=ROOT/profile.get('runtime_environment',{}).get('MW34_EFFECT_LIGHT_CATALOG','')
            pin=profile.get('effect_lighting',{})
            if not catalog.is_file() or pin.get('catalog')!=str(catalog):
                raise RuntimeError('Configured effect-light catalog is missing or unregistered')
            data=catalog.read_bytes()
            if len(data)<12 or data[:8]!=b'MWFX1\0\0\0':raise RuntimeError('Invalid effect-light catalog')
            count=int.from_bytes(data[8:12],'little')
            if not 0<count<=8192 or len(data)!=12+48*count:raise RuntimeError('Invalid effect-light catalog size')
            if hashlib.sha256(data).hexdigest()!=pin.get('sha256'):raise RuntimeError('Effect-light catalog changed; publish its matching preview metadata')
        if not executable.is_file():raise RuntimeError('Registered native executable is missing')
        if profile.get('executable_sha256'):
            with executable.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            if digest.lower()!=profile['executable_sha256'].lower():raise RuntimeError('Native executable changed; publish its completed validation/profile before launching')
        if profile.get('verify_source_snapshot'):
            snapshot=read_json(ROOT/profile['source_snapshot'])
            if snapshot.get('executable_sha256','').lower()!=profile.get('executable_sha256','').lower():raise RuntimeError('Native source snapshot does not match the selected executable; publish its matching build metadata')
            if sorted(snapshot.get('model_ids',[]))!=sorted(profile.get('model_ids',[])):raise RuntimeError('Native source snapshot and launcher disagree on supported models')
            if snapshot.get('skin_ids',{})!=profile.get('skin_ids',{}):raise RuntimeError('Native source snapshot and launcher disagree on supported model skins')
            if snapshot.get('normal_map_formats',[])!=profile.get('normal_map_formats',[]):raise RuntimeError('Native source snapshot and launcher disagree on normal-map support')
            if snapshot.get('world_normal_page_versions',[])!=profile.get('world_normal_page_versions',[]):raise RuntimeError('Native source snapshot and launcher disagree on world-normal page support')
            if snapshot.get('authored_normal_catalog_versions',[])!=profile.get('authored_normal_catalog_versions',[]):raise RuntimeError('Native source snapshot and launcher disagree on authored-normal catalog support')
            if snapshot.get('surface_detail_versions',[])!=profile.get('surface_detail_versions',[]):raise RuntimeError('Native source snapshot and launcher disagree on sky/water detail support')
        unknown=[m['name'] for m in ready if m.get('id') not in profile.get('model_ids',[])]
        if unknown:raise RuntimeError('Published models need a compatible native host: '+', '.join(unknown))
        unsupported_skins=[m['name']+'/'+skin['id'] for m in ready for skin in m.get('skins',[]) if skin['id'] not in profile.get('skin_ids',{}).get(m['id'],[])]
        if unsupported_skins:raise RuntimeError('Published skins need a compatible native host: '+', '.join(unsupported_skins))
        mesh_versions=profile.get('mesh_payload_versions',[1,2])
        incompatible=[m['name'] for m in ready if m.get('required_native_mesh_format',1) not in mesh_versions]
        if incompatible:raise RuntimeError('Published models need a newer native mesh format: '+', '.join(incompatible))
        choices=profile.get('supported_graphics_values',{})
        supported=all(caps.get(k)==v or v in choices.get(k,[]) for k,v in graphics.items())
        command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/remaster-launcher/play_native.ps1'),'-Profile',str(selected_config)]
        limitations=['Native renderer does not yet implement this complete requested graphics profile.'] if not supported else []
        if profile.get('cumulative_texture_banks') is not True:
            supported=False;limitations.append('Native cumulative texture-bank redirection has not been connected to this profile.')
    else:raise RuntimeError('Unknown renderer backend '+str(backend))
    for model in ready:
        for asset in model['required_files']+[path for path in model.get('normal_textures',{}).values() if path is not None]:
            if not (ROOT/asset).is_file():raise RuntimeError(f"Published model {model['name']} is incomplete: {asset}")
    music=None
    if backend=='native' and config['native'].get('local_cd_audio',False):
        from local_music import configuration
        music=configuration(ROOT)
    asset_output=config.get('native',{}).get('prepared_asset_directory') if backend=='native' else None
    return dict(backend=backend,graphics=graphics,supported=supported,texture_banks=len(banks),models=ready,offline_models=offline,limitations=limitations,command=command,music=music,asset_output=asset_output)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=['native','d7vk'])
    parser.add_argument('--original-models',action='store_true',help='Use original MW3 geometry while retaining registered texture banks and graphics settings')
    parser.add_argument('--check',action='store_true',help='Read current profiles/assets without launching or changing files')
    parser.add_argument('--prepare-only',action='store_true',help='Verify and prepare registered native assets without launching')
    parser.add_argument('--profile',type=Path,default=CONFIG,help='Completed native profile to check or launch')
    parser.add_argument('--registry',type=Path,default=REGISTRY,help='Completed model registry for this profile')
    parser.add_argument('--asset-output',type=Path,help='Separate prepared-asset directory for an integration candidate')
    parser.add_argument('--lighting-preset',help='Registered map lighting preset, e.g. sunrise, sunset or midday')
    parser.add_argument('--frames',type=int,default=0)
    parser.add_argument('--dump',type=int,default=0)
    args=parser.parse_args()
    try:
        p=plan(args.backend,args.original_models,config_path=args.profile,registry_path=args.registry)
        lighting_config=read_json(args.profile).get('native',{}).get('sun_preset')
        if args.lighting_preset and p['backend']!='native':raise RuntimeError('Lighting presets require the native renderer')
        if p['backend']=='native' and (lighting_config or args.lighting_preset):
            resolved=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/remaster-launcher/resolve_sun_preset.ps1'),'-Profile',str(args.profile.resolve()),'-Preset',args.lighting_preset or lighting_config['default']],capture_output=True,text=True)
            if resolved.returncode:raise RuntimeError(resolved.stderr.strip())
            lighting=json.loads(resolved.stdout)
            print('Lighting preset: '+lighting['map']+' / '+lighting['preset'])
            p['command']+=['-LightingPreset',lighting['preset']]
        g=p['graphics']
        aa='AA off' if g['aa']==1 else 'FXAA' if g['aa']=='fxaa' else str(g['aa'])+'-sample SSAA'
        af='AF off' if g['af']==1 else str(g['af'])+'x AF'
        aspect='43:18 ultrawide' if (g['width'],g['height'])==(3440,1440) else '4:3' if g['width']*3==g['height']*4 else 'native aspect'
        print(f"Play MW3Remaster requested profile: {g['width']}x{g['height']} ({aspect}), {aa}, {af}")
        print(f"Renderer: {p['backend']}; current texture pack: {p['texture_banks']} banks")
        if p['backend']=='native':print('Native build: '+read_json(args.profile)['native']['executable'])
        if p['backend']=='native':print('Scenery draw distance: '+str(g.get('draw_distance',800))+' units')
        if p['backend']=='native' and g.get('fog_distance',0):print('Linear fog distance: '+str(g['fog_distance'])+' units')
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
            environment.update(prepare(ROOT,p['models'],output=args.asset_output or p['asset_output']))
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
