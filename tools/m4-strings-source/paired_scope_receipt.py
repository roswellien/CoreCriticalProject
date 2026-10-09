"""Correct inherited54 prose around unchanged passing selected71 comparisons."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-strings-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive scope receipt');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact immutable paired evidence');files[str(p)]=v;return p
 parent=BASE/'paired-initialization-policy-r2/report.json';old=json.loads(pin(parent,'1f454d420cb4bad8ec8cbe6aa0466fc4b516aa71abc1236afa53e6f5210ce047').read_bytes());need(old['passed'] and old['counts']['paired_phases']==852,'Actual passing71 evidence');files.update(old['files'])
 contract=json.loads(pin(BASE/'recovery-r7/instruction-contracts.json','e1a4a4e2a6f1d55b5a1a94b10254202e88304e67dfbedd77326e72f0986e97a9').read_bytes());order=contract['selected_order'];spi=next(i for i,r in enumerate(order)if r['entry']==0x482cf0)
 graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes());nextfp=next(i for i,r in enumerate(order)if i>spi and graphs[str(r['entry'])]['FP_sites']);need((spi,nextfp)==(38,44),'Source/table-derived finite SPI metadata interval')
 pointer_fields=[r['objects'][0]['address']+4 for r in contract['roots']if r['string']['actual_strdup_called']];need(len(pointer_fields)==16,'16 source-established actual duplication fields')
 new=dict(old);new.update(scope='Bounded selected71 initialization relation against fresh genuine original71: entire31 nonstack game pages, literal43-callback order and atexit success return, exact numeric hardware FX projection, finite source/table-derived SPI metadata interval, backed by strict persistent native source State/CPU/FX/ENV/full32gamepages',metadata_parent=str(parent),metadata_parent_sha256=sha(parent),metadata_correction_only=True,comparisons_rerun=False,comparison_algorithm_changed=False,source_duplicate_pointer_fields=pointer_fields,source_duplicate_pointer_relation='Each branch literal constructor establishes its own actual live allocation pointer; genuine original HeapAlloc result and native owned-allocation witness authenticate those identities. Entire four-byte fields carry unchanged throughout subsequent roots. Raw observations are retained.',crossbranch_numeric_contract='Frozen hardwarefx capability-mask projection only; exact CW/TOP/status/raw80/SIMD all phases. Exact ENV head throughout; actual SPI FIP/FOP/FDP metadata retained on source/table-derived AFTER phases38..43 and BEFORE39..44 until source FP overwrites it. Exact complete ENV otherwise.',SPI_metadata_AFTER_phases=list(range(spi,nextfp)),SPI_metadata_BEFORE_phases=list(range(spi+1,nextfp+1)),cached_HeapSize_capacity_relation='Successful original source realloc resets native cached capacity to0; zero accepted only after actual growth and backed by independent exact committed-owner extent proof. Next genuine msize establishes fresh actual capacity.',native_private_owned_allocation_page_comparison='Separate independent provider/lifecycle review gate; this paired receipt compares game initialization pages and declared owned identities, not original allocator padding.',files=files)
 pin(__file__);new['files']=files;(out/'report.json').write_text(json.dumps(new,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),metadata_only=True)))
if __name__=='__main__':main(sys.argv[1])
