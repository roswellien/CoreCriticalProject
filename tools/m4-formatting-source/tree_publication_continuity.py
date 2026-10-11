"""Bound the unchanged accepted tree publication implementation without captures."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 accepted=pin(ROOT/'reports/m4-tree-native/preparation-r5/report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2')
 current=pin(ROOT/'reports/m4-formatting-native/preparation-r18/report.json','68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06')
 a=json.loads(accepted.read_bytes());b=json.loads(current.read_bytes());assert a['passed'] and b['passed']
 source=pin(accepted.parent/'tree_operations.inc');dest=pin(current.parent/'tree_operations.inc');assert source.read_bytes()==dest.read_bytes();text=source.read_text()
 assert 'Binding::tree_publish'not in text and 'Binding::tree_owner_after'in text
 assert '++r->words[23]'in text and '++tree_publication_cursor_'in text and 'fs_publications_.push_back'in text
 for pc in('0x4ba315','0x4ba347','0x4bab9c','0x4babac'):assert pc in text
 pin(ROOT/'tools/m4-tree-native/tree_operations_v5.inc');assert source.read_bytes()==(ROOT/'tools/m4-tree-native/tree_operations_v5.inc').read_bytes()
 pin(ROOT/'tools/m4-tree-source/final_observer125_v2.py');pin(ROOT/'tools/m4-tree-source/compare_provider125_v4.py');pin(__file__)
 report=dict(passed=True,scope='Native18 preserves accepted tree5 whole implementation; publication is part of tree_owner_after, not a separate tree_publish symbol',accepted_preparation=str(accepted),current_preparation=str(current),implementation_sha256=sha(source),physical_publication_PCs=[0x4ba315,0x4ba347,0x4bab9c,0x4babac],source_obligations=['actual current child generation and allocation CALL','actual live parent generation and source branch edge','seven ordered role/parent/global publication tuples','one words23 commit for each actual occurrence','complete16Q publication private rows from literal source'],current130_provider_gate_required=True,runtime_claim=False,capture_reader_opened=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
