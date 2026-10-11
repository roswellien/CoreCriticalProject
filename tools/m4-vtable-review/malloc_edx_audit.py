"""Review finite original HeapAlloc EDX carry without later CPU seeds."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-vtable-review'/name;need(not out.exists(),'Fresh independent finite boundary review');out.mkdir(parents=True);pins={};facts=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Pinned physical boundary input');need(str(p)not in pins or pins[str(p)]==v,'Stable read');pins[str(p)]=v;return p
 report=json.loads(pin(R/'reports/m4-next-source/original-game-source-r1/report.json','d463ca7beddb8b7ccce6c51749d9146cf70e9c7de47cc42cba9584a9430a2f04').read_bytes());need(report['passed']and report['counts']['true_API_EDX_scalar_positive_source_carries']==414,'Final carried source prefix proof')
 source=pin(R/'tools/m4-next-source/compare_original_game_v5.py',report['files'][str(R/'tools/m4-next-source/compare_original_game_v5.py')]).read_text();block=source.split('def finite_malloc(model,target):',1)[1].split('\n      machine.run(',1)[0]
 need("fact[25]==0x78001385 and fact[19]==0"in block and "model.reg('edx',fact[12])"in block,'Uses actual returnPC and typed CPU after.EDX field; CPU.pc intentionally unpopulated')
 need('nullsnapshots'not in block and 'actual_cpu'not in block and 'after['not in block and 'b['not in block,'Finite boundary obtains no later free-entry or phase AFTER EDX seed')
 need("model.api_return(site,0,pointer)"in block and "target==0x780012b3 and site in(0x78010a7e,0x5f401eb5)"in block,'Narrow positive malloc finite boundary only; native model unaffected')
 contract=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d').read_bytes());by={r['pc']:r for r in contract['instructions']};pcs=(0x78001385,0x78001367,0x7800136a,0x78001371,0x78001372,0x78001373,0x78001374,0x78001375,0x780012d9,0x780012db,0x780012dc,0x780012e2,0x780012c2,0x780012c3,0x780012c4)
 s=importlib.util.spec_from_file_location('EDX_physical_PE',pin(R/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(s);s.loader.exec_module(PE);pe=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());rows=[]
 expected={0x78001385:('jmp','0x78001367'),0x78001367:('mov','ecx, dword ptr [ebp - 0x10]'),0x7800136a:('mov','dword ptr fs:[0x0], ecx'),0x78001371:('pop','edi'),0x78001372:('pop','esi'),0x78001373:('pop','ebx'),0x78001374:('leave',''),0x78001375:('ret',''),0x780012d9:('test','eax, eax'),0x780012db:('pop','ecx'),0x780012dc:('je','0x7800cc3f'),0x780012e2:('ret',''),0x780012c2:('pop','ecx'),0x780012c3:('pop','ecx'),0x780012c4:('ret','')}
 for pc in pcs:
  row=by[pc];need((row['mnemonic'],row['operands'])==expected[pc]and pe.read(pe.rva_range(pc-pe.image_base,row['width'])[0],row['width'])==bytes.fromhex(row['bytes_hex']),'Exact complete reached positive malloc return-path instruction');rows.append(row)
 need(0x780013d6 not in pcs,'No unrelated positive-free path admitted')
 p=out/'physical-return-path.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p)
 s=importlib.util.spec_from_file_location('EDX_true_archive',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(s);s.loader.exec_module(D);a=D.DirectSet(R/'reports/m4-vtable-original/execution-r1/original/transport.json',pin);order=json.loads(pin(R/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order']
 try:
  for seq in range(6):
   n=0
   for phase,item in enumerate(order):
    stem=f'phase/{seq}/{phase}/';raw=a.data(stem+'api-ledger.bin');need(len(raw)%104==0,'Actual true fixed API observations')
    for index in range(len(raw)//104):
     q=struct.unpack_from('<26I',raw,index*104)
     if q[24]!=0:continue
     need(q[10]and q[21]==0 and q[22]>0 and q[22]%16==0 and q[25]==0x78001385 and q[19]==0,'Actual successful mode1 allocation has exact typed returnPC/CPU-after schema')
     size=struct.unpack('<I',a.data(stem+f'api-initial/{index}/size.bin'))[0];need(size>=q[22]and len(a.data(stem+f'api-initial/{index}/bytes.bin'))==size,'Complete actual initial allocation input backing exists at same genuine API boundary')
     facts.append(dict(sequence=seq,phase=phase,root=item['entry'],API_index=index,retPC=q[25],actual_after_EDX=q[12],rounded_request=q[22]));n+=1
   need(n==69,'All actual fifty MFC plusnineteen strdup positive allocation leaves per sequence')
 finally:a.close()
 need(len(facts)==414,'All real original API EDX facts independently inspected');p=out/'API-EDX-facts.json';p.write_text(json.dumps(facts,indent=2)+'\n');pin(p);pin(__file__);pin(R/'reports/m4-vtable-original/preparation-r3/report.json','a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5');pin(R/'reports/m4-vtable-original/build-r2/build.json','ea4fb73e11dfa0d5c4b6f4145eb57df5148e5b096bb44e3fdd6c8d9d99e6dc5a')
 result=dict(passed=True,scope='Independent finite original positive malloc EDX carry review. Scalar comes only from genuine typed HeapAlloc AFTER boundary; exact physical positive return path preserves it to malloc RET. No later free-entry/phase AFTER seed, native API injection, whole original provider stack or volatile equivalence claim.',actual_API_EDX_scalar_carries=414,physical_return_instructions=15,no_later_CPU_seed=True,full_source_freeNULL_CPU_snapshots=report['counts']['NULLfree_source_CPU_FX_ENV_frame_snapshots'],files=pins,physical_closure=verify_manifest(pins));(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
