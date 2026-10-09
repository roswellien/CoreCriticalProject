"""Fresh derivative preserves measured sticky exception bits at source zeroFSQRT."""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh zeroFSQRT correction');out.mkdir(parents=True);pins={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen zeroFSQRT repair input');pins[str(p)]=v;return p
 sealed=ROOT/'reports/m4-onexit-source/lifts-r4';d=json.loads(pin(sealed/'report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e').read_bytes());b=d['source_bodies']['f_4020d0'];old=pin(sealed/'f_4020d0-host.ll',b['host_sha256']).read_text()
 block='740:                                              ; preds = %706\n  %741 = getelementptr inbounds nuw i8, ptr %state, i32 2755\n  store i8 0, ptr %741, align 1\n  %742 = getelementptr inbounds nuw i8, ptr %state, i32 2753\n  store i8 0, ptr %742, align 1\n  %743 = getelementptr inbounds nuw i8, ptr %state, i32 2745\n  store i8 0, ptr %743, align 1\n  br label %_ZN12_GLOBAL__N_17DoFSQRTEP6MemoryR5State2InIjES4_ItE.exit'
 need(old.count(block)==1,'Exactly one literal zeroFSQRT branch')
 replacement=block
 for var in ('741','742','743'):replacement=replacement.replace('  store i8 0, ptr %'+var+', align 1\n','')
 fresh=old.replace(block,replacement);source_symbol='mw34_onexit_game_f_4020d0_body';symbol='mw34_onexit_game_f_4020d0_sticky_body'
 need(fresh.count('define ptr @'+source_symbol+'(')==1,'One source body definition');fresh=fresh.replace('define ptr @'+source_symbol+'(','define ptr @'+symbol+'(',1)
 expected=old
 for var in ('741','742','743'):expected=expected.replace('  store i8 0, ptr %'+var+', align 1\n','',1)
 expected=expected.replace('define ptr @'+source_symbol+'(','define ptr @'+symbol+'(',1);need(expected==fresh,'Only three exact zero-path stores removed and physical symbol changed')
 host=out/'f_4020d0_sticky-host.ll';host.write_text(fresh)
 need(re.search(r'^define ptr @'+symbol+r'\(ptr noalias %state, i32 %program_counter, ptr noalias %memory\)',fresh,re.M),'Unchanged exact native C ABI')
 sp=importlib.util.spec_from_file_location('fsqrt_coff_verifier',pin(ROOT/'tools/m4-onexit-source/symbol_attribution_v2.py'));S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=pin(llvm/'clang.exe');nm=pin(llvm/'llvm-nm.exe');objects={}
 for level in ('O0','O2'):
  obj=out/('f_4020d0_sticky-'+level+'.obj');argv=[str(clang),'--target=x86_64-pc-windows-msvc','-'+level,'-c',str(host),'-o',str(obj)];t=time.perf_counter();r=subprocess.run(argv,capture_output=True,timeout=60,creationflags=0x08000000);(out/(level+'-compile.stdout')).write_bytes(r.stdout);(out/(level+'-compile.stderr')).write_bytes(r.stderr);commands.append(dict(argv=argv,returncode=r.returncode,seconds=time.perf_counter()-t));need(r.returncode==0,'Repaired source LLVM compiles');pin(obj)
  objects[level]=dict(path=str(obj.resolve()),sha256=sha(obj),**S.coff_definition(obj,symbol));oldobj=b['objects'][level];pin(oldobj['path'],oldobj['sha256'])
 r=subprocess.run([str(nm),'--format=posix','--print-file-name','--defined-only',*[o['path']for o in objects.values()]],capture_output=True,timeout=30,creationflags=0x08000000);need(r.returncode==0,'Repaired physical symbols');(out/'physical-symbols.txt').write_bytes(r.stdout)
 for o in objects.values():need(sum(x.startswith(o['path']+': '+symbol+' T ')for x in r.stdout.decode().splitlines())==1,'Independent physical symbol')
 interface=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes());row=next(r for r in interface['instructions']if r['pc']==0x4020f5);need(row['mnemonic']=='fsqrt'and row['bytes_hex']=='d9fa','Original literal zeroFSQRT sourcePC')
 originals=pin(ROOT/'reports/m4-onexit-source/original-game-source-r2/report.json','e3854a8ceaaab3461a27fc45bf8a426378241d298096ec9ec405d81f67d94a5c');pin(ROOT/'tools/m4-onexit-source/game_model.py');source=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/lib/Arch/X86/Semantics/X87.cpp')
 need('if (IsZero(st0)) {\n    state.sw.ie = 0;\n    state.sw.de = 0;\n    state.sw.pe = 0;'in source.read_text(),'Original Remill zero-branch exception clearing identified')
 callbacks=json.loads(pin(ROOT/'reports/m4-onexit-source/game-callbacks-r2/callbacks.json','df3f761e5672e290a01d8ef729f6bef3489d9d9a5520c532ee685e0d689d4076').read_bytes());subset={k:v for k,v in callbacks['State_offsets_by_original_PC'].items()if 0x4020d0<=int(k)<0x402132}
 manifest=[dict(entry=0x4020d0,symbol=symbol,objects=objects,bridges=b['bridges'],undefined_calls=b['undefined_calls'],FP=True,research_terminal=None)]
 (out/'dispatch.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'declarations.hpp').write_text('#pragma once\nextern "C" void* '+symbol+'(void*, unsigned int, void*);\n');(out/'callbacks.json').write_text(json.dumps(dict(State_offsets_by_original_PC=subset),indent=2)+'\n')
 (out/'repair.json').write_text(json.dumps(dict(source_PC=0x4020f5,source_bytes_hex='d9fa',predicate='Exact raw80 IsZero(ST0) only',removed_State_stores=[dict(offset=o,old_store=0,new_effect='Retain incoming exact source State bit')for o in(2755,2753,2745)],preserved_nonzero_semantics=True,preserved_raw80_value=True,preserved_CW_and_TOP=True,preserved_source_state_layout=True,host_before_sha256=b['host_sha256'],host_after_sha256=sha(host),before_branch=block,after_branch=replacement,physical_source_symbol=source_symbol,physical_repaired_symbol=symbol,reference_policy='Six original32 zero-vector constructor BEFORE-only proofs retained; full physical hardware zeroFSQRT exception cases should validate derivative runtime',AFTER_machine_seed=False),indent=2)+'\n')
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():
  if p.is_file():pin(p)
 report=dict(passed=True,scope='Fresh source zeroFSQRT sticky exception semantic repair and O0/O2 AMD64 COFF preparation; runtime verification pending',dispatch_manifest=manifest,source_bodies={'f_4020d0_sticky':dict(entry=0x4020d0,symbol=symbol,host_sha256=sha(host),objects=objects,bridges=b['bridges'],instructions=b['instructions'])},overrides_entry=0x4020d0,source_PC=0x4020f5,removed_State_zero_stores=[2755,2753,2745],sealed_original64_modified=False,physical_COFF_count=2,native_executed=False,initializer_credit=False,whole_M4_complete=False,commands=commands,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),dispatch_sha256=sha(out/'dispatch.json'))))
if __name__=='__main__':main(sys.argv[1])
