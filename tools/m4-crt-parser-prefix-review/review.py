"""Independent compiled hardware/COFF review through pinned logical archives."""
import hashlib, json, pathlib, re, subprocess, sys
sys.dont_write_bytecode=True
from transport import ROOT, T, PINS as TRANSPORT_PINS, need, opened, read_json, sha_file, verify_manifest
from native_receipts import validate as native_receipts
BASE=ROOT/'reports/m4-crt-parser-prefix'
CATEGORIES=('sources','source_files','tools','tool_files','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','compiler_read_headers','artifacts')

def dependencies(build):
 files={}
 for key in CATEGORIES:
  for path,digest in build.get(key,{}).items():T.add(files,path,digest)
 for relative,digest in TRANSPORT_PINS.items():T.add(files,ROOT/relative,digest)
 for path,digest in T.SOURCES.items():T.add(files,path,digest)
 return files

def publication_stage(build_path,build,files):
 receipt=build_path.parent/'seal-stage.json';stage=read_json(receipt);T.add(files,receipt,sha_file(receipt))
 need(stage['passed'] is True and stage['stage']=='completed-native-capture-archive-publication' and stage['no_new_native_execution'] is True and stage['source_watch_rechecked'] is True,'Completed separately associated archive publication')
 need(pathlib.Path(stage['build_path']).absolute()==build_path and sha_file(build_path)==stage['build_sha256'],'Publication stage binds exact final build')
 need(pathlib.Path(stage['flat_build_path']).absolute()==build_path.parent/'flat-build.json' and sha_file(stage['flat_build_path'])==stage['flat_build_sha256'],'Publication stage binds exact completed native worker build')
 script=ROOT/'tools/m4-crt-parser-prefix-review/seal_captures.py';python=pathlib.Path('C:/Python314/python.exe')
 need(pathlib.Path(stage['script_path']).absolute()==script and pathlib.Path(stage['python_path'])==python,'Exact publication script and Python executable')
 T.add(files,script,stage['script_sha256']);T.add(files,python,stage['python_sha256'])
 command=stage['command'];need(command['program']=='C:/Python314/python.exe' and command['arguments']==[str(script),str(build_path.parent)] and command['exit_code']==0,'Exact actual publication command')
 need(type(command['monotonic_start_ticks']) is int and type(command['monotonic_end_ticks']) is int and type(command['monotonic_frequency']) is int and 0<=command['monotonic_start_ticks']<=command['monotonic_end_ticks'] and command['monotonic_frequency']>0 and type(command['duration_seconds']) in (int,float) and command['duration_seconds']>=0,'Honest monotonic archive publication timing')
 need(abs(command['duration_seconds']-(command['monotonic_end_ticks']-command['monotonic_start_ticks'])/command['monotonic_frequency'])<1,'Consistent archive publication timing')
 log=build_path.parent/'seal-captures.log';need(pathlib.Path(command['log_path']).absolute()==log,'Exact completed publication log');T.add(files,log,command['log_sha256'])
 return stage

def decode(path,out,label,files):
 commands=[];values=[]
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for tool,args,suffix in ((llvm/'llvm-objdump.exe',['--disassemble','--reloc','--x86-asm-syntax=intel'],'decode'),(llvm/'llvm-readobj.exe',['--unwind'],'unwind')):
  T.add(files,tool,sha_file(tool));argv=[str(tool)]+args+[str(path)];result=subprocess.run(argv,capture_output=True)
  need(result.returncode==0,'Fresh actual fixture decode/unwind succeeded');target=out/(label+'-'+suffix+'.txt');target.write_bytes(result.stdout);T.add(files,target,sha_file(target));values.append(result.stdout.decode())
  commands.append(dict(argv=argv,exit_code=result.returncode,output_path=str(target),output_sha256=sha_file(target)))
 return values,commands

def main(build_path,output):
 need(output.parent==BASE and output.name.startswith('independent-compiled-') and not output.exists(),'Fresh independent review output');output.mkdir()
 build=read_json(build_path);need(build['passed'],'Passed actual fixture build')
 files=dependencies(build);T.add(files,build_path,sha_file(build_path));T.add(files,__file__,sha_file(__file__))
 stage=publication_stage(build_path,build,files)
 native_commands=native_receipts(build_path,build,files)
 validator,association=T.load_validator();rows=[];checks=denials=records=0;commands=[]
 for level in ('O0','O2'):
  bundle,reader,result=opened(build,level)
  try:
   log_path=build_path.parent/level/'controls.log';log=log_path.read_text();match=re.fullmatch(r'(\d+) independent compiled checks / (\d+) scenarios passed\s*',log)
   need(match and int(match[1])==result['checks']+1 and int(match[2])==66 and result['malformed_token_denials']==27,'Exact actual assertions/request/typed-denial result')
   checks+=int(match[1]);denials+=27
   for i in range(1,67):
    for actor in ('writer','entry'):
     validator(reader.path(f'case-{i}/{actor}-host-before.bin'),reader.path(f'case-{i}/{actor}-host-after.bin'),i);records+=1
   obj=build_path.parent/level/'controls.obj';(compiled,unwind),decoded=decode(obj,output,level+'-independent-fixture',files);commands+=decoded
   need(all(name in compiled for name in ('sub_5ac3a0','sub_7800b38f','sub_780042e1','sub_780014f8','mw34_mainargs_mainargs_body','mw34_mainargs_normal_argv_body','mw34_carry_cmd_writer_body','mw34_mainargs_normal_parser_body')),'Fixture links all real prior bodies and complete normal parser object')
   need('__CxxFrameHandler' in unwind,'Actual C++ cleanup/unwind handlers present')
   rows.append(dict(level=level,scenarios=66,checks=int(match[1]),malformed_token_denials=27,logical_files=len(reader.expected),logical_reads=reader.reads,archive_path=build['capture_archives'][level]['path'],archive_sha256=build['capture_archives'][level]['sha256']))
  finally:bundle.close()
 closure=verify_manifest(files)
 report=dict(passed=True,scope='Exact new compiled prefix fixtures and unchanged rich hardware validator through strictly pinned complete archives',build_path=str(build_path),publication_stage=stage,native_commands=native_commands,checks=checks,scenarios=132,malformed_token_denials=denials,direct_host_records=records,nonzero_complete_legacy_metadata_records=records,rows=rows,archives=build['capture_archives'],validator=association,closure=closure,files=files,tools_commands=commands,ordinary_game_launched=False,original_executed=False,guest_original_equivalence_claimed=False,parser_RET=False,argument_outputs=False,whole_M4_complete=False)
 (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','checks','scenarios','malformed_token_denials','direct_host_records')}))

if __name__=='__main__':
 need(len(sys.argv)==3,'review.py sealed-new-build.json fresh-review-output');main(pathlib.Path(sys.argv[1]).absolute(),pathlib.Path(sys.argv[2]).absolute())
