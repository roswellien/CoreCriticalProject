"""Physical source recovery and finite execution plan for the separate map root.

No candidate124 input or accepted files are changed. Dynamic node counts and
retained register imports remain obligations until genuine prefix execution.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(ROOT/p,h).read_bytes())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,pin(ROOT/p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True)
 front='reports/m4-lockit-frontier/recovery-r1/';shape=next(r for r in read(front+'root-shapes.json','ef35b482de766b81d979a5a6ff7ef427dcf73147375c6879d955c25986661526')if r['root']==0x4b7f70)
 graphs={int(k):v for k,v in read(front+'game-normal-graphs.json','c1b7dbed7a80b15eb789c5299369085450c34dd58a7eb7afd6ad4c20eca61be9').items()};normal={e:graphs[e]for e in shape['entries']};new={int(k):v for k,v in read(front+'game-new-graphs.json').items()if int(k)in normal};rows={r['pc']:r for g in normal.values()for r in g['instructions']}
 PE=load('Lockit_complex_PE','tools/analysis/pe.py');pe=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());parser=load('Lockit_complex_parser','tools/m4-crt-locale-batch-recovery/recover_v2.py');decoded=[]
 for r in sorted(rows.values(),key=lambda r:r['pc']):
  raw=bytes.fromhex(r['bytes']);offset,_=pe.rva_range(r['pc']-pe.image_base,len(raw));assert pe.data[offset:offset+len(raw)]==raw;decoded.append(parser.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0])))
 assert len(rows)==613 and sum(r['size']for r in rows.values())==1894 and len(new)==7
 register_calls=[r for r in read(front+'named-indirect-projections.json','82b8916469ffd08c4bc5affb051e892cd8f7e15db5876a71a5990e166c3b442e')if r['pc']in rows];assert len(register_calls)==9
 # Recover the exact literal request push despite intervening source MOVs.
 allocation=[]
 for site,push,role in((0x4ba306,0x4ba304,'conditional-shared-header'),(0x4ba33c,0x4ba32d,'container-sentinel'),(0x4bab32,0x4bab2c,'repeated-tree-node')):
  assert rows[push]['bytes']=='6a18'and rows[site]['mnemonic']=='call'and rows[site]['operands'].startswith('0x5abd26 ');allocation.append(dict(root=0x4b7f70,CALL_pc=site,return_pc=site+5,source_request=24,request_push_pc=push,request_push_hex='6a18',role=role,actual_executions=None,full_actual_native_backing_required=True,untouched_capacity_tail_required=True))
 assignments=[]
 for key,pc,pointer in((0,0x4b7df6,0x5e88cc),(1,0x4b7e32,0x5e88c4),(2,0x4b7e6c,0x5e88bc),(3,0x4b7ea2,0x5e88b4),(4,0x4b7ee0,0x5e88a8)):
  r=rows[pc];assert r['mnemonic']=='mov'and r['operands'].endswith(hex(pointer));off,_=pe.rva_range(pointer-pe.image_base,1);end=pe.data.index(b'\0',off);assignments.append(dict(key=key,store_PC=pc,field_offset=16,static_pointer=pointer,raw_string_hex=pe.data[off:end+1].hex(),raw_string=pe.data[off:end].decode('ascii'),heap_string_allocation_claimed=False))
 # Source tail entry below the nominal wrapper must have a physical dispatch.
 lower=min(r['pc']for r in graphs[0x4b7f80]['instructions']);assert lower==0x4b7d80
 pages=sorted({r['address']&~4095 for g in normal.values()for r in g['absolute_memory_references']if r['address']})
 plan=dict(root=0x4b7f70,slot=shape['slot'],registration=shape['registration'],source_object=0x60b2f8,shared_header=0x60b314,header_counter=0x60b318,physical_dispatch_entries=sorted(new)+[lower],lower_tail_entry=lower,retained_entries=sorted(set(normal)-set(new)),source_instruction_count=len(rows),physical_source_bytes=sum(r['size']for r in rows.values()),syntactic_MFC_sites=allocation,register_import_calls=register_calls,FS_source_sites=shape['FS_sites'],static_map_assignments=assignments,data_pages=pages,provider_reuse='Use four-root124 exact initialized source rows only after its acceptance; no cold/lazy path credit',runtime_obligations=['Observe header/counter NULL in actual original sequence BEFORE, then derive every repeated allocation through its exact MFC823 frame and request.', 'Derive all five ordered tree inserts, rotations, header/root/min/max links, count and color fields from one persistent source BEFORE; compare all object and every full owned backing byte including unwritten tails.', 'At all nine register CALLs prove the earlier raw IAT definition and every intervening callee nonvolatile preservation from actual prefix; project only named ctor/dtor target, leave source IAT DWORD unchanged.', 'Execute all reached nested normal 12B FS records and Lockit recursion with same native resource generation/thread; compare literal source and actual CPU/FX/API frames.', 'Lift eight physical dispatch entries at O0/O2, attribute all callbacks, then compare actual original/native125 schedules with96 prior callbacks plus this callback.', 'Run independent owning/import/state/recursion/FS rejection controls, bootstrap true BEFORE, positive owner teardown; publish root125 only when all executed receipts agree.'],initializers_admitted=0,original_execution_credit=False,native_execution_credit=False,candidate124_changed=False)
 def emit(name,value):
  p=out/name;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
 emit('game-normal-graphs.json',normal);emit('game-new-graphs.json',new);emit('instruction-contracts.json',dict(schema='mw34-complex-Lockit-static-v1',instructions=decoded,root=shape,lower_tail_entry=lower,register_import_calls=register_calls,source_data_pages=pages));emit('execution-plan.json',plan);pin(__file__)
 report=dict(passed=True,scope='Separate physical read-only/source plan for complex4B7F70; does not block or change candidate124',root=0x4b7f70,new_nominal_bodies=7,physical_dispatch_entries=8,rows=613,bytes=1894,register_import_CALLs=9,allocation_syntactic_sites=3,actual_allocation_count_known=False,initializers_admitted=0,files=PINS)
 emit('report.json',report);print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),rows=613,physical_bytes=1894,dispatch_entries=8)))
if __name__=='__main__':main(sys.argv[1])
