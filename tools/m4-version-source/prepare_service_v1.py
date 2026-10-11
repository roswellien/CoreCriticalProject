"""Copy exact accepted service and add only bounded genuine version MFC leases."""
from pathlib import Path
import hashlib,json,shutil,sys,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh version service');out.mkdir(parents=True);pins={};relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical service input '+str(p));pins[str(p)]=v;return p
 try:
  parent=pin(R/'reports/m4-widget-native/service-preparation-r3/report.json','3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd');prior=json.loads(parent.read_bytes());need(prior['passed'],'Exact positive accepted service lineage')
  for p in parent.parent.iterdir():
   if not p.is_file()or p.name=='report.json':continue
   pin(p,prior['files'][str(p.resolve())]);q=out/p.name;shutil.copyfile(p,q);relations.append(dict(parent=str(p),child=str(q),parent_sha256=sha(p)))
  header=out/'session.hpp';s=header.read_text();a='struct SessionImpl;';b='struct SessionImpl;\nstruct VersionBuffer {void*native;unsigned guest,generation,requested,capacity;};';need(s.count(a)==1,'One service declaration seam');s=s.replace(a,b)
  a=' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);';b=a+'\n void borrow_version_mfc(State&,unsigned site,unsigned frame,unsigned return_pc);\n VersionBuffer borrow_version_buffer(unsigned site,unsigned guest,unsigned bytes);\n void commit_version_buffer(unsigned site,const VersionBuffer&);';need(s.count(a)==1,'One borrowed service API seam');header.write_text(s.replace(a,b))
  impl=out/'session_impl.inc';s=impl.read_text();a=' std::vector<std::array<unsigned,8>>projections;';b=a+'\n struct VersionHistory {std::array<std::uint64_t,6>lease;std::vector<std::byte>before,after;};\n bool version_buffer_live_{};std::array<std::uint64_t,6>version_buffer_{};std::vector<std::byte>version_buffer_before_;std::vector<VersionHistory>version_buffer_history_;';need(s.count(a)==1,'One exact private service state seam');s=s.replace(a,b)
  add=pin(R/'tools/m4-version-source/borrowed_mfc_v1.inc').read_text();a=' void finish(){';need(s.count(a)==1,'One method insertion seam');s=s.replace(a,add+'\n'+a+'\n  require(!version_buffer_live_,"No open native version-buffer lease during provider cleanup");',1)
  a='void Session::borrow_widget_onexit(State&s,unsigned root,unsigned frame,unsigned ret){impl_->borrow_widget_onexit(s,root,frame,ret);}'
  b=a+'\nvoid Session::borrow_version_mfc(State&s,unsigned site,unsigned frame,unsigned ret){impl_->borrow_version_mfc(s,site,frame,ret);}\nVersionBuffer Session::borrow_version_buffer(unsigned site,unsigned guest,unsigned bytes){return impl_->borrow_version_buffer(site,guest,bytes);}\nvoid Session::commit_version_buffer(unsigned site,const VersionBuffer&lease){impl_->commit_version_buffer(site,lease);}'
  need(s.count(a)==1,'One concrete public service forwarding seam');s=s.replace(a,b);impl.write_text(s)
  for x in relations:x['child_sha256']=sha(x['child']);x['unchanged']=x['child_sha256']==x['parent_sha256'];pin(x['child'])
  need(sorted(Path(x['child']).name for x in relations if not x['unchanged'])==['session.hpp','session_impl.inc'],'Only exact private/public borrowed interface extension')
  prep=pin(R/'reports/m4-version-source/preparation-r2/report.json','137c214307a28b0e120b600ee53f14fcfacac0a72a7ef64b437178f3b3b17c75');p=json.loads(prep.read_bytes());pin(prep.parent/'contracts.json',p['files'][str((prep.parent/'contracts.json').resolve())]);pin(__file__)
  report=dict(passed=True,scope='Compile-only actual typed MFC823/825 borrowing and private same-generation full version native-buffer lease/commit; no Version API call, worker or fixture acceptance',parent_service_sha256=sha(parent),source_relations=relations,copied_files=len(relations),unchanged_files=sum(x['unchanged']for x in relations),changed_files=['session.hpp','session_impl.inc'],native_include=str(out),native_library=str(out/'registry_library.cpp'),root=0x4af240,MFC_CALL_sites=[0x4af11a,0x4af1a8],buffer_API_CALL_sites=[0x4af12c,0x4af167],retains_genuine_NULL_free=True,retains_existing_allocator_private_owner_checks=True,owns_private_whole_native_buffer_before=True,commits_whole_capacity_not_requested_prefix_only=True,source_CALLBACK_onexit_extension_pending=True,version_API_identity_hardware_adapter_pending=True,native_executed=False,original_executed=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),unchanged_files=report['unchanged_files'])))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
