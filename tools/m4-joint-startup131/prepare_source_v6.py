"""Exact BEFORE-only two-DWORD TIB representation repair for reader5."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True)
 base=ROOT/'tools/m4-joint-startup131/mfc_source.py';snap=base.with_name('mfc_source_v3.py');reader=base.with_name('compare_provider_v5.py')
 assert sha(base)=='591bbc9cde5e23c12c51236f9c812031de2eedde8eb9c4d51c9947d14b060d07'
 assert sha(snap)=='8a51906ccc85f500c259b12b068d2ff38823ff7bce975a3c914e28b18eb079c4'
 text=base.read_text();changes=[]
 def one(old,new):
  nonlocal text
  assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new);changes.append(dict(before=old,after=new))
 old='  computed, source = self.literal.derive(state, fx, cpu, machine.memory, self.inputs, self.contracts)'
 new="""  original_layout={a:len(b)for a,b in machine.memory.items()};literal_memory=dict(machine.memory);tib_layout=[]
  if 0x7ffde004 in literal_memory and 0x7ffde008 in literal_memory and len(literal_memory[0x7ffde004])==len(literal_memory[0x7ffde008])==4:
   first=machine.bytes(0x7ffde004,4);second=machine.bytes(0x7ffde008,4);joined=first+second
   eq(joined,machine.bytes(0x7ffde004,8),'Exact computed TIB two-DWORD BEFORE join')
   literal_memory[0x7ffde004]=joined;del literal_memory[0x7ffde008]
   tib_layout=[dict(address=0x7ffde004,original_parts=[dict(address=0x7ffde004,bytes=4,BEFORE_hex=first.hex()),dict(address=0x7ffde008,bytes=4,BEFORE_hex=second.hex())],literal_extent=8,joined_BEFORE_hex=joined.hex(),candidate_BEFORE_seed=False)]
  eq({a:bytes(b)for a,b in literal_memory.items()if a not in(0x7ffde004,0x7ffde008)},{a:bytes(b)for a,b in machine.memory.items()if a not in(0x7ffde004,0x7ffde008)},'Every nonTIB pure source BEFORE region unchanged')
  computed, source = self.literal.derive(state, fx, cpu, literal_memory, self.inputs, self.contracts)"""
 one(old,new)
 one('  for address,b in computed.memory.items():machine.store_bytes(address,bytes(b))',"""  # Inverse projection into every original region preserves its exact extent.
  for address,size in original_layout.items():machine.store_bytes(address,computed.bytes(address,size))
  eq({a:len(b)for a,b in machine.memory.items()},original_layout,'Exact original persistent mapped-region layout restored')
  for row in tib_layout:
   row['source_AFTER_parts']=[dict(address=part['address'],bytes=4,source_AFTER_hex=computed.bytes(part['address'],4).hex())for part in row['original_parts']]
   row['source_AFTER_joined_hex']=computed.bytes(row['address'],8).hex();row['persistent_original_layout_restored']=True
  source['TIB_region_representation']=tib_layout""")
 layout=base.with_name('mfc_source_layout.py');assert not layout.exists();ast.parse(text);layout.write_text(text)
 text=snap.read_text();snapshot_changes=[]
 def snapshot_one(old,new):
  nonlocal text
  assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new);snapshot_changes.append(dict(before=old,after=new))
 snapshot_one('BOUNDARIES=(0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca)',"""layout_path=ROOT/'tools/m4-joint-startup131/mfc_source_layout.py'
assert hashlib.sha256(layout_path.read_bytes()).hexdigest()==LAYOUT_HASH
layout_spec=importlib.util.spec_from_file_location('joint131_mfc_exact_TIB_layout',layout_path)
L=importlib.util.module_from_spec(layout_spec);layout_spec.loader.exec_module(L)
BOUNDARIES=(0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca)""".replace('LAYOUT_HASH',repr(sha(layout))))
 snapshot_one('  super().__init__(preparation,pin);pin(parent)','  super().__init__(preparation,pin);pin(parent);pin(layout_path)')
 snapshot_one('  result=super().phase(machine,*args,**kwargs)',"  result=L.Extension.phase(self,machine,*args,**kwargs);machine._source_undefined_flags=dict(result['final_undefined_flags']);self.counts['MFC_defined_flag_consumers']+=len(result['defined_flag_consumers'])")
 snapshot_one("   M.M.need(len(owners)==1,'Exactly one computed BEFORE owner for every exported source requirement')\n   a,b=owners[0];selected[str(a)]=b.hex()", """   if not owners and (address,width)==(0x7ffde004,8) and len(memory.get(0x7ffde004,b''))==len(memory.get(0x7ffde008,b''))==4:
    selected[str(0x7ffde004)]=memory[0x7ffde004].hex();selected[str(0x7ffde008)]=memory[0x7ffde008].hex()
    M.M.eq(memory[0x7ffde004]+memory[0x7ffde008],bytes.fromhex(result['TIB_region_representation'][0]['joined_BEFORE_hex']),'Exact proof export original computed TIB parts')
   else:
    M.M.need(len(owners)==1,'Exactly one computed BEFORE owner for every exported source requirement')
    a,b=owners[0];selected[str(a)]=b.hex()""")
 target=base.with_name('mfc_source_v4.py');assert not target.exists();ast.parse(text);target.write_text(text)
 reader_text=reader.read_text();assert reader_text.count('import mfc_source_v3 as MF')==1;reader_text=reader_text.replace('import mfc_source_v3 as MF','import mfc_source_v4 as MF');new_reader=reader.with_name('compare_provider_v6.py');assert not new_reader.exists();ast.parse(reader_text);new_reader.write_text(reader_text)
 inputs=(Path(__file__),base,snap,reader,layout,target,new_reader,ROOT/'reports/m4-joint-startup131-source/combined-source-provider-r1/report.json')
 report=dict(passed=True,scope='Unexecuted exact adjacent TIB representation-only repair: computed BEFORE joins two DWORDs for pure phase; every original persistent region/byte projected back, unchanged source/equality coverage',parent_preparation=str(ROOT/'reports/m4-joint-startup131-source/preparation-r5/report.json'),parent_preparation_sha256=sha(ROOT/'reports/m4-joint-startup131-source/preparation-r5/report.json'),retained_failure=str(inputs[-1]),retained_failure_sha256=sha(inputs[-1]),tool=str(new_reader),layout_changes=changes,snapshot_changes=snapshot_changes,reader_changes=[dict(before='import mfc_source_v3 as MF',after='import mfc_source_v4 as MF')],files={str(p.resolve()):sha(p)for p in inputs},normalized_span=[0x7ffde004,8],original_spans=[[0x7ffde004,4],[0x7ffde008,4]],nonTIB_memory_change=False,persistent_original_layout_restored=True,candidate_AFTER_machine_seed=False,per_phase_BEFORE_machine_seed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
