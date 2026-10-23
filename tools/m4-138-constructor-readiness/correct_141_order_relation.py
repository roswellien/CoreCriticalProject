"""Additive metadata correction only; no source/build/acceptance alteration."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-runway/order-relation-correction-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 child=R/'reports/m4-startup141-runway/preparation-r2';parent=R/'reports/m4-joint-startup138/preparation-r4'
 c=read(child/'report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');p=read(parent/'report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
 relations=read(child/'source-relations.json',c['files'][str((child/'source-relations.json').resolve())]);old=[x for x in relations if Path(x['child']).name=='selected-order.json'];assert len(old)==1
 a=pin(parent/'selected-order.json',p['files'][str((parent/'selected-order.json').resolve())]);b=pin(child/'selected-order.json',c['files'][str((child/'selected-order.json').resolve())]);ao=json.loads(a.read_bytes());bo=json.loads(b.read_bytes());assert ao==p['selected_order']and bo==c['selected_order']
 physical=read(R/'reports/m4-startup141-runway/readiness-r1/physical-table144.json')['nonzero_order'];ctors={0x4103f0,0x410440,0x459b40}
 assert len(ao)==138 and len(bo)==141 and [x for x in bo if x['entry']not in ctors]==ao
 assert bo==[x for x in physical if x in ao or x['entry']in ctors]
 additions=[dict(phase=i,**x)for i,x in enumerate(bo)if x['entry']in ctors];assert [(x['phase'],x['entry'])for x in additions]==[(13,0x4103f0),(14,0x410440),(39,0x459b40)]
 corrected=dict(parent=str(a),child=str(b),sha256_parent=sha(a),sha256_child=sha(b),whole_bytes_equal=False,relation='Exact finite physical slot-ordered extension138→141; deleting only3constructor entries recovers entire parent selected order',added_entries=additions)
 assert old[0]['whole_bytes_equal']and old[0]['sha256_child']!=sha(b)
 for i,x in enumerate(relations):
  if Path(x['child']).name=='selected-order.json':relations[i]=corrected
 pin(__file__);pin(sys.executable);out.mkdir(parents=True)
 q=out/'source-relations-corrected.json';q.write_text(json.dumps(relations,indent=2)+'\n');pin(q)
 report=dict(passed=True,scope='Additive correction of one stale selected-order source-relation only; original preparation and build remain immutable; independent source/full-link review and admission still required',superseded_relation=old[0],corrected_relation=corrected,only_relation_changed=True,source_changed=False,build_executed=False,native_executed=False,archive_reader_opened=False,initializer_credit=0,accepted_count=131,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main()
