"""Explicit complete provider-state reads and executed dependency sealing."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=ROOT/'reports/m4-tree-source/connected125-preparation-r3'
 if out.exists():raise ValueError('Fresh receipt')
 out.mkdir(parents=True);pins={}
 for source,target in [('compare_connected125_v2.py','compare_connected125_v3.py'),('compare_provider125_v2.py','compare_provider125_v3.py')]:
  src=HERE/source;s=src.read_text();pins[str(src)]=sha(src)
  old="len(machine.lockit_import_proofs)==8 and len(machine.lockit_state_reads)==8,'All eight literal owning imports and authentic state reads'"
  if old not in s:raise ValueError('Exact state-read anchor')
  s=s.replace(old,"len(machine.lockit_import_proofs)==8 and len(machine.lockit_state_reads)==34,'Eight old literal owning imports and all34 original initialized-provider state reads'")
  anchor='  passed=True'
  dependency_seals="""  for name in ('recovery-r1/report.json','recovery-r1/instruction-contracts.json','game-callbacks-r1/report.json','game-callbacks-r1/callbacks.json','dynamic-contracts-r1/report.json','dynamic-contracts-r1/normal-contracts.json'):pin(ROOT/'reports/m4-tree-source'/name)
  seen_modules=set();modules=[G]
  while modules:
   module=modules.pop()
   if id(module)in seen_modules:continue
   seen_modules.add(id(module));path=getattr(module,'__file__',None)
   if path:pin(path)
   for key in ('G','I','SF'):
    value=getattr(module,key,None)
    if value is not None and hasattr(value,'__file__'):modules.append(value)
  pin(ROOT/'tools/m4-tree-source/prepare_connected125_v2.py');pin(ROOT/'tools/m4-tree-source/prepare_connected125_v3.py');pin(ROOT/'tools/m4-lockit-source/identity_records.py')
"""
  if anchor not in s:raise ValueError('Exact seal anchor')
  s=s.replace(anchor,dependency_seals+anchor);ast.parse(s);dst=HERE/target
  if dst.exists():raise ValueError('Fresh tool')
  dst.write_text(s);pins[str(dst)]=sha(dst)
 pins[str(Path(__file__).resolve())]=sha(__file__)
 (out/'report.json').write_text(json.dumps(dict(passed=True,execution_credit=False,provider_initialized_state_reads_per_case=34,old_four_imports_per_case=8,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
