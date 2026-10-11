"""Pure exact two-DWORD TIB join/inverse equivalence; no archive inputs."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
parent=ROOT/'tools/m4-joint-startup131/preflight_source_v2.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='579c21eda5402d260d48a13a5c10df281aab75813ac9b21155bdc7e53804185d'
text=parent.read_text().replace('mfc_source_v2.py','mfc_source_v4.py')
old="  (out/'pure-model-equivalence.json').write_text"
new="""  # This artificial target transport is an independent frozen old-model
  # result, not a native capture. Only representation equivalence is claimed.
  split=dict(memory);split[0x7ffde004]=memory[0x7ffde004][:4];split[0x7ffde008]=memory[0x7ffde004][4:]
  class Carried(I.Machine):
   def projected_cpu(self):return e.literal.Literal.cpu_now(self)
   def bytes(self,address,size):
    if (address,size)==(0x7ffde004,8):return super().bytes(address,4)+super().bytes(address+4,4)
    return super().bytes(address,size)
  carrier=Carried(bytes(state),raw[116:628],struct.pack('<10I',*cpu),split,program={},callbacks={});carrier.initial_flags=cpu[8];layout_before={k:len(v)for k,v in carrier.memory.items()}
  regions=[(o['new'],o['extent'],3)for o in preparation['inputs']['role_owners']]+[(0x5f4cb000,4096,3),(preparation['inputs']['guest_CS'],24,3),(0x7ffdee1c,4,3),(0x78037000,4096,3),(0x7ffde000,4,3),(0x7ffde004,8,1),(0x7ffde018,4,1)]
  transport={'before/State.bin':bytes(state),'before/CPU.bin':struct.pack('<10I',*cpu),'before/FX.bin':raw[116:628],'before/memory/index.bin':b''.join(struct.pack('<3I',*v)for v in regions),'after/memory/index.bin':b''.join(struct.pack('<3I',*v)for v in regions),'after/accesses.bin':b''.join(struct.pack('<IIQII',*v)for v in a.accesses),'after/State.bin':bytes(a.state),'after/CPU.bin':struct.pack('<10I',*a.cpu_now()),'after/FX.bin':a.fx}
  for address,size,_ in regions:transport[f'before/memory/{address}.bin']=carrier.bytes(address,size);transport[f'after/memory/{address}.bin']=a.bytes(address,size)
  transport['after/import-projections.bin']=b''.join(struct.pack('<6I',v['access_index'],v['PC'],v['cell'],v['raw'],v['projected'],0)for v in a.projections)
  APIs=[]
  for i,r in enumerate(ar['source_API_relations']):
   spec=r['spec'];w=[1,i,spec['source_PC'],r['target'],spec['argc'],r['CPU_before'][4],spec['return_PC'],r['typed_result'],1252 if i==2 else 0x12345000,0x1234,0,0x12345000,preparation['inputs']['role_owners'][1]['new'],r['CS_depth_after'],0,0]
   def synthetic_CS(depth):
    result=bytearray(40);struct.pack_into('<I',result,12,depth);struct.pack_into('<Q',result,16,0x1234 if depth else 0);return bytes(result)
   APIs.append(struct.pack('<16Q',*w)+struct.pack('<10I',*r['CPU_before'])+struct.pack('<10I',*r['CPU_after'])+bytes.fromhex(r['frame64_hex'])+synthetic_CS(r['CS_depth_before'])+synthetic_CS(r['CS_depth_after']))
  transport['after/APIs.bin']=b''.join(APIs)
  class Synthetic:
   def data(self,key):return transport[key.removeprefix('sequence-0/MFC/')]
  e.resource=lambda *args,**kwargs:None
  result=e.phase(carrier,Synthetic(),'synthetic-pure-model',0,13)
  assert carrier.state==a.state and carrier.fx==a.fx and carrier.projected_cpu()==a.cpu_now() and {k:len(v)for k,v in carrier.memory.items()}==layout_before
  assert all(carrier.bytes(k,len(v))==a.bytes(k,len(v))for k,v in split.items())
  assert len(result['TIB_region_representation'])==1 and result['TIB_region_representation'][0]['persistent_original_layout_restored']
  assert [r['PC']for r in result['source_normal_boundaries']]==list(M.BOUNDARIES) and result['source_computed_BEFORE']['memory'][str(0x7ffde004)]==split[0x7ffde004].hex() and result['source_computed_BEFORE']['memory'][str(0x7ffde008)]==split[0x7ffde008].hex()
  q=out/'pure-TIB-layout-equivalence.json';q.write_text(json.dumps(dict(witness=result['TIB_region_representation'],original_region_inventory=layout_before,source_normal_boundaries=result['source_normal_boundaries'],synthetic_transport=True,native_API_lifecycle_or_phase_claim=False),indent=2)+'\\n');pin(q)
  (out/'pure-model-equivalence.json').write_text"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('pin(__file__);pin(sys.executable)',"pin(ROOT/'tools/m4-joint-startup131/preflight_source_v5.py');pin(ROOT/'tools/m4-joint-startup131/preflight_source_v2.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
