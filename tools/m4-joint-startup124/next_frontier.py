"""Physical original-table lookahead after accepted124; static evidence only."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main(acceptance_path,acceptance_sha256,name):
 out=ROOT/'reports/m4-joint-startup124-root'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(path,expected=None):
  path=Path(path).resolve();actual=sha(path);assert expected is None or expected==actual
  assert str(path) not in pins or pins[str(path)]==actual;pins[str(path)]=actual;return path
 spec=importlib.util.spec_from_file_location('frontier_PE',pin(ROOT/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
 pe=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 table=[dict(slot=address,entry=pe.rva_u32(address-pe.image_base)) for address in range(0x5e0000,0x5e0244,4)]
 table=[row for row in table if row['entry']];assert len(table)==144
 acceptance=json.loads(pin(acceptance_path,acceptance_sha256).read_bytes())
 assert acceptance['passed'] is True and acceptance['connected_roots']==124 and acceptance['whole_M4_complete'] is False
 candidate=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25').read_bytes())
 selected=candidate['selected_order'];entries={r['entry'] for r in selected}
 assert len(entries)==len(selected)==124 and all(row in table for row in selected)
 classification=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/root-classification.json').read_bytes())
 inventory={r['entry']:r for r in classification['roots']};assert len(inventory)==144
 remaining=[inventory[row['entry']] for row in table if row['entry'] not in entries];assert len(remaining)==20
 graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 physical={}
 for root in remaining:
  assert any(row['entry']==root['entry'] and row['slot']==root['slot'] for row in table)
  for entry in root['local_entries']:
   for row in graphs[str(entry)]['instructions']:
    pc=row['pc'];raw=bytes.fromhex(row['bytes']);offset,_=pe.rva_range(pc-pe.image_base,len(raw));assert pe.data[offset:offset+len(raw)]==raw
    assert pc not in physical or physical[pc]==raw;physical[pc]=raw
 groups=collections.defaultdict(list)
 for root in remaining:groups[tuple(root['imports'])].append(root['entry'])
 counts=dict(remaining_roots=20,roots_with_FS_sites=sum(bool(r['FS_sites']) for r in remaining),roots_with_unresolved_controls=sum(bool(r['unresolved_controls']) for r in remaining),roots_with_FP_sites=sum(bool(r['FP_sites']) for r in remaining),unique_physical_instruction_rows=len(physical),unique_physical_instruction_bytes=sum(map(len,physical.values())))
 (out/'remaining-roots.json').write_text(json.dumps(remaining,indent=2)+'\n');pin(out/'remaining-roots.json');pin(__file__)
 result=dict(passed=True,scope='Exact original144 table minus accepted124, every remaining static closure byte checked; reached-path/provider execution contracts remain required',counts=counts,service_groups=[dict(imports=list(key),count=len(value),roots=value) for key,value in sorted(groups.items(),key=lambda row:(-len(row[1]),row[0]))],priority='Continue separately recovered4B7F70 tree: genuine allocation occurrences/capacities, source node links/rotations, nine register-import carries, source-owned node cleanup; then remaining graph/service and numerical families.',native_executed=False,original_executed=False,initializer_credit=0,whole_M4_complete=False,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),counts=counts)))

if __name__=='__main__':main(*sys.argv[1:])
