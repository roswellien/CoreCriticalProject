"""Actual three VERSION APIs and exact 4AF270 onexit callback; preserve v2."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=P/'prepare_service_v2.py';assert sha(p)=='49da13aa9cd8b474a40e7f4167b13f1cffd7b44d64a0dcc8e743aefc8f0f0c00'
s=p.read_text();a="add=pin(R/'tools/m4-version-source/borrowed_mfc_v2.inc').read_text();";assert s.count(a)==1;s=s.replace(a,"add=pin(R/'tools/m4-version-source/borrowed_mfc_v2.inc').read_text()+pin(R/'tools/m4-version-source/borrowed_version_api_v1.inc').read_text();",1)
a="header=out/'session.hpp';s=header.read_text();";b=a+"header_source=pin(R/'tools/m4-version-source/native_version_api_v1.hpp','dec29e48d8e974e96c3630d6e8c7d3ab20c98db822e19af140749ecb1d50d4c0');shutil.copyfile(header_source,out/'native_version_api.hpp');s=s.replace('#include \\\"runtime.hpp\\\"','#include \\\"runtime.hpp\\\"\\n#include \\\"native_version_api.hpp\\\"',1);";assert s.count(a)==1;s=s.replace(a,b)
a="s=s.replace(a,b)\n  a=' void borrow_widget_onexit";b="s=s.replace(a,b)\n  a=' void borrow_widget_onexit";assert s.count(a)==1
a="void commit_version_buffer(unsigned site,const VersionBuffer&);";assert s.count(a)==1;s=s.replace(a,a+"\\n void borrow_version_api(State&,unsigned site,unsigned frame,unsigned return_pc);",1)
a="std::vector<VersionHistory>version_buffer_history_;";assert s.count(a)==1;s=s.replace(a,a+"\\n m4_version_api::Module version_module_;std::vector<m4_version_api::Record>version_APIs_;",1)
a="void Session::commit_version_buffer(unsigned site,const VersionBuffer&lease){impl_->commit_version_buffer(site,lease);}";assert s.count(a)==1;s=s.replace(a,a+"\\nvoid Session::borrow_version_api(State&s,unsigned site,unsigned frame,unsigned ret){impl_->borrow_version_api(s,site,frame,ret);}",1)
a="need(s.count(a)==1,'One exact lease-history emission seam');s=s.replace(a,b);impl.write_text(s)"
b="""need(s.count(a)==1,'One exact lease-history emission seam');s=s.replace(a,b)
  a='case 0x479590:callback=0x4795d0;break;'
  need(s.count(a)==1,'One finite callback extension');s=s.replace(a,a+'case 0x4af240:callback=0x4af270;break;',1)
  a='  sink("heap-query-witness.bin",std::as_bytes(std::span(b.query_witness)),user);'
  b=a+'\\n  for(unsigned n=0;n<version_APIs_.size();++n){const auto&v=version_APIs_[n];const auto stem="version-api-"+std::to_string(n);sink(stem+"-words.bin",std::as_bytes(std::span(v.words)),user);sink(stem+"-CPU-before.bin",std::as_bytes(std::span(&v.before,1)),user);sink(stem+"-CPU-after.bin",std::as_bytes(std::span(&v.after,1)),user);sink(stem+"-args.bin",std::as_bytes(std::span(v.args)),user);sink(stem+"-frame.bin",v.frame,user);sink(stem+"-hardware.bin",std::as_bytes(std::span(&v.hardware,1)),user);for(unsigned side=0;side<2;++side){const auto&i=side?v.identity_after:v.identity_before;const auto&f=side?v.file_after:v.file_before;const auto p=stem+"-"+std::to_string(side);sink(p+"-identity.bin",std::as_bytes(std::span(i.words)),user);sink(p+"-entry64.bin",i.entry,user);sink(p+"-primary-path.bin",std::as_bytes(std::span(i.primary_path)),user);sink(p+"-owner-path.bin",std::as_bytes(std::span(i.owner_path)),user);sink(p+"-primary-sha.bin",std::as_bytes(std::span(i.primary_sha)),user);sink(p+"-owner-sha.bin",std::as_bytes(std::span(i.owner_sha)),user);sink(p+"-file-identity.bin",std::as_bytes(std::span(f.words)),user);sink(p+"-cwd.bin",std::as_bytes(std::span(f.cwd)),user);sink(p+"-file-path.bin",std::as_bytes(std::span(f.path)),user);sink(p+"-file-sha.bin",std::as_bytes(std::span(f.sha)),user);}}'
  need(s.count(a)==1,'One actual version API proof emission seam');s=s.replace(a,b);impl.write_text(s)
  asm_parent=pin(R/'tools/m4-widget-native/native_api.s','692b17f008c0cdc69c9cc4ea57959df76f520d4913e40a49ee281e212f9e1e7a');asm=asm_parent.read_text();asm=asm[:asm.index('.globl mw34_widget_hardware_call')].replace('mw34_widget_native_api','mw34_version_native_api');(out/'native_version_api.s').write_text(asm)
  pin(out/'native_version_api.s');pin(out/'native_version_api.hpp')"""
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('source_CALLBACK_onexit_extension_pending=True,version_API_identity_hardware_adapter_pending=True','source_CALLBACK_onexit_extension_pending=False,version_API_identity_hardware_adapter_pending=False,actual_VERSION_APIs=3,whole_source_frame_bytes=64,native_hardware_bytes=1152,typed_native_query_pointer_projection=True,actual_file_CWD_SHA_and_file_identity_before_after=True,worker_fixture_pending=True')
s=s.replace("pin(R/'tools/m4-version-source/derive_service_v2.py');","pin(R/'tools/m4-version-source/derive_service_v2.py');pin(R/'tools/m4-version-source/derive_service_v3.py');pin(R/'tools/m4-version-source/prepare_service_v2.py','49da13aa9cd8b474a40e7f4167b13f1cffd7b44d64a0dcc8e743aefc8f0f0c00');")
s=s.replace('no Version API call, worker or fixture acceptance','real three VERSION.dll implementations and callback extension compiled, no actual worker execution or fixture acceptance')
q=P/'prepare_service_v3.py';assert not q.exists();q.write_text(s);print(json.dumps(dict(emitted=str(q),native_executed=False)))
