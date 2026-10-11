"""Derivative accepted Session exposes one exact borrowed onexit service."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 out=(R/sys.argv[1]).resolve();need(not out.exists(),'Fresh borrowed registry preparation');out.mkdir(parents=True)
 parent=R/'reports/m4-formatting-native/preparation-r19/report.json';need(sha(parent)=='1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3','Exact accepted corrected registry parent');data=json.loads(parent.read_text());files={str(parent):sha(parent)};relations=[]
 for old in parent.parent.iterdir():
  if not old.is_file()or old.name=='report.json':continue
  need(str(old)in data['files']and sha(old)==data['files'][str(old)],'Physically sealed parent source '+str(old));new=out/old.name;shutil.copyfile(old,new);files[str(old)]=sha(old);relations.append({'parent':str(old),'child':str(new),'parent_sha256':sha(old),'unchanged':True})
 header=out/'session.hpp';s=header.read_text();marker=' void finish();void dump(Sink,void*)const;';need(s.count(marker)==1,'Exact Session public API seam');s=s.replace(marker,' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);\n'+marker);header.write_text(s)
 implementation=out/'session_impl.inc';s=implementation.read_text();marker=' void finish(){';need(s.count(marker)==1,'Exact Session implementation seam');add=R/'tools/m4-widget-native/borrowed_onexit.inc';s=s.replace(marker,add.read_text()+'\n'+marker);marker='void Session::bootstrap(){';need(s.count(marker)==1,'Exact Session method definition seam');s=s.replace(marker,'void Session::borrow_widget_onexit(State&s,unsigned root,unsigned frame,unsigned ret){impl_->borrow_widget_onexit(s,root,frame,ret);}\n'+marker);implementation.write_text(s)
 for row in relations:row['child_sha256']=sha(Path(row['child']));row['unchanged']=row['parent_sha256']==row['child_sha256']
 need([Path(row['child']).name for row in relations if not row['unchanged']]==['session.hpp','session_impl.inc'],'Only two explicit borrowed API changes')
 # Six literal callback identities are authenticated against current contracts.
 contracts=R/'reports/m4-widget-native/preparation-r2/contracts.json';c=json.loads(contracts.read_text());expected={row['root']:row['registration']['callback']for row in c['roots']};import re
 actual={int(a,16):int(b,16)for a,b in re.findall(r'case 0x([0-9a-f]+):callback=0x([0-9a-f]+)',add.read_text())};need(actual==expected,'All six exact source callback identities')
 for p in [Path(__file__).resolve(),add,contracts,*out.iterdir()]:
  if p.is_file():files[str(p)]=sha(p)
 report={'passed':True,'scope':'Compile preparation of exact caller-owned borrowed widget onexit service through accepted source CRT/heap/CS; no worker or service-equivalence execution','parent_preparation_sha256':sha(parent),'parent_preparation':str(parent),'native_library':str(out/'registry_library.cpp'),'native_include':str(out),'source_relations':relations,'copied_files':len(relations),'unchanged_files':sum(x['unchanged']for x in relations),'changed_files':['session.hpp','session_impl.inc'],'roots':list(expected),'source_callbacks':expected,'service':{'source_CALL_pc':0x5ac11e,'raw_IAT':0x1decb0,'IAT_slot':0x5bb52c,'provider_entry':0x78004a36,'source_return':0x5ac124,'frame_minus_root_frame':-24,'extra_source_frame_pushed':False,'source_provider_after_seed':False},'files':files,'native_executed':False,'initializer_credit':0,'host_onexit_or_noop_substitution':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json'),'changed_files':2}))
if __name__=='__main__':main()
