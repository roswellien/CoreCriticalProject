"""Exact static mixed-format root; observations and credit remain separate."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh static recovery');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical input '+str(p));pins[str(p)]=v;return p
 def load(p,h=None):return json.loads(pin(ROOT/p,h).read_bytes())
 def emit(n,v):
  p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p);return p
 accepted=load('reports/m4-joint-startup125-root/acceptance-r2/report.json','856ba8bd458e178f4a9afd91ff24299becc4debef76ee17c359da0f741165d51');need(accepted['passed'],'Actual accepted125')
 frontier=load('reports/m4-joint-startup124-root/next-frontier-r1/remaining-roots.json');r=next(x for x in frontier if x['entry']==0x4e1ca0);need(r['slot']==0x5e01d4,'Physical144 frontier mixed slot')
 allgraphs=load('reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a');graphs={e:allgraphs[str(e)]for e in r['local_entries']};need(len(graphs)==12 and not any(g['unresolved_controls']or g['FP_sites']for g in graphs.values()),'Twelve physically decoded closed integer graphs')
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());rows={x['pc']:x for g in graphs.values()for x in g['instructions']};need(len(rows)==348,'Complete unique348 source rows')
 p=pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py');s=importlib.util.spec_from_file_location('mixed_contract_parser',p);parser=importlib.util.module_from_spec(s);s.loader.exec_module(parser);decoded=[]
 for x in sorted(rows.values(),key=lambda x:x['pc']):
  b=bytes.fromhex(x['bytes']);off,_=game.rva_range(x['pc']-game.image_base,len(b));need(game.data[off:off+len(b)]==b,'Every exact source opcode '+hex(x['pc']));mn=x['mnemonic'];op=x['operands'].split(' <')[0];repeat=None
  if mn in('rep','repe','repz','repne','repnz'):repeat=mn;mn,op=op.split(None,1)
  row=dict(pc=x['pc'],width=x['size'],bytes_hex=x['bytes'],mnemonic=mn,operands=op)
  if repeat:row['repeat']=repeat
  decoded.append(parser.instruction_contract(row))
 filename=0x5e97dc;off,_=game.rva_range(filename-game.image_base,16);v=game.data[off:off+16].split(b'\0')[0];need(v==b'valves','Exact literal filename')
 frames=[dict(root=0x4e1ca0,entry=0x4e2190,handler=0x5b90fb,read=0x4e2197,install=0x4e219e,saved=0x4e22bd,restore=0x4e22cd,ret=0x4e22d8,ret_cleanup=0,bytes=12),dict(root=0x4e1ca0,entry=0x4e5290,handler=0x5b956c,read=0x4e5297,install=0x4e529e,saved=0x4e538f,restore=0x4e539d,ret=0x4e53a8,ret_cleanup=16,bytes=12)]
 allocations=[dict(root=0x4e1ca0,CALL_pc=pc,request=request,role=role,return_pc=pc+5,actual_count_unknown=True)for pc,request,role in[(0x49cc8d,12,'inner-list-sentinel'),(0x4e5325,24,'conditional-shared-header'),(0x4e535b,24,'outer-list-sentinel')]]
 lockcalls=[dict(root=0x4e1ca0,CALL_pc=pc,return_pc=pc+6,IAT=slot,target=target,scratch_LEA_pc=lea,derived_scratch='outer-frame +44',actual_boundary_unknown=True)for pc,slot,target,lea in[(0x4e530f,0x5bb4f8,0x7810a290,0x4e52fa),(0x4e5389,0x5bb4f4,0x7810a350,0x4e537d)]]
 root=dict(entry=0x4e1ca0,slot=0x5e01d4,wrapper=0x4e1cb0,constructor=0x4e5290,base_constructor=0x4de9c0,object=0x60b668,object_extent=264,filename=filename,filename_bytes_hex=(v+b'\0').hex(),owned_pointer_field=0x60b66c,formatting_default_output='valves.zrd',formatting_default_request=11,registration=dict(CALL_pc=0x4e1cd5,callback=0x4e1ce0),header=0x60b7d4,counter=0x60b7d0,sentinel_field=0x60b764,inner_sentinel_field=0x60b750,source_strdup_calls=5,source_strdup_actual_reached=False,normal_null_string_arguments_derived=True,actual_MFC_calls_unknown=True,callbacks_executed=False)
 emit('game-normal-graphs.json',graphs);emit('instruction-contracts.json',dict(instructions=decoded,FS_frame_contracts=frames,roots=[root],allocations=allocations,Lockit_calls=lockcalls));emit('roots.json',[root]);emit('FS-frame-contracts.json',frames);emit('allocation-contracts.json',allocations);emit('Lockit-call-contracts.json',lockcalls);pin(__file__)
 report=dict(passed=True,scope='Exact mixed root4E1CA0 physical source; static predictions are not observations',game_entries=len(graphs),unique_instructions=len(rows),unique_bytes=sum(x['size']for x in rows.values()),root=root,normal_FS_frames=2,MFC_static_sites=3,Lockit_static_sites=2,formatting_provider_same_source=True,formatting_normal_format='%s%s',normal_filename='valves',native_executed=False,original_executed=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),instructions=len(rows))))
if __name__=='__main__':main(sys.argv[1])
