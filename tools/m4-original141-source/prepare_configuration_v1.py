"""ROOT configuration preparation after actual input-cut and tree6 gates.

No model/export import, native worker, or acceptance. Configuration remains
unadmitted until an independent whole code/input closure is sealed.
"""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
VSHA='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(input_cut,input_sha,tree_path,tree_sha,name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('transport.json','index.json','payload.bin');v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def ref(p,h=None):p=pin(p,h);return dict(path=str(p),sha256=sha(p))
 vpath=R/'reports/m4-original141/root-capture-validation-r3/report.json';v=read(vpath,VSHA);assert v['passed']and v['reader_closed']and v['counts']['phases']==846 and v['callbacks']==111
 cutpath=pin(input_cut,input_sha);cut=read(cutpath,input_sha);assert cut['passed']and cut['reader_closed']and cut['source_execution']is False and cut['original_validation_sha256']==VSHA
 providerpath=cutpath.parent/'provider-proof.json';provider=read(providerpath);assert provider['passed']and provider['original_validation_sha256']==VSHA
 patchpath=cutpath.parent/'patches.json';patches=read(patchpath);assert len(patches)==13 and all(type(p['original_hex'])is str and len(p['original_hex'])==len(p['instrumented_hex'])for p in patches)
 tree=read(tree_path,tree_sha);assert tree['passed']and tree['source_case_extent']==6 and tree['original_validation_sha256']==VSHA and tree['source_AFTER_seed']is False and tree['canonical_reader_opened']is False
 prepdir=R/'reports/m4-original141/source-preparation-r6';prep=read(prepdir/'report.json',v['preparation_sha256']);order=read(prepdir/'selected-order.json');assert len(order)==141 and len({r['entry']for r in order})==141
 metadata_path=R/'reports/m4-original141-source/root-input-metadata-r1/report.json';metadata=read(metadata_path,'eb73abbf388a8407a5f412755675e5f611ef70cfdb8698b9b450f3476c0cbe67');assert metadata['source_metadata_view']and metadata['actual_compiled_preparation_sha256']==v['preparation_sha256']and metadata['selected_order']==order
 sourceauthority=pin(R/'reports/m4-original141/geometry-preparation-r4/callback-source-contracts.json');authority=read(sourceauthority);assert len(authority)==111
 packed=pin(prepdir/'pages.bin').read_bytes();assert packed[:8]==b'MW4J124P';n=struct.unpack_from('<I',packed,8)[0];assert len(packed)==12+n*4104;pages={}
 for i in range(n):offset=12+i*4104;address,permission=struct.unpack_from('<2I',packed,offset);assert address not in pages;pages[address]=packed[offset+8:offset+4104]
 def bytesat(at,size):assert(at&4095)+size<=4096;return pages[at&~4095][at&4095:(at&4095)+size]
 rows=[]
 for item in order:
  root=item['entry'];key=str(root)
  if key not in authority:continue
  fact=authority[key];assert bytesat(fact['push_pc'],5)==b'\x68'+struct.pack('<I',fact['callback']);call=bytesat(fact['CALL_pc'],5);assert call[0]==0xe8 and(fact['CALL_pc']+5+struct.unpack_from('<i',call,1)[0])&0xffffffff==fact['wrapper']and fact['return_pc']==fact['CALL_pc']+5
  rows.append(dict(root=root,callback=fact['callback'],authority_path=str(sourceauthority),authority_sha256=sha(sourceauthority),authority_row=[key,'callback']))
 assert len(rows)==111 and len({r['root']for r in rows})==111
 callbacks=out/'callbacks.json';callbacks.write_text(json.dumps(dict(schema='mw34-source-callback111-v1',rows=rows),indent=2)+'\n');pin(callbacks)
 reference=pin(prepdir/'reference.cpp').read_text();assert 'std::memcpy(header.magic,debugger?"MW4J138D":"MW4J138O",8);'in reference
 C=dict(schema='mw34-original141-source-input-contract-v1',validation=ref(vpath,VSHA),source_preparation=ref(prepdir/'report.json',v['preparation_sha256']),selected_order=ref(prepdir/'selected-order.json'),source_input_metadata=ref(metadata_path),whole69_page_order=metadata['observed_pages']+metadata['extra_whole_source_pages'],callbacks=ref(callbacks),constructor_source_preparation=ref(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json','26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e'),current_provider_proof=ref(providerpath),current_transition_patches=ref(patchpath),current_compiled_review=ref(R/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c'),current_compiled_links=ref(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json'),physical_header_magic_hex=b'MW4J138O'.hex(),current_tree_source=ref(tree_path,tree_sha))
 config=out/'configuration.json';config.write_text(json.dumps(C,indent=2)+'\n');pin(config);pin(__file__)
 for p,h in files.items():assert sha(p)==h
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,configuration_admitted=False,initializer_credit=0,current_callback_literal_PUSH_CALL_pairs=111,current_original_validation_sha256=VSHA,current_input_cut_sha256=input_sha,current_tree_source_sha256=tree_sha,configuration_sha256=sha(config),files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),configuration=str(config),configuration_sha256=sha(config))))
if __name__=='__main__':main(*sys.argv[1:])
