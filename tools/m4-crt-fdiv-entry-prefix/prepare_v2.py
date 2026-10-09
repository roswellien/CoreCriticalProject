"""Additive, exactly reversible game-only undefined-helper namespace repair."""
import argparse,hashlib,json,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-entry-prefix'
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def save(p,v):
 with pathlib.Path(p).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def main(out):
 out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh namespace preparation');files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact frozen namespace dependency '+str(p));need(str(p)not in files or files[str(p)]==v,'Consistent binding');files[str(p)]=v
 before=BASE/'preparation-r1';bind(before/'report.json','f7d519be39f2455c2703b390e4c6cd39791b98808a4b5018c9ee5a39799226aa')
 for p,h in json.loads((before/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():bind(p,h)
 bind(before/'pins.json')
 failed=BASE/'build-r1/build.json';receipt=json.loads(failed.read_text(encoding='utf-8-sig'));need(not receipt['passed']and not receipt['native_component_executed'],'Actual build-only namespace collision retained');bind(failed)
 for group in('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
  for p,h in receipt[group].items():bind(p,h)
 log=BASE/'build-r1/build-O0.log';need('duplicate symbol: __remill_undefined_8'in log.read_text(encoding='utf-8-sig'),'Concrete link collision diagnostic')
 game=ROOT/'reports/m4-crt-entry/native-preparation-r1';original=game/'candidate.ll';bind(original)
 api=json.loads((game/'report.json').read_text(encoding='utf-8-sig'));need(api['all_named_type_layouts_equal']and api['State_bytes']==3504,'Exact34 type prior layout proof')
 old=b'@__remill_undefined_8';new=b'@mw34_fdiv_entry_undefined_8';ir=original.read_bytes();need(ir.count(old)>0 and new not in ir,'Only game namespace collision present');changed=ir.replace(old,new);need(changed.replace(new,old)==ir,'Literal complete IR reverse equality')
 cpp=(before/'composition.cpp').read_bytes();need(cpp.count(b'__remill_undefined_8')==1 and b'mw34_fdiv_entry_undefined_8'not in cpp,'Exactly one C++ throwing bridge definition');modified=cpp.replace(b'__remill_undefined_8',b'mw34_fdiv_entry_undefined_8');need(modified.replace(b'mw34_fdiv_entry_undefined_8',b'__remill_undefined_8')==cpp,'Literal complete C++ reverse equality')
 out.mkdir();(out/'candidate.ll').write_bytes(changed);(out/'composition.cpp').write_bytes(modified);shutil.copyfile(before/'seed.hpp',out/'seed.hpp');shutil.copyfile(original,out/'game-ancestor.ll');shutil.copyfile(before/'composition.cpp',out/'composition-ancestor.cpp')
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';commands=[];objects={}
 try:
  for level in ('O0','O2'):
   obj=out/('candidate-'+level+'.obj')
   for program,args,label in ((llvm/'clang.exe',['--target=x86_64-pc-windows-msvc','-'+level,'-c',str(out/'candidate.ll'),'-o',str(obj)],'compile-'+level),(llvm/'llvm-objdump.exe',['--disassemble','--syms','--unwind-info',str(obj)],'object-'+level)):
    bind(program);cp=subprocess.run([str(program),*args],capture_output=True);(out/(label+'.stdout')).write_bytes(cp.stdout);(out/(label+'.stderr')).write_bytes(cp.stderr);commands.append({'program':str(program),'arguments':args,'exit_code':cp.returncode});need(cp.returncode==0,'Actual compiler/COFF generation')
   symbols=(out/('object-'+level+'.stdout')).read_text();need('mw34_fdiv_entry_undefined_8'in symbols and '__remill_undefined_8'not in symbols and '.pdata'in symbols,'New game helper external and actual unwind section');objects[level]={'path':str(obj),'sha256':sha(obj)}
  save(out/'report.json',{'passed':True,'scope':'Source/object-only game helper namespace repair; no original/native worker execution','original_IR_sha256':sha(original),'new_IR_sha256':sha(out/'candidate.ll'),'IR_exact_reverse_equality':True,'helper_name_occurrences_renamed':ir.count(old),'all34_literal_types_unchanged':api['layouts'],'State_bytes':3504,'guest_arithmetic_or_CFG_rewrites':0,'CXX_bridge_exact_reverse_equality':True,'bridge_may_unwind_and_noexcept_false_retained':True,'generic_provider_helper_unchanged':True,'objects':objects,'commands':commands,'native_executed':False,'original_executed':False,'whole_M4_complete':False})
 except Exception as e:
  save(out/'failure.json',{'passed':False,'reason':str(e),'commands':commands});raise
 finally:
  bind(__file__)
  for p in out.rglob('*'):
   if p.is_file():bind(p)
  save(out/'pins.json',{'files':files})
 print(json.dumps({'passed':True,'bindings':len(files),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
