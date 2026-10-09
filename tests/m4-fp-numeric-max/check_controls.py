"""Causal raw observers and real publisher/identity/replay admission controls."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'tools/m4-fp-numeric-max'))
from analyze import Raw,compare,bind
from model import checks
def main():
 out=Path(sys.argv[1]).resolve();assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists();out.mkdir(parents=True)
 original=ROOT/'reports/m4-fp-numeric-max/original-r5-normal-windows';build=ROOT/'reports/m4-fp-numeric-max/repaired-r2';packpath=ROOT/'reports/m4-fp-numeric-max/recovery-r1/pages.bin';pack=packpath.read_bytes();observations=[]
 o=Raw(original/'default.bin',b'MW4NMO01',35764)
 # Each mutation changes a literal captured byte; original streams stay readonly.
 original_mutations=[('before_CPU',40),('after_CPU',80),('initial_SW',122),('physical_FTW',636),('initial_ST1',168),('dead_ST7',776),('legacy_FIP',2208),('legacy_FDP',2216),('host_FP',1656),('host_ENV',2252),('IAT_page',2280+0x4fc),('provider_data',2280+4096+4),('output_store',18664+8192+0x368),('stack_frame',18664+12288+0x800),('return_CONTEXT_GPR',35048+176),('return_CONTEXT_EIP',35048+184),('return_CONTEXT_FTW',35048+208),('return_CONTEXT_ST0',35048+236),('return_CONTEXT_live_ST1',35048+252)]
 native_mutations=[('full_State_protected',39268+2000),('State_segment_base',39268+2168),('State_GPR_high',39268+2220),('State_XMM_padding',39268+48),('State_live_ST1',39268+2502),('State_legacy_FIP',39268+2776),('State_physical_tag',39268+2772),('initial_State',35764+1),('checkpoint_State',43352+2001),('checkpoint_metadata',43352+2776),('checkpoint_Tag',43352+2772),('checkpoint_CPU',42772+16),('checkpoint_ST0',42812+32),('event_address',46888),('event_value',46892),('event_width',46896),('event_operation',46900),('event_order',46904),('event_count',46856),('read_count',46860),('route_return',47240+4),('route_RET_cleanup',47240+8),('route_complete',47240+12),('route_provider_stack',47240+96+16+16),('route_checkpoint_PC',47240+96+56+36),('counterfeit_CONTEXT',35048),('failure_flag',46884)]
 for level in ('O0','O2'):
  n=Raw(build/('default-'+level+'.bin'),b'MW4NMN01',47432);a=o.record(145);b=n.record(145);leaf=o.record(144);assert not compare(a,b) and not checks(a,b,leaf,pack)
  for side,mutations in (('original',original_mutations),('native',native_mutations)):
   for name,offset in mutations:
    aa=bytearray(a);bb=bytearray(b);(aa if side=='original' else bb)[offset]^=1
    rejected=False;reason=[]
    try:reason=compare(aa,bb)+checks(aa,bb,leaf,pack);rejected=bool(reason)
    except (AssertionError,ValueError,IndexError) as e:rejected=True;reason=[type(e).__name__+': '+str(e)]
    assert rejected,(side,name);observations.append({'level':level,'side':side,'name':name,'offset':offset,'rejected':True,'reason':reason})
  # Causally remove only the previous provider tag/data evidence. This breaks
  # the actual leaf-to-connected-return comparison without touching numerics.
  altered=bytearray(leaf);altered[664]^=1;assert checks(a,b,altered,pack);observations.append({'level':level,'side':'paired_leaf','name':'real_provider_return_dependency','rejected':True})
  for index in (0,1,144,145,288,289):assert not compare(o.record(index),n.record(index)) and not checks(o.record(index),n.record(index),o.record(index-1) if index%2 else None,pack);observations.append({'level':level,'positive_record':index,'passed':True})
 commands=[]
 def run(name,args,exitcode,phrase=None):
  r=subprocess.run(list(map(str,args)),capture_output=True,timeout=60);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);assert r.returncode==exitcode,(name,r.returncode,r.stderr)
  if phrase:assert phrase.encode() in r.stderr,(name,r.stderr)
  commands.append({'name':name,'command':list(map(str,args)),'exit_code':r.returncode})
 game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'
 for name,path in (('game',game),('provider',provider),('pack',packpath)):
  data=bytearray(path.read_bytes());data[-1]^=1;(out/('wrong-'+name+'.bin')).write_bytes(data)
 workers=[('original',ROOT/'reports/m4-fp-numeric-max/original-build-r5/build/Release/mw34_numeric_reference.exe')]+[(level,build/('build-'+level)/'mw34_numeric_native.exe') for level in ('O0','O2')]
 for label,worker in workers:
  run(label+'-publication',[worker,'--check-publication',out/(label+'-publication')],0)
  for kind,phrase in (('game','Exact game identity rejected'),('provider','Exact provider identity rejected'),('pack','Exact pack identity rejected')):
   output=out/(label+'-rejected-'+kind+'.bin');args=[worker,out/'wrong-pack.bin' if kind=='pack' else packpath,out/'wrong-game.bin' if kind=='game' else game,out/'wrong-provider.bin' if kind=='provider' else provider,output]
   run(label+'-'+kind,args,1,phrase);assert not output.exists() and not list(out.glob(output.name+'.numeric-stage-*'))
 # Entirely existing output trees must be rejected before any snapshot/extract
 # or compile, including markers in each of its child build directories.
 pwsh=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe');recipe=ROOT/'tools/m4-fp-numeric-max/build.ps1';recipe_controls=[]
 for mode in ('partial-report','build-x86','build-O0','build-O2'):
  directory=out/('existing-'+mode);marker=directory/'marker.bin' if mode=='partial-report' else directory/mode/'marker.bin';marker.parent.mkdir(parents=True);sentinel=b'NumericMaxEvidence\x00\xff\x80';marker.write_bytes(sentinel)
  before={str(p.relative_to(directory)):bind(p) for p in directory.rglob('*') if p.is_file()}
  run('recipe-'+mode,[pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',recipe,'-OutputDirectory',directory,'-Repair'],1,'Existing report directory rejected before mutation')
  after={str(p.relative_to(directory)):bind(p) for p in directory.rglob('*') if p.is_file()};assert before==after and marker.read_bytes()==sentinel;recipe_controls.append({'mode':mode,'before':before,'after':after,'unchanged':True})
 report={'passed':True,'observer_mutations':observations,'observer_negative_count':sum(x.get('rejected',False) for x in observations),'observer_positive_count':sum(x.get('passed',False) for x in observations),'actual_commands':commands,'actual_identity_denials':9,'actual_publication_checks':6,'recipe_no_mutation_controls':recipe_controls,'source':bind(__file__),'observer_sources':[bind(ROOT/'tools/m4-fp-numeric-max'/p) for p in ('analyze.py','model.py')],'scope':'Actual isolated workers; fresh sequential private ordinary directories. Production concurrent/reparse publication and generic live-game debugging unadmitted.'}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'negative':report['observer_negative_count'],'positive':report['observer_positive_count'],'identity':9,'publisher':6,'recipe':4}))
if __name__=='__main__':main()
