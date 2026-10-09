"""Source-derived generic checker interface, not an expected-machine oracle."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
import recover_v2 as R
ROOT=R.ROOT
REC_SHA='2d1c4a3f41505358df0ba8aaf4ed31c4b90a08d18b8bdf5cf1ed3eed2d996170'
HEAP_SHA='a0'

def main(name):
 out=ROOT/'reports/m4-crt-locale-batch-recovery'/name;R.need(name=='interface-r1' and not out.exists(),'Fresh source operand interface')
 files={}
 def add(p,h=None):
  p=Path(p).absolute();v=R.sha(p);R.need(h is None or h==v,'Pinned operand-interface source');files[R.normalized(str(p))]=v;return p
 report=R.read(add(ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json',REC_SHA))
 alloc=R.read(add(ROOT/'reports/m4-crt-allocation-recovery/recovery-r1/report.json',R.ALLOC_SHA))
 heap_path=add(ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json');heap=R.read(heap_path)
 R.need(heap['passed'] and heap['provider_sha256']==R.PROVIDER_SHA,'Frozen literal heap version source identity')
 pe_spec=importlib.util.spec_from_file_location('interface_PE',add(ROOT/'tools/m4-crt/recover_provider.py'));mod=importlib.util.module_from_spec(pe_spec);pe_spec.loader.exec_module(mod)
 pe=mod.PE(add(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',R.PROVIDER_SHA),R.PROVIDER_SHA)
 allrows={};spans=[]
 sources=[('locale-batch',report,tuple(report['spans'])),('allocation',alloc,tuple(alloc['spans'])),
  ('heap-version',heap,('heap-fragment','heap-provider','selector-prefix','stack-probe','selector-conditions','selector-environment-frontier','selector-mode1-cold','selector-epilogue'))]
 for domain,source,labels in sources:
  for label in labels:
   s=source['spans'][label];spans.append(dict(domain=domain,label=label,start=s['start'],end_exclusive=s['end_exclusive'],bytes=s['bytes'],sha256=s['sha256'],section=s.get('section')))
   for original in s['instructions']:
    r={k:original[k] for k in ('pc','width','bytes_hex','mnemonic','operands')}
    if 'repeat' in original:r['repeat']=original['repeat']
    if r['mnemonic'] in ('rep','repe','repz','repne','repnz'):
     r['repeat']=r['mnemonic'];r['mnemonic'],r['operands']=r['operands'].split(None,1)
    R.need(pe.read(r['pc']-pe.base,r['width'])==bytes.fromhex(r['bytes_hex']),'Every current/reused interface instruction matches exact original PE')
    c=R.instruction_contract(r)
    R.need(r['pc'] not in allrows or allrows[r['pc']]==c,'Exact repeated current/reused instruction contract');allrows[r['pc']]=c
 def wire(r):
  operands=[];op=r['mnemonic'];decoded=r['decoded_operands']
  for i,value in enumerate(decoded):
   kind=value['kind'];bits=value.get('bits',0) or next((x.get('bits',0) for x in decoded if x.get('bits',0)),32)
   access='r'
   if i==0 and op in ('mov','lea','movzx','movsx','pop'):access='w'
   elif i==0 and op in ('add','sub','and','or','xor','shl','shr','sar','sbb','inc','dec','neg'):access='rw'
   if kind=='memory':
    terms=value['terms'];R.need(len(terms)<=2,'At most base/index source address terms');base=None;index=None;scale=1
    for term in terms:
     if term['scale']==1 and base is None:base=term['register']
     else:R.need(index is None and term['scale'] in (1,2,4,8),'Exact legal source SIB');index=term['register'];scale=term['scale']
    disp=value['displacement'];disp=disp if disp<2**31 else disp-2**32
    access=('r' if i in r['explicit_memory_reads'] else '')+('w' if i in r['explicit_memory_writes'] else '')
    if op=='lea':access='address'
    operands.append(dict(kind='mem',width=bits//8,access=access,mem=dict(segment=value['segment'],base=base,index=index,scale=scale,disp=disp)))
   elif kind=='register':operands.append(dict(kind='reg',width=bits//8,access=access,reg=value['register']))
   else:operands.append(dict(kind='imm',width=bits//8,access='r',imm=value['value']))
  return dict(address=r['pc'],size=r['width'],bytes_hex=r['bytes_hex'],mnemonic=op,operands=operands,repeat=r.get('repeat'),implicit_memory=r['implicit_memory'],flags=r['flags'])
 rows=[wire(allrows[pc]) for pc in sorted(allrows)];out.mkdir(parents=True)
 for p in (Path(__file__),Path(R.__file__),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):add(p)
 def publish(filename,value):
  p=out/filename;R.publish_bytes(p,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode());add(p);return p
 generic=publish('operand-contracts.json',dict(schema='mw34-locale-batch-generic-source-interface-v1',width_unit='bytes',
  instruction_count=len(rows),instructions=rows,source_spans=spans,implicit_operations_checked_separately=True,
  nonFS_flat_address_admission_requires_carried_DS_SS_ES_bases_zero=True,expected_machine_values_included=False))
 semantic=publish('instruction-contracts.json',dict(schema='mw34-locale-batch-original-memory-specs-v1',instructions=[allrows[p] for p in sorted(allrows)],source_spans=spans))
 references=publish('API-primary-references.json',dict(read_on='2026-10-09',sources=[
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-getstringtypew',facts='Four arguments; nonzero BOOL success; output WORD per wide source character.'),
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-getstringtypea',facts='Five arguments including LCID; output character classifications are WORDs.'),
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-lcmapstringw',facts='Six arguments; destination count0 queries required size; mapping output units are wide characters; failure may leave partial output.'),
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-multibytetowidechar',facts='Six arguments; source byte count and destination wide-character count are distinct; count0 can query size.'),
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-widechartomultibyte',facts='Eight arguments; source wide-character count and destination byte count are distinct.'),
  dict(url='https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-getcpinfo',facts='Two arguments; finite BOOL and CPINFO contents drive source, with no assumed default code page.')],API_executed=False))
 result=dict(schema='mw34-m4-locale-batch-source-interface-v1',passed=True,recovery_sha256=REC_SHA,accepted_allocation_source_sha256=R.ALLOC_SHA,
  heap_source_path=str(heap_path),heap_source_sha256=R.sha(heap_path),source_instruction_count=len(rows),source_span_records=len(spans),
  operand_contracts_path=str(generic),operand_contracts_sha256=R.sha(generic),instruction_contracts_path=str(semantic),instruction_contracts_sha256=R.sha(semantic),
  expected_machine_values_included=False,API_executed=False,original_executed=False,native_component_executed=False,files=files,physical_closure=R.verify_manifest(files))
 p=publish('report.json',result);R.publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-locale-batch-interface-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,instructions=len(rows),report_sha256=R.sha(p),operand_contracts_sha256=R.sha(generic),instruction_contracts_sha256=R.sha(semantic))))

if __name__=='__main__':main(sys.argv[1])
