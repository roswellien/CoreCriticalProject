"""Bounded sealed ordinary two-page CRT relation frontier, no source or archive."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 spec=importlib.util.spec_from_file_location('ordinary',pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(rp.read_bytes());assert gate['passed']and gate['reader_closed'];pages=(0x7802e000,0x78037000);order=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes())['selected_order'];results=[]
 for branch in('original','O0','O2'):
  row=next(r for r in gate['paired_exports']if r['branch']==branch);ip=pin(row['index_path'],row['index_sha256']);payload=Path(row['payload_path']);assert payload.stat().st_size==row['payload_bytes'];pattern=re.compile(r'phase/[0-5]/\d+/extra-(before|after)/('+ '|'.join(str(p)for p in pages)+r')\.bin')if branch=='original'else re.compile(r'sequence-[0-5]/phase-\d+-(before|after)-page-('+ '|'.join(str(p)for p in pages)+r')\.bin');index=m.entries(ip,pattern);assert len(index)==6*138*2*2
  with payload.open('rb')as f:
   def data(key):
    v=index[key];assert v['bytes']==4096;f.seek(v['offset']);b=f.read(4096);assert len(b)==4096 and hashlib.sha256(b).hexdigest()==v['sha256'];return b
   for seq in range(6):
    baseline={};previous={}
    for phase,root in enumerate(order):
     for page in pages:
      def key(side):return f'phase/{seq}/{phase}/extra-{side}/{page}.bin'if branch=='original'else f'sequence-{seq}/phase-{phase}-{side}-page-{page}.bin'
      before=data(key('before'));after=data(key('after'))
      if phase==0:baseline[page]=before
      transition=[dict(offset=i,before=before[i],after=after[i])for i in range(4096)if before[i]!=after[i]];interphase=[]if phase==0 else [i for i in range(4096)if previous[page][i]!=before[i]]
      results.append(dict(branch=branch,sequence=seq,phase=phase,root=root['entry'],page=page,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),source_gate_does_not_admit_this_crossbranch_policy=True,within_root_changed_bytes=transition,interphase_changed_offsets=interphase,baseline_difference_offsets=[i for i in range(4096)if baseline[page][i]!=before[i]]));previous[page]=after
  assert sha(ip)==row['index_sha256']
 p=out/'cells.json';p.write_text(json.dumps(results,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable);counts={}
 for branch in('original','O0','O2'):
  subset=[r for r in results if r['branch']==branch];counts[branch]=dict(page_roots=len(subset),root_written_addresses=sorted({r['page']+x['offset']for r in subset for x in r['within_root_changed_bytes']}),interphase_changed_addresses=sorted({r['page']+x for r in subset for x in r['interphase_changed_offsets']}))
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current sealed twoCRTpage actual changes and carries only; literal policy not yet admitted',counts=counts,raw_file_readers_closed=True,archive_reader_opened=False,full_pair_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(sha256=sha(q),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
