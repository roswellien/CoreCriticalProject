"""Exact current compiled import targets/raw image cells and six MFC domains."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  sp=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 d=load('entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');pe=load('image',R/'tools/analysis/pe.py');image=pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());sp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(sp.read_bytes());assert gate['passed']and gate['reader_closed'];vr=pin(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');val=json.loads(vr.read_bytes());review=pin(R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json','eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c');reviewgate=json.loads(review.read_bytes());assert reviewgate['passed']and reviewgate['preparation_sha256']==val['preparation_sha256']and reviewgate['build_sha256']==val['build_sha256'];compiled=json.loads(pin(review.parent/'compiled-observers.json',reviewgate['files'][str((review.parent/'compiled-observers.json').resolve())]).read_bytes());symbols={r['symbol']:r for r in compiled if r['family']=='whole-ASM'}
 export=gate['paired_exports'][0];idx=pin(export['index_path'],export['index_sha256']);payload=pin(export['payload_path'],export['payload_sha256']);entries=d.entries(idx,re.compile(r'(widget|fps)/identity.bin'));identities={}
 with payload.open('rb')as f:
  for key,v in entries.items():f.seek(v['offset']);raw=f.read(v['bytes']);assert len(raw)==v['bytes']and hashlib.sha256(raw).hexdigest()==v['sha256'];identities[key]=struct.unpack('<'+str(len(raw)//4)+'I',raw)
 assert sha(idx)==export['index_sha256']and sha(payload)==export['payload_sha256'];mfcpath=pin(R/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801');mf=json.loads(mfcpath.read_bytes());mr=mfcpath.parent/'source-derivations.json';mfc=json.loads(pin(mr,mf['files'][str(mr.resolve())]).read_bytes());fp=vr.parent/'format-IAT-relations.json';formats=json.loads(pin(fp,val['files'][str(fp.resolve())]).read_bytes());parent=json.loads(pin(R/'reports/m4-startup138-paired/comparer-preparation-r2/policy-preparation.json').read_bytes());fmt=parent['exact_format_IAT_domains'];assert len(formats)==6*138*3
 for row in fmt:
  targets={r['declared_entry_target']for r in formats if r['cell']==row['cell']};assert len(targets)==1 and all(r['actual_before']==r['actual_after']==r['declared_entry_target']for r in formats if r['cell']==row['cell']);row['actual_original_compiled_observer_target']=targets.pop()
 def raw(cell):
  off,_=image.rva_range(cell-image.image_base,4);return struct.unpack('<I',image.read(off,4))[0]
 for r in fmt:assert r['native_physical_raw_pointer32']==raw(r['cell'])
 extra=[]
 for i,(service,pc)in enumerate([('GetStockObject',0x5a013a),('CreateFontA',0x5a074b),('DeleteObject',0x59ffc8)]):
  cell,target,shim,declared,owner=identities['widget/identity.bin'][i*5:(i+1)*5];section=symbols['widget_observer_x86 whole source'];assert section['address']<=shim<section['address']+section['bytes'];extra.append(dict(cell=cell,named_import=service,actual_original_named_target=target,actual_original_compiled_observer_target=shim,native_physical_raw_pointer32=raw(cell),source_read_pc=pc,whole_DWORD_identity_required=True))
 cell,target,shim,declared=identities['fps/identity.bin'];assert cell==0x5bb53c and target==0x780230dd and declared==0x78000000;section=symbols['fps_observer_x86 whole source'];assert section['address']<=shim<section['address']+section['bytes'];extra.append(dict(cell=cell,named_import='vsprintf',actual_original_named_target=target,actual_original_compiled_observer_target=shim,native_physical_raw_pointer32=raw(cell),whole_DWORD_identity_required=True))
 domains=[]
 for r in mfc:
  domains.append(dict(sequence=r['sequence'],phase=13,source_frame=r['source_frame'],source_FS_before=r['source_FS_BEFORE'],source_FS_after=r['source_FS_AFTER'],source_TEB=r['source_TEB'],owners=[dict(role=v['role'],address=v['address'],extent=v['extent'],initial_sha256=hashlib.sha256(bytes.fromhex(v['initial_hex'])).hexdigest(),source_final_sha256=hashlib.sha256(bytes.fromhex(v['source_final_hex'])).hexdigest())for v in r['source_borrowed_backings']],normal_boundary_PCs=[v['PC']for v in r['source_normal_boundary_relations']],named_API_source_PCs=[v['source_PC']for v in r['source_API_relations']]))
 result=dict(exact_format_IAT_domains=fmt,exact_widget_FPS_IAT_domains=extra,MFC_current_original_domains=domains);p=out/'domains.json';p.write_text(json.dumps(result,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current exact format/GDI/FPS compiled target and physical raw IAT cell domains; fresh six original MFC role metadata only',domains_path=str(p),domains_sha256=sha(p),compiled_whole_observer_report_sha256=sha(review),ordinary_readers_closed=True,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
