"""Read-only physical provider LLVM/COFF export proof; frozen lifts remain unchanged."""
import importlib.util,hashlib,json,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];LIFTS=ROOT/'reports/m4-mfc-native/lifts-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise RuntimeError(w)
def main(name):
 out=ROOT/'reports/m4-mfc-native'/name;need(re.fullmatch('symbol-attribution-r[1-9][0-9]*',name) and not out.exists(),'Fresh provider export proof');pins={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Physical source pin');pins[str(p)]=v;return p
 report=json.loads(pin(LIFTS/'report.json','3c49ba0a564416ec1c3eb1b3c656f82381947cfd47cabc8a076209246eecf73d').read_bytes())
 parser_path=pin(ROOT/'tools/m4-strings-source/symbol_attribution.py');spec=importlib.util.spec_from_file_location('provider_CO​​FF_attribution',parser_path);parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
 out.mkdir(parents=True);rows=[];objects=[]
 for label,v in report['source_bodies'].items():
  host=pin(LIFTS/(label+'-host.ll'),v['host_sha256']);symbol=v['symbol'];need(re.search(r'^define ptr @'+symbol+r'\(ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+\)',host.read_text(),re.M),'Actual provider ptr(ptr,i32,ptr) LLVM entry')
  row=dict(entry=v['entry'],symbol=symbol,source_signature='ptr (ptr, i32, ptr)',host_path=str(host),host_sha256=sha(host),objects={})
  for level,o in v['objects'].items():
   path=pin(o['path'],o['sha256']);row['objects'][level]=dict(path=str(path),sha256=sha(path),**parser.coff_definition(path,symbol));objects.append((path,symbol))
  rows.append(row)
 nm=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-nm.exe');argv=[str(nm),'--format=posix','--print-file-name','--defined-only',*[str(p) for p,_ in objects]];cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000);need(cp.returncode==0,'Physical batched llvm-nm provider exports');(out/'defined-symbols.txt').write_bytes(cp.stdout);(out/'nm.stderr').write_bytes(cp.stderr)
 lines=cp.stdout.decode().splitlines()
 for path,symbol in objects:need(sum(line.startswith(str(path)+': '+symbol+' T ') for line in lines)==1,'Independent COFF parser and actual nm agree')
 (out/'dispatch.json').write_text(json.dumps(rows,indent=2)+'\n');pin(Path(__file__));pin(Path(sys.executable))
 for p in out.iterdir():
  if p.is_file():pin(p)
 result=dict(passed=True,scope='Static MFC allocator positive-path and free-wrapper physical LLVM signature and AMD64 executable external symbols; no execution or cold-path acceptance',body_count=2,physical_COFF_count=4,sealed_original_lifts_modified=False,files=pins,native_executed=False,roots_admitted=0)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
