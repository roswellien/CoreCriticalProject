from pathlib import Path
import importlib.util,json,sys,struct
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('provider_final_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
a=D.DirectSet(ROOT/'reports/m4-joint-startup54-root/execution-r6/O0/transport.json',lambda p,h=None:Path(p))
try:
 for stage in ('cleaned',):
  stem=f'sequence-0/{stage}/'; names={a.data(k).decode():k[:-9] for k in a.entries if k.startswith(stem+'registry-checkpoint-')and k.endswith('-name.bin')}
  print('physical_heap',[(n,a.words(stem+n+'.bin',11,'Q'))for n in ('heap-create-api-before','heap-create-api-after','heap-query-api-before','heap-query-api-after','heap-destroy-api-before','heap-destroy-api-after')])
  print('unseen_heap',[n for n in names if n.startswith('heap')]);continue
  print('checkpoints_last',list(names)[-35:]);print('names_first',list(names)[:35])
  print('allocations',list(struct.iter_unpack('<16Q',a.data(stem+'locale-allocations.bin'))));print('sections',list(struct.iter_unpack('<16Q',a.data(stem+'locale-critical-sections.bin'))))
  facts=[]
  for i in range(a.words(stem+'locale-summary.bin',32)[18]):
   w=a.words(stem+f'locale-api-{i}-witness.bin',32,'Q');facts.append((i,hex(w[2]),hex(w[3]),w[8],w[12],w[16],w[17],w[18],w[31]))
  print('API_firstlast',facts[:8],facts[-18:]);print('ledger_sizes',[(n,len(a.data(stem+n))) for n in ('locale-source-accesses.bin','locale-api-transports.bin','locale-research-accesses.bin','locale-research-projections.bin','heap-source-accesses.bin','heap-api-accesses.bin')])
finally:a.close()
