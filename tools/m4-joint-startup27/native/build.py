"""Fresh native candidate with one outer host boundary before large frame."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-joint-startup27'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community');CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 bpath=ROOT/'reports/m4-joint27-startup/build-only-r1/build.json';assert sha(bpath)=='695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5';b=json.loads(bpath.read_text());assert b['passed']
 sources=dict(b['sources']);sources.update({str(p.resolve()):sha(p)for p in Path(__file__).parent.parent.rglob('*')if p.is_file()and p.suffix in('.cpp','.txt','.py','.ps1','.hpp','.asm')})
 for p,h in b['sources'].items()|b['tools'].items()|b['artifacts'].items():assert sha(p)==h,(p,h)
 for p,h in json.loads((BASE/'boundary-derivation-r1/pins.json').read_text())['files'].items():assert sha(p)==h,(p,h)
 commands=[];failure=None;workers={};tools={};derived=ROOT/'reports/m4-joint27-startup/derived-r1'
 def run(args,log):
  args=list(map(str,args));r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240);(out/log).write_bytes(r.stdout+r.stderr);tools[args[0]]=sha(args[0]);commands.append({'arguments':args,'exit_code':r.returncode,'log':log});print(json.dumps({'log':log,'exit_code':r.returncode}),flush=True);assert r.returncode==0,r.stderr.decode(errors='replace')[-6000:]
 try:
  os.environ['TEMP']=os.environ['TMP']=str(out)
  for level in ('O0','O2'):
   tree=out/f'build-{level}';flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid offsetof'.replace('invalid offsetof','invalid- offsetof').replace('- offsetof','-offsetof')
   run([CMAKE,'-G','Ninja','-S',Path(__file__).parent,'-B',tree,f'-DMW34_ROOT={ROOT}',f'-DMW34_DERIVED={derived}',f'-DMW34_BINDINGS={ROOT}/reports/m4-joint27-startup/build-only-r1/{level}',f'-DMW34_OBJECTS={";".join(b["objects"][level])}',f'-DCMAKE_CXX_COMPILER={LLVM}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
   run([CMAKE,'--build',tree,'--parallel','8'],f'{level}-build.log');worker=tree/'mw34_joint_startup27.exe';workers[level]={'path':str(worker),'sha256':sha(worker),'objects':b['objects'][level]}
  for p,h in sources.items():assert sha(p)==h,('Sourcechanged',p)
 except BaseException:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()}
 report={'passed':failure is None,'failure':failure,'scope':'Fresh actual native candidate compile only; small stable outer host boundary before unchanged large body, all frozen translated objects reused','sources':sources,'tools':tools,'commands':commands,'workers':workers,'artifacts':artifacts,'guest_executed':False,'whole_M4_complete':False}
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');artifacts[str(out/'build.json')]=sha(out/'build.json');(out/'pins.json').write_text(json.dumps({'files':sources|artifacts|tools},indent=2)+'\n')
 if failure:raise RuntimeError(failure)
if __name__=='__main__':main(sys.argv[1])
