"""ROOT-reviewed finite schema view; no exports/readers/model imports."""
from pathlib import Path
import hashlib,json,re,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(actual_path,actual_sha,name):
 files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('transport.json','index.json','payload.bin');v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 actual_path=pin(actual_path,actual_sha);current=json.loads(actual_path.read_bytes());assert current['passed']and current['root_count']==141 and current['phases']==846 and current['callback_count']==111 and current['Record_bytes']==356992
 parent_path=pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161');parent=json.loads(parent_path.read_bytes());currentdir=actual_path.parent
 orderpath=pin(currentdir/'selected-order.json');order=json.loads(orderpath.read_bytes());assert len(order)==141 and len({r['entry']for r in order})==141
 assert [r for r in order if r['entry']not in(0x4103f0,0x410440,0x459b40)]==parent['selected_order']
 spec=pin(currentdir/'spec.hpp').read_text();match=re.search(r'std::array<unsigned,69> widget_whole_pages\{([^}]+)\};',spec);assert match;whole=[int(v.strip(),16)for v in match[1].split(',')];assert whole==parent['observed_pages']+parent['extra_whole_source_pages']and len(set(whole))==69
 packpath=pin(currentdir/'pages.bin');pack_sha=sha(packpath)
 contractpath=pin(currentdir/'contracts.json');contract=json.loads(contractpath.read_bytes());assert contract['selected_order']==parent['selected_order'];contract['selected_order']=order
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir(parents=True)
 q=out/'contracts.json';q.write_text(json.dumps(contract,indent=2)+'\n');pin(q)
 view=dict(parent);view.pop('source_spans',None);view.update(scope='Prepared source-input metadata schema view, physical original141 composition plus retained original138 fixed fields; no new capture or source equivalence',source_metadata_view=True,actual_compiled_preparation_path=str(actual_path),actual_compiled_preparation_sha256=actual_sha,parent_metadata_sha256=sha(parent_path),selected_order=order,order=order,original_roots=141,original_phases=846,callback_count=111,original_sequences=6,contracts=str(q.resolve()),contracts_sha256=sha(q),pack_sha256=pack_sha,source_frame=0x20001800,source_input_frame_policy='Exact actual root BEFORE must separately authenticate0x20001800; declaration alone supplies no runtime input',files=files)
 for p,h in files.items():assert sha(p)==h
 q=out/'report.json';q.write_text(json.dumps(view,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),ordinary_only=True,initializer_credit=0)))
if __name__=='__main__':main(*sys.argv[1:])
