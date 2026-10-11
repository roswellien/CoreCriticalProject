"""Additive independent observer review derived from immutable accepted116 audit."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
 s=(R/'tools/m4-container-review/observer_static.py').read_text()
 s=s.replace('m4-container-review','m4-vtable-review').replace('m4-container-source/original-preparation-r2','m4-vtable-original/preparation-r3').replace('fc3ce8ef54040236bced7072b3c121a0a7121c19ca81ef6e19ae0f54d5a06c49','a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5')
 s=s.replace('len(hooks)==30','len(hooks)==33').replace('Thirty physical FS spans','Thirty-three physical FS spans').replace('physical_FS_spans=30','physical_FS_spans=33').replace('boundaries=62','boundaries=74')
 marker=' pin(__file__);report=dict('
 extra='''
 vh=pin(p/'vtable-hook-bindings.json');vt=pin(p/'vtable_observer_x86.asm').read_text();vrows=json.loads(vh.read_bytes());need(len(vrows)==6,'Six exact indirect observer spans')
 for row in vrows:
  physical(row['PC'],row['raw_bytes']);part=vt.split(row['declared_observer']+' PROC\\n',1)[1].split(row['declared_observer']+' ENDP',1)[0]
  before,tail=part.split(' db ',1);capture(before,'vtable','vtable_observe');line,*remainder=tail.splitlines();replayed=bytes(int(q.strip()[:-1],16)for q in line.split(','));need(replayed==bytes.fromhex(row['replayed_bytes']),'Exact physical entry or genuine RET replay')
  if row['kind']==0:need(row['continuation']==row['PC']+len(replayed)and remainder==[' jmp DWORD PTR vtable_continue_'+format(row['PC'],'x')],'Exact entry continuation')
  else:need(not remainder and replayed in (b'\\xc3',b'\\xc2\\x04\\x00'),'Literal genuine RET with no adjacent byte execution')
 need(vrows[4]['PC']==0x59ff0d and vrows[4]['raw_bytes']=='c39090568b'and vrows[4]['replayed_bytes']=='c3','Entire five-byte return patch authenticated')
 need(images['game'].read(images['game'].rva_range(0x59ff10-0x400000,2)[0],2)==bytes.fromhex('568b'),'Neighbor prefix is actual code, not NOP padding')
 source=pin(R/'tools/m4-next-source/game_model.py');spec=importlib.util.spec_from_file_location('complete120_literal_closure_for_patch',source);G=importlib.util.module_from_spec(spec)
 old_read=Path.read_bytes
 def observed_read(q):
  data=old_read(q)
  if q.is_relative_to(R):pin(q)
  return data
 Path.read_bytes=observed_read
 try:spec.loader.exec_module(G);program,_=G.source_program()
 finally:Path.read_bytes=old_read
 need(len(program)==2633 and 0x59ff0d in program,'Entire carried120 literal instruction closure')
 for pc,row in program.items():
  width=row['width'];need(pc+width<=0x59ff10 or pc>=0x59ff12,'Excluded adjacent59FF10 prefix has no source instruction')
  for operand in row['decoded_operands']:
   if row['mnemonic']in('call','jmp')and operand.get('kind')=='immediate':need(operand['value']!=0x59ff10,'No declared direct control enters excluded neighbor')
  if 0x400000<=pc<0xa20000:physical(pc,row['bytes_hex'])
 root_order=json.loads(pin(R/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order'];need(len(root_order)==120 and all(q['entry']!=0x59ff10 for q in root_order),'Excluded neighbor is not any selected root')
 # Pin every frozen literal model dependency so closure absence is not a pseudocode inference.
 for module in list(sys.modules.values()):
  q=getattr(module,'__file__',None)
  if q and str(R/'tools').lower()in str(q).lower()and str(q).endswith('.py'):pin(q)
 for q in R.glob('reports/m4-*/**/instruction-contracts.json'):
  if str(q)in cpp:pin(q)
 neighbor=dict(patch_PC=0x59ff0d,patch_bytes='c39090568b',actual_RET='c3',NOP_tail='9090',excluded_neighbor_PC=0x59ff10,excluded_neighbor_prefix='568b',complete_literal_rows=len(program),selected_roots=120,neighbor_execution_admitted=False,frozen_padding_bytes_field_is_bounded_unreplayed_tail=True)
 (out/'neighbor-scope.json').write_text(json.dumps(neighbor,indent=2)+'\\n');pin(out/'neighbor-scope.json')
'''
 s=one(s,marker,extra+marker)
 s=one(s,'compiled_hook_check_pending=True,files=pins','compiled_hook_check_pending=True,physical_indirect_spans=6,complete120_neighbor_frontier_checked=True,neighbor_scope=neighbor,files=pins')
 (H/'observer_static.py').write_text(s)
 s=(R/'tools/m4-container-review/observer_compiled_v3.py').read_text()
 s=s.replace('m4-container-review','m4-vtable-review').replace('observer-static-r1','observer-static-r2').replace('f6f8b3d9f5d278af06b52bac560daaac76105ba43b0847d6be128813591bbba4','b7151a732bed9021d7cd80c80bdf371ac1e2866a965a52f1a49856c7b7d70aeb')
 s=s.replace('m4-container-source/original-build-r2','m4-vtable-original/build-r2').replace('8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541','ea4fb73e11dfa0d5c4b6f4145eb57df5148e5b096bb44e3fdd6c8d9d99e6dc5a')
 s=s.replace('m4-container-source/original-validation-r1','m4-vtable-original/validation-r1').replace('4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b','2a072a38b8f0ff98377709a10da203b017bea92615baa9b153f548027565c251')
 s=s.replace('mw34_joint_startup116_original','mw34_joint_startup120_original').replace('m4-container-source/original-preparation-r2','m4-vtable-original/preparation-r3').replace('(fs,60)','(fs,66)')
 s=s.replace('m4-container-source/recovery-r3/instruction-contracts.json','m4-next-source/recovery-r1/instruction-contracts.json')
 s=one(s,' finally:a.close()',"""
  spec=importlib.util.spec_from_file_location('independent_complete_indirect_observer',pin(R/'tools/m4-vtable-review/observer_indirect.py'));V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);V.main(a,pin,out,counts,b,R/'reports/m4-vtable-original/preparation-r3',link)
 finally:a.close()""")
 s=s.replace('Independent actual original observer compiled COFF/final-link and thirty true free(NULL) frame/hardware/nested-chain audit.','Independent actual original33FS+2NULLfree+6indirect compiled COFF/final-link, genuine30NULLfree and36indirect entry/preRET frame/hardware audit.')
 (H/'observer_compiled.py').write_text(s)
if __name__=='__main__':main()
