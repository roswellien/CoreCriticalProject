"""Derive a fresh audit of120 paired physical observer/page relations."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent;ROOT=HERE.parents[1]
s=(ROOT/'tools/m4-joint-startup116/paired_audit_v2.py').read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one('def main(paired_path,name):','def main(paired_path,compiled_path,compiled_sha,build_path,build_sha,prep_path,prep_sha,name):')
s=s.replace('reports/m4-joint-startup116-root','reports/m4-joint-startup120-root').replace('1392','1440').replace('paired116','paired120')
one("contract=read(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json')","contract=read(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108')\n container_contract=read(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json','3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d')")
one("len(order)==116,'Exact selected116 order'","len(order)==120,'Exact selected120 order'")
one("cinstructions={x['pc']:x for x in contract['instructions']};container_fields=[];container_roots={x['entry']:x for x in contract['roots']}","cinstructions={x['pc']:x for x in container_contract['instructions']};container_fields=[];container_roots={x['entry']:x for x in container_contract['roots']}")
one("compiled=read(ROOT/'reports/m4-container-review/observer-compiled-r3/report.json','9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59')","compiled=read(compiled_path,compiled_sha)")
one("need(compiled['passed'] and compiled['counts']['compiled_FS_trampolines']==30,'Compiled transparent original observer')","need(compiled['passed'],'Compiled transparent original observer')")
one("build=read(ROOT/'reports/m4-container-source/original-build-r2/build.json','8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541')","build=read(build_path,build_sha)\n prep=read(Path(prep_path)/'report.json',prep_sha)")
one("bindings={x['PC']:x for x in read(ROOT/'reports/m4-container-source/original-preparation-r2/fs-hook-bindings.json')}","bindings={x['PC']:x for x in read(Path(prep_path)/'fs-hook-bindings.json')}\n need(compiled['counts']['compiled_FS_trampolines']==len(bindings),'Every final linked transparent FS observer accounted for')")
one("need([(x['PC'],x['width']) for x in observer_spans]==[(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only three exact observed-page spans,20 source bytes')","expected_spans=sorted((x['PC'],len(bytes.fromhex(x['raw_bytes']))) for x in bindings.values() if x['PC']&~4095 in prep['observed_pages'])\n need(sorted((x['PC'],x['width']) for x in observer_spans)==expected_spans,'Exactly all physical FS hook spans on observed pages')\n span_bytes=sum(width for pc,width in expected_spans)")
one("need(len(observer_bytes)==20,'Exactly20 source-bound observer bytes')","need(len(observer_bytes)==span_bytes,'Every source-bound observer byte')")
one("len(row['nonstack_pages'])==70,'35 ordinary entire nonstack pages on both sides; loader page relation is separate'","len(row['nonstack_pages'])==76,'38 ordinary entire nonstack pages on both sides; loader page relation is separate'")
one('compiled20byte original observer spans','complete compiled original observer spans')
one('exact_original_observer_spans=3,exact_original_observer_bytes=20','exact_original_observer_spans=len(expected_spans),exact_original_observer_bytes=span_bytes')
one('main(sys.argv[1],sys.argv[2])','main(*sys.argv[1:])')
p=HERE/'paired_audit.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
print('Generated additive120 paired_audit.py')
