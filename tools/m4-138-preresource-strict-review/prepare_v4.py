"""Own Native BEFORE page inputs and accepted typed first TLS API source joins."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/preparation-r4';assert not out.exists();out.mkdir()
 parent=R/'reports/m4-138-preresource-strict-review/preparation-r3/verify_case_v3.py';s=parent.read_text();d=[]
 def change(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);d.append(dict(before=a,after=b))
 insertion="""      own=a.data(prefix+'entry/Native.bin');eq(len(own),159716,'Whole actual own root BEFORE input');eq(own[36:76],entry_cpu,'Own entry Native CPU cut');eq(own[141540:145044],entry_state,'Own entry Native State cut')
      own_pages=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
      for j,address in enumerate(own_pages):
       data=own[2276+j*4096:2276+(j+1)*4096];eq(len(data),4096,'Whole own actual entry BEFORE page')
       for base,payload in memory.items():
        lo=max(base,address);hi=min(base+len(payload),address+4096)
        if lo<hi:eq(payload[lo-base:hi-base],data[lo-address:hi-address],'Every own BEFORE overlapping source input agrees')
       if address not in memory:memory[address]=data
      # Fill absent code/IAT inputs only from the fixed physical source image;"""
 change('      # Fill absent code/IAT inputs only from the fixed physical source image;',insertion)
 api="""       relation=derived['source_API_relations'][0];spec=relation['spec'];rec=a.data(prefix+'refused/APIs.bin');w=struct.unpack_from('<16Q',rec)
       eq(w[:8],(1,0,spec['source_PC'],relation['target'],spec['argc'],relation['CPU_before'][4],spec['return_PC'],relation['typed_result']),'Exact current source TLS target/order/args/return/result')
       eq(struct.unpack_from('<10I',rec,128),tuple(relation['CPU_before']),'Whole source-derived actual API entry CPU40');eq(struct.unpack_from('<10I',rec,168),tuple(relation['CPU_after']),'Whole source-derived actual API return CPU40')
       eq(rec[208:272].hex(),relation['frame64_hex'],'All64 actual source API frame bytes');eq(w[12],p['inputs']['role_owners'][1]['new'],'Exact guest thread role');eq(w[13],relation['CS_depth_after'],'Exact source semantic lock depth')
       eq(V.cs(rec[272:312]),(relation['CS_depth_before'],w[9]if relation['CS_depth_before']else 0),'Whole native CS40 incoming depth/owner');eq(V.cs(rec[312:352]),(relation['CS_depth_after'],w[9]if relation['CS_depth_after']else 0),'Whole native CS40 outgoing depth/owner');eq(w[8],w[11],'Actual TLS lookup returns current owned native association')
       counts['whole_source_API_CPU40_frame64_joins']+=1"""
 target="eq(API_count,1,'One complete TLS source API before controlled store/transport denial')";change(target,target+'\n'+api)
 inverse=s
 for h in reversed(d):assert inverse.count(h['after'])==1;inverse=inverse.replace(h['after'],h['before'])
 assert inverse==parent.read_text();ast.parse(s);q=out/'verify_case_v4.py';q.write_text(s);(out/'exact-deltas.json').write_text(json.dumps(d,indent=2)+'\n')
 physical=R/'reports/m4-joint-startup138/preparation-r4/joint_protocol.hpp';body=physical.read_text();assert 'sizeof(Common)==141540&&sizeof(Native)==159716'in body and 'std::array<std::uint32_t,17> pages'in body
 files={str(p):sha(p)for p in(parent,q,Path(__file__),out/'exact-deltas.json',physical,R/'tools/m4-joint-startup131/mfc_source.py')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted own actual Native root-entry BEFORE17page source input plus accepted finite TLS API fullCPU40/frame64/current native CS ownership joins',whole_parent_inverse=True,exact_hunks=2,source_AFTER_seed=False,partial_CPU_mask=False,worker_executed=False,actual_strict_checker_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
