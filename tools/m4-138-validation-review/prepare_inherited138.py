"""Immutable original-only current138 inherited source adapters; no raw reader."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];OUT=R/'reports/m4-startup138-original/inherited-source-preparation-r2';FILES={};changes=[]
def pin(path,h=None):
 path=Path(path).resolve();assert path.suffix.lower()not in('.mwb','.zip','.mwi')and path.name not in('index.json','payload.bin','transport.json')
 assert path.stat().st_size<=32*1024*1024
 with path.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
 assert h is None or h==v,(path,h,v);FILES[str(path)]=v;return path
def read(path,h=None):return json.loads(pin(R/path,h).read_text(encoding='utf-8-sig'))
V='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181';P='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2';B='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69';Q='efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a'
previous=read('reports/m4-startup131-original/inherited-source-preparation-r3/report.json')
for p,h in previous['files'].items():pin(p,h)
old=read('reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
prep=read('reports/m4-startup138-original/preparation-r7/report.json',P);validation=read('reports/m4-startup138-original/original-validation-r2/report.json',V)
build=read('reports/m4-startup138-original/build-r4/build.json',B);review=read('reports/m4-tree-review/original138-prelaunch-r5/report.json',Q)
mfc=read('reports/m4-startup138-original/mfc-source-r1/report.json','e320179826dc0d0ab6033e98502eb5706186afa235222dd906d67c7d9605180f')
assert all(p['passed']for p in(previous,old,prep,validation,build,review,mfc))
assert validation['reader_closed']and validation['paired_export_readers_closed']and validation['counts']['phases']==828and validation['combined_pages']==69and validation['callbacks']==108
assert build['preparation_sha256']==P and review['build_sha256']==B
newroots={0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0}
assert [row for row in prep['selected_order']if row['entry']not in newroots]==old['selected_order']and len(prep['selected_order'])==138
assert prep['observed_pages']==old['observed_pages']and len(prep['observed_pages'])==43
assert len(prep['extra_whole_source_pages'])==26and set(old['extra_whole_source_pages'])<=set(prep['extra_whole_source_pages'])and len(set(prep['observed_pages']+prep['extra_whole_source_pages']))==69
key=lambda row:(row['pc'],row['size'],row['image_offset'],row.get('origin',0))
oldspans={key(row)for row in old['source_spans']};newspans={key(row)for row in prep['source_spans']}
assert len(oldspans)==3980and len(newspans)==5040and oldspans<=newspans
treephase=next(i for i,row in enumerate(prep['selected_order'])if row['entry']==0x4b7f70);assert treephase==83
for path in ('reports/m4-startup138-original/preparation-r7/spec.hpp','reports/m4-startup138-original/preparation-r7/selected-order.json','reports/m4-startup138-original/build-r4/original-worker.exe','reports/m4-tree-review/original138-prelaunch-r5/compiled-observers.json'):
 full=R/path;h=review['files'].get(str(full))or prep['files'].get(str(full));pin(full,h)
export=validation['paired_exports'];assert len(export)==1and export[0]['branch']=='original'
for field,identity in(('index_path','index_sha256'),('payload_path','payload_sha256')):
 path=Path(export[0][field]);assert validation['files'][str(path)]==export[0][identity]and path.is_file()
assert Path(export[0]['payload_path']).stat().st_size==export[0]['payload_bytes']==1482491611
common=[('m4-startup131-original','m4-startup138-original'),('9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f',V),('1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb',P),('f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d',B),('e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed',Q),('original131-prelaunch-r4','original138-prelaunch-r5'),('current131','current138'),('original131','original138'),('Current131','Current138'),('across131 phases','across138 phases'),('whole46-page BEFORE','whole69-page BEFORE'),('all46 current source pages','all69 current source pages')]
generated={}
for name in('current_inherited_source_v2.py','format_source_v4.py','tree_source.py','old4_source.py','export_reader.py'):
 parent=R/'tools/m4-startup131-original'/name;original=pin(parent).read_text();text=original;deltas=[];operations=[]
 def replace(a,z,required=True):
  global text
  n=text.count(a)
  if required:assert n>0,(name,a)
  if n:
   deltas.append(dict(before=a,after=z,occurrences=n));positions=[];start=0
   while True:
    index=text.find(a,start)
    if index<0:break
    positions.append(index);start=index+len(a)
   for index in reversed(positions):
    text=text[:index]+z+text[index+len(a):];operations.append(dict(offset=index,before=a,after=z))
 for a,z in common:replace(a,z,False)
 if name!='export_reader.py':replace('m4-startup138-original/validation-r2','m4-startup138-original/original-validation-r2',False)
 if name=='current_inherited_source_v2.py':
  replace('inherited-source-preparation-r3','inherited-source-preparation-r2')
  replace("validation['counts']['phases']==786","validation['counts']['phases']==828 and validation['record_bytes']==356992 and validation['combined_pages']==69 and validation['callbacks']==108 and validation['original_executed'] and not validation['native_executed']")
  replace("derived['phase']==79","derived['phase']==83");replace('phase=79','phase=83')
  replace('m4-startup138-original/source-r2','m4-startup138-original/mfc-source-r1')
  replace('203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910','e320179826dc0d0ab6033e98502eb5706186afa235222dd906d67c7d9605180f')
 if name=='tree_source.py':replace('tree_phase==79','tree_phase==83')
 if name=='old4_source.py':
  replace('m4-startup138-original/preparation-r4','m4-startup138-original/preparation-r7');replace('m4-startup138-original/build-r3','m4-startup138-original/build-r4')
  replace("len(p['order'])==131","len(p['order'])==138")
  replace("extra_pages==[0x5cd000,0x5e3000,0x5e9000]","len(extra_pages)==26 and len(set(pages+extra_pages))==69 and {0x5cd000,0x5e3000,0x5e9000}<=set(extra_pages)")
  replace('Three complete physical additional source pages','All26 complete physical additional source pages, retaining inherited three')
  replace('and43 fixed pages plus3 external whole pages','and43 fixed pages plus26 external whole pages')
 for child in ('format_source_v4.py','tree_source.py','old4_source.py','export_reader.py'):
  replace('tools/m4-startup138-original/'+child,'tools/m4-startup138-original/'+child.removesuffix('.py')+'_r2.py',False)
 inverse=text
 for delta in reversed(operations):
  index=delta['offset'];assert inverse[index:index+len(delta['after'])]==delta['after']
  inverse=inverse[:index]+delta['before']+inverse[index+len(delta['after']):]
 assert inverse==original
 ast.parse(text)
 target=R/'tools/m4-startup138-original'/(name.removesuffix('.py')+'_r2.py');assert not target.exists();target.write_text(text);pin(target)
 generated[name]=str(target);changes.append(dict(parent=str(parent),parent_sha256=FILES[str(parent)],target=str(target),target_sha256=FILES[str(target)],exact_inverse_restores_parent=True,deltas=deltas,operations=operations))
pin(__file__);pin(sys.executable);assert not OUT.exists();OUT.mkdir(parents=True)
delta=OUT/'adapter-deltas.json';delta.write_text(json.dumps(changes,indent=2)+'\n');pin(delta)
report=dict(passed=True,scope='Prepared current138 inherited131 source comparers, retaining every literal operand/API/normalization/byteflow gate; whole source69 inputs and exact old131 physical spans retained',counts=dict(inherited_source_spans=3980,current_source_spans=5040,inherited_roots=131,current_roots=138,tree_phase=83,original_phases=828,source_pages=69),exact_inverse_restores_parents=True,generated=generated,original_validation_sha256=V,source_model_execution_performed=False,capture_reader_opened=False,source_comparison_executed=False,raw_export_reader_opened=False,raw_export_index_opened=False,raw_export_report=str(R/'reports/m4-startup138-original/original-validation-r2/report.json'),raw_export_report_sha256=V,combined_native_source_report_required_by_original_checker=False,combined_native_semantic_gate_remains_separate=True,initializer_credit=0,files=FILES)
path=OUT/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),generated=generated,pins=len(FILES))))
