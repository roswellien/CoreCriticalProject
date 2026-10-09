"""Independent source and candidate build association for bounded CRT control.

No author execution comparator or expected AFTER payload is imported. A final
candidate audit is separate from this source contract and from root's scalar
execution observer and the independent compiled causal/hardware review.
"""
import hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-entry-control'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS, CHECKS, COMMANDS = {}, [], []
FROZEN = {
 'MW3/Mech3.exe':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
 'tools/analysis/pe.py':'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638',
 'tools/m4-runtime/runtime.cpp':'48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7',
 'tools/m4-runtime/runtime.hpp':'41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536',
 'reports/m4-crt-control-integration/research-r1/host.ll':'45de8ae06bda09bfbd7a734f4be67eeca6fc5a9f68161e614a89b2871a7b569a',
 'reports/m4-crt-control/research-r1/host.ll':'49e25a2cd2f9279970fac099141a08742ab678eb9b041be6b1368effc55ea5a9',
}

def need(ok, why):
 if not ok: raise ValueError(why)

def sha(p):
 with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p, wanted=None):
 p=Path(p).resolve(); h=sha(p)
 need(wanted is None or wanted==h,'Physical identity: '+str(p))
 need(str(p) not in PINS or PINS[str(p)]==h,'Conflicting physical identity')
 PINS[str(p)]=h; return p

def text(p): return pin(p).read_text(encoding='utf-8-sig')
def read(p): return json.loads(text(p))
def check(name, **facts): CHECKS.append(dict(name=name,passed=True,**facts))

def run(out, argv, name):
 argv=list(map(str,argv)); p=subprocess.run(argv,capture_output=True,cwd=ROOT)
 log=out/name; log.write_bytes(p.stdout+p.stderr); pin(log); pin(argv[0])
 COMMANDS.append(dict(arguments=argv,exit_code=p.returncode,log=str(log),log_sha256=sha(log)))
 need(p.returncode==0,'Independent decode: '+name); return p.stdout.decode(errors='replace')

def image_contract(out):
 parser=pin(ROOT/'tools/analysis/pe.py',FROZEN['tools/analysis/pe.py'])
 spec=importlib.util.spec_from_file_location('independent_control_PE',parser)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 game_path=pin(ROOT/'MW3/Mech3.exe',FROZEN['MW3/Mech3.exe'])
 provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',FROZEN['local/mw3-staged/Shared_DLLs/MSVCRT.DLL'])
 game,provider=game_path.read_bytes(),provider_path.read_bytes()
 pe,dll=module.PEImage(game),module.PEImage(provider)
 owners=[(lib['library'],sym)for lib in pe.imports()for sym in lib['symbols']if pe.image_base+sym['iat_rva']==0x5bb578]
 need(len(owners)==1 and owners[0][0].lower()=='msvcrt.dll' and owners[0][1].get('name')=='_controlfp','Unique original named import owner')
 need(pe.rva_u32(0x5bb578-pe.image_base)==0x1ded8a,'Original raw _controlfp IAT')
 exports=[e for e in dll.exports()if '_controlfp' in e['names']]
 need(len(exports)==1 and dll.image_base+exports[0]['rva']==0x780042e1 and 'forwarder'not in exports[0],'Unique direct original provider export')
 sources=[]
 for material,image,va,n,want in ((game,pe,0x5ac431,5,'f8b21f68d2277b61d744273c7c041f160b18ea4ada0625df395fc2053d33b3de'),(game,pe,0x5ac5a0,19,'ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac'),(game,pe,0x5ac5d6,6,'cd4225ce0b49983d72e298fad14f78fed9e8bfdc3042de603871ce08a29e3646'),(provider,dll,0x780042e1,303,'adf05ce99957b1a9d6c33dce1dda80a595cda795085d2794935bb4d78a46f47b'),(provider,dll,0x7801129b,125,'b48e01a7f8be0f6c5f477cb30911f7dc92adcca417894943587560507db19b88')):
  off=image.rva_range(va-image.image_base,n)[0]; data=material[off:off+n]
  need(hashlib.sha256(data).hexdigest()==want,'Exact source range')
  sections=[s for s in image.sections if s['virtual_address']<=va-image.image_base<s['virtual_address']+s['raw_size']]
  need(len(sections)==1 and sections[0]['readable'] and sections[0]['executable'] and not sections[0]['writable'],'File-backed RX source')
  sources.append(dict(va=va,bytes=n,file_offset=off,sha256=want,section=sections[0]['name']))
  (out/f'source-{va:x}.bin').write_bytes(data);pin(out/f'source-{va:x}.bin')
 program={}
 for label,path,start,stop in [('game-continuation',game_path,0x5ac431,0x5ac445),('wrapper',game_path,0x5ac5a0,0x5ac5b3),('thunk',game_path,0x5ac5d6,0x5ac5dc),('provider-hot',provider_path,0x780042e1,0x78004410),('provider-cold',provider_path,0x7801129b,0x78011318)]:
  output=run(out,[LLVM/'llvm-objdump.exe','-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={stop}',path],label+'.txt')
  image=pe if path==game_path else dll;material=game if path==game_path else provider
  for line in output.splitlines():
   match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$',line)
   if not match:continue
   pc=int(match[1],16);code=bytes.fromhex(match[2]);off=image.rva_range(pc-image.image_base,len(code))[0]
   need(material[off:off+len(code)]==code and start<=pc<stop,'Decoded bytes are actual original source')
   need(pc not in program,'Unique decoded PC')
   operands=re.sub(r'\s*<[^>]*>','',match[4]).strip()
   program[pc]=dict(bytes=len(code),instruction=match[3],operands=operands)
 expected={0x5ac431:('call','0x5ac5a0'),0x5ac436:('push','0x5e024c'),0x5ac43b:('push','0x5e0248'),0x5ac440:('call','0x5ac598'),0x5ac5a0:('push','0x30000'),0x5ac5a5:('push','0x10000'),0x5ac5aa:('call','0x5ac5d6'),0x5ac5af:('add','esp, 0x8'),0x5ac5b2:('ret',''),0x5ac5d6:('jmp','dword ptr [0x5bb578]'),0x780042fc:('wait',''),0x780042fd:('fnstcw','word ptr [ebp - 0x4]'),0x78004324:('fldcw','word ptr [ebp + 0xc]')}
 for pc,(ins,args)in expected.items():need(program[pc]['instruction']==ins and program[pc]['operands']==args,'Exact declared source contract '+hex(pc))
 need(sum(1 for pc in program if pc>=0x78000000)==148,'Complete actual provider hot/cold 148 instruction PCs')
 (out/'instruction-contract.json').write_text(json.dumps(program,indent=2)+'\n');pin(out/'instruction-contract.json')
 check('Original PE ownership, complete control source ranges and actual next caller dependency',import_owner=owners[0][0],import_name='_controlfp',raw_iat=0x1ded8a,provider_export=exports[0],source_spans=sources,provider_source_instructions=148,outer_source=0x5ac431,outer_return=0x5ac436,provider_callsite=0x5ac5aa,provider_return=0x5ac5af,next_callsite=0x5ac440,next_target=0x5ac598,next_return=0x5ac445)
 return program

def frozen_contract():
 for relative,want in FROZEN.items():pin(ROOT/relative,want)
 context=text(ROOT/'tools/m4-crt-control-integration/native_context.hpp')
 cw=text(ROOT/'tools/m4-guest-cw/guest_cw.cpp')
 need('std::longjmp' in context and 'std::array<std::jmp_buf,4>' in context,'Historical serial standalone longjmp boundary acknowledged')
 need('state_.x87.fxsave.cwd.flat=cw;std::memcpy(fx_.data(),&cw,2)' in cw,'CW transfer updates only persistent State/FX word')
 need('normalized(cw)!=cw' in cw and 'f.swd.flat||sw||f.ftw.flat' in cw and 'mx!=0x1f80||f.mxcsr.flat!=0x1f80' in cw,'Measured empty normalized transfer domain retained')
 check('Frozen runtime and admitted control transfer domain remain explicit',runtime_r9_changed=False,provider_pages_already_owned_by_FDIV=[0x78004000,0x78011000],minimum_guest_domain='Normalized coherent State/FX CW, masked corpus, empty TOP0/SW0/FTW0 and status shadow, MXCSR1F80',guest_FP_effect='Only normalized CW at State offset2768 and Runtime FX first2; metadata, raw80, XMM and other State carry',historical_risk='Standalone longjmp/cast-before-token bridge must not be adopted unchanged under the live outer entry',minimum_derivative='Remove standalone bridge definitions, exact typed active-owner dispatch, BridgeAbort C++ unwind boundary, full exception cleanup and terminal retry; no State/FX seed or remap',source_only_acceptance=True)

def main():
 out=Path(sys.argv[1]).resolve();need(out.parent==BASE and out.name.startswith('independent-source-')and not out.exists(),'Fresh isolated source review directory');out.mkdir(parents=True)
 (out/'review.py').write_bytes(Path(__file__).read_bytes());pin(out/'review.py')
 try:
  image_contract(out);frozen_contract()
  report=dict(passed=True,scope='Independent read-only original source/contract; final candidate and execution closure remain separate',checks=CHECKS,commands=COMMANDS,findings=[],full_CRT=False,native_menu=False,selected_initializer_count_unchanged=27,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');pin(Path(__file__))
  (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
  print(json.dumps(dict(passed=True,checks=len(CHECKS),files=len(PINS),report=str(out/'report.json'),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main()
