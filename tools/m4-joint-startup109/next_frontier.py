"""Physical-table lookahead after candidate109; static planning earns no credit."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup109-root'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 spec=importlib.util.spec_from_file_location('frontier_PE',pin(ROOT/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
 pe=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 table=[dict(slot=a,entry=pe.rva_u32(a-pe.image_base))for a in range(0x5e0000,0x5e0244,4)];table=[r for r in table if r['entry']]
 assert len(table)==144
 candidate=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes());selected=candidate['selected_order'];assert len(selected)==109
 entries={r['entry']for r in selected};assert len(entries)==109 and all(r in table for r in selected)
 classification=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/root-classification.json').read_bytes());inventory={r['entry']:r for r in classification['roots']};assert len(inventory)==144
 remaining=[inventory[r['entry']]for r in table if r['entry']not in entries];assert len(remaining)==35
 graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 checked={}
 for root in remaining:
  assert any(t['entry']==root['entry']and t['slot']==root['slot']for t in table)
  for entry in root['local_entries']:
   for row in graphs[str(entry)]['instructions']:
    pc=row['pc'];raw=bytes.fromhex(row['bytes']);off,_=pe.rva_range(pc-pe.image_base,len(raw));assert pe.data[off:off+len(raw)]==raw
    assert pc not in checked or checked[pc]==raw;checked[pc]=raw
 groups=collections.defaultdict(list)
 for root in remaining:groups[tuple(root['imports'])].append(root['entry'])
 metrics=dict(remaining_roots=35,roots_with_FS_sites=sum(bool(r['FS_sites'])for r in remaining),roots_with_unresolved_controls=sum(bool(r['unresolved_controls'])for r in remaining),roots_with_FP_sites=sum(bool(r['FP_sites'])for r in remaining),unique_physical_instruction_rows=len(checked),unique_physical_instruction_bytes=sum(map(len,checked.values())))
 pin(__file__);(out/'remaining-roots.json').write_text(json.dumps(remaining,indent=2)+'\n');pin(out/'remaining-roots.json')
 report=dict(passed=True,scope='Exact original144-entry table minus candidate109, checked against physically unchanged static closure bytes; pending109 acceptance and fresh reached-path contracts',counts=metrics,service_groups=[dict(imports=list(k),count=len(v),roots=v)for k,v in sorted(groups.items(),key=lambda kv:(-len(kv[1]),kv[0]))],priority='Recover normal FS exception-chain setup/teardown shared by remaining constructors, while preserving unsupported exception dispatch and handler branches. Then route reached new providers, original startup scheduler/environment/mainargs and native menu entry.',candidate109_accepted_by_this_report=False,native_executed=False,original_executed=False,initializer_credit=0,whole_M4_complete=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=metrics)))
if __name__=='__main__':main(sys.argv[1])
