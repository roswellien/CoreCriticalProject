"""Freeze four positive current source children; never promote failed parent."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path(__file__).resolve().parents[2]

def main():
 base=R/'reports/m4-original141-source';out=base/'retained-positive-family-r2'
 assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 priorpath=base/'source-r5/report.json';prior=read(priorpath,'daef37cb22b9d6f00961ce182f5ddc27821374aa6158080e4d2ca8400c53b056')
 assert prior['passed']is False and prior['reader_closed']and prior['ordinary_reader_closed']
 old=read(base/'retained-positive-family-r1/manifest.json','4bde643912fe8a35aa3bdb469ae73da1dc730cc363af92b1f329056a00f70266')
 assert prior['configuration_sha256']==old['configuration_sha256']and prior['original_validation_sha256']==old['original_validation_sha256']
 rows=old['rows']+[dict(domain='new_MFC',path=str((base/'source-r5-MFC/report.json').resolve()),sha256='820a0832b24cd0666b4011552d1c9127623429cc0b01cfcc33319e8b40211dd4',source_case_extent=6,helper_path=str((R/'tools/m4-original141-source/mfc_source141_v1.py').resolve()))]
 assert len(rows)==4 and {r['domain']for r in rows}=={'constructor18','formatter4','old4','new_MFC'}
 for row in rows:
  g=read(row['path'],row['sha256']);assert g['passed']and not g['source_AFTER_seed']and not g['canonical_reader_opened']
  assert any(x['domain']==row['domain']and x['receipt']==row['path']and x['sha256']==row['sha256']for x in prior['children'])
  for p,h in g['files'].items():pin(p,h)
  pin(row['helper_path']);row['helper_sha256']=files[row['helper_path']]
  assert g['files'][row['helper_path']]==row['helper_sha256']
  if row['domain']=='constructor18':assert len(g['cases'])==18 and all(x['whole_GPR_EIP']and x['defined_EFLAGS']and x['whole_FX512']and x['whole_ENV28']for x in g['cases'])
  else:assert g['source_case_extent']==row['source_case_extent']and g['original_validation_sha256']==prior['original_validation_sha256']
 out.mkdir();m=out/'manifest.json'
 m.write_text(json.dumps(dict(schema=old['schema'],configuration_sha256=old['configuration_sha256'],original_validation_sha256=old['original_validation_sha256'],failed_parent_path=str(priorpath.resolve()),failed_parent_sha256=files[str(priorpath.resolve())],failed_parent_passed=False,failed_parent_reader_closed=True,rows=rows,files=files),indent=2)+'\n')
 pin(m);msha=files[str(m.resolve())]
 p=R/'tools/m4-original141-source/replay_original141_v8.py';c=p.with_name('replay_original141_v9.py');assert not c.exists()
 a=pin(p).read_text();b=a
 edits=[("retained-positive-family-r1/manifest.json','4bde643912fe8a35aa3bdb469ae73da1dc730cc363af92b1f329056a00f70266",f"retained-positive-family-r2/manifest.json','{msha}"),("Only three actual closed current positive children","Only four actual closed current positive children"),("len(reuse['rows'])==len(reused)==3 and set(reused)=={'constructor18','formatter4','old4'},'Exactly distinct three retained positive domains'","len(reuse['rows'])==len(reused)==4 and set(reused)=={'constructor18','formatter4','old4','new_MFC'},'Exactly distinct four retained positive domains'"),("'widget_source141_v3.py'","'widget_source141_v4.py'")]
 for x,y in edits:assert b.count(x)==1;b=b.replace(x,y)
 ast.parse(b);assert all(b.count(y)==1 for x,y in edits)
 back=b
 for x,y in reversed(edits):back=back.replace(y,x)
 assert back==a;c.write_text(b);pin(c)
 aa=a.splitlines(True);bb=b.splitlines(True);deltas=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes():
  if tag!='equal':deltas.append(dict(child_start=k,child_stop=l,parent=''.join(aa[i:j]),child=''.join(bb[k:l])))
 d=out/'controller-inverse.json';d.write_text(json.dumps(deltas,indent=2)+'\n');pin(d);pin(__file__)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,retained_actual_positive_domains=rows,failed_parent_success_used=False,controller_exact_whole_inverse=True,controller_inverse_hunks=len(deltas),registry846_rerun=True,MFC6_reused=True,widget42_fresh_required=True,widget_v4_separate_ROOT_admission_required=True,initializer_credit=0,accepted_function_credit=0,manifest_sha256=msha,files={str(z.resolve()):files[str(z.resolve())]for z in(p,c,m,d,Path(__file__))}),indent=2)+'\n')
 with q.open('rb')as f:print(hashlib.file_digest(f,'sha256').hexdigest())
if __name__=='__main__':main()
