"""One failed endpoint field from sealed ordinary exports; no candidate prediction."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 p=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');s=importlib.util.spec_from_file_location('narrow_entries',p);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
 source=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');exports=json.loads(source.read_bytes())['paired_exports'];address=0x5fc098;page=address&~4095;actual={};entry_receipts=[]
 for branch,key in [('original','phase/0/15/extra-after/6275072.bin'),('O0',f'sequence-0/phase-15-after-page-{page}.bin')]:
  # Original5FC000 is fixed record page39, unlike native external page.
  if branch=='original':key='phase/0/15.bin'
  e=next(v for v in exports if v['branch']==branch);index=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);entries=D.entries(index,re.compile(re.escape(key)));v=entries[key]
  with payload.open('rb')as f:f.seek(v['offset']);raw=f.read(v['bytes'])
  assert hashlib.sha256(raw).hexdigest()==v['sha256'];offset=(178404+39*4096+(address&4095))if branch=='original'else address&4095;actual[branch]=struct.unpack_from('<I',raw,offset)[0];entry_receipts.append(dict(branch=branch,name=key,**v))
 assert actual=={'original':0,'O0':0}
 deriv=pin(R/'reports/m4-startup138-original/widget-complete-source-r1/source-derivations.json','b0f9dd7bbd3cd9f656f3792d399dc8a51a46df77cbd6bb11f6c6beb16ee59f89');row=next(v for v in json.loads(deriv.read_bytes())if v['sequence']==0 and v['phase']==15);writes=[dict(index=i,row=a)for i,a in enumerate(row['source_accesses'])if a[4]and a[1]<=address<a[1]+a[3]];assert writes[-1]['row']==[0x5a0645,address,0,4,1]
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Measured phase15 AFTER field causing frozen helper7 mismatch; source literal latest writer zero independently named',level='O0',sequence=0,phase=15,side='after',page=page,address=address,helper7_expected_original=0x058a00c6,helper7_expected_native=0x72001010,actual=actual,source_writes=writes,raw_entries=entry_receipts,ordinary_readers_closed=True,capture_archives_opened=False,source_machine_executed=False,raw_AFTER_used_as_prediction_input=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
