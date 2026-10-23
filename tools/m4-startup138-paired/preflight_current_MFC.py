"""Unmodified accepted131 MFC pairing helper on current closed ordinary exports."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};readers=[];rows=[];counts={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def hardwarefx(raw):return raw[:6]+bytes(18)+raw[24:28]+(0x2ffff).to_bytes(4,'little')+raw[32:]
 try:
  e=load('sealed_export',R/'tools/m4-startup131-original/export_reader.py');m=load('accepted_MFC',R/'tools/m4-startup131-paired/mfc_relations_v2.py');sourcep=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');source=json.loads(sourcep.read_bytes());originalp=pin(R/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801');originalgate=json.loads(originalp.read_bytes());validationp=pin(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');validation=json.loads(validationp.read_bytes());prep=json.loads(pin(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a').read_bytes());op=originalp.parent/'source-derivations.json';np=sourcep.parent/'MFC-source-derivations.json';ap=validationp.parent/'fresh-MFC-observations.json';o=json.loads(pin(op,originalgate['files'][str(op.resolve())]).read_bytes());n=json.loads(pin(np,source['files'][str(np.resolve())]).read_bytes());actual=json.loads(pin(ap,validation['files'][str(ap.resolve())]).read_bytes());assert len(o)==len(actual)==6 and len(n)==12;ori=e.ExportReader(sourcep,sha(sourcep),'original',pin);readers.append(ori)
  for level in('O0','O2'):
   native=e.ExportReader(sourcep,sha(sourcep),level,pin);readers.append(native)
   for seq in range(6):
    ct,row=m.compare(next(r for r in o if r['sequence']==seq),next(r for r in actual if r['sequence']==seq),next(r for r in n if r['level']==level and r['sequence']==seq),prep['inputs'],ori,native,hardwarefx);rows.append(row)
    for k,v in ct.items():counts[k]=counts.get(k,0)+v
   native.close();readers.remove(native)
  ori.close();readers.remove(ori);p=out/'relations.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for rd in readers:rd.close()
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Unmodified accepted131 MFC pair rules, current original3 six source domains and source6 O0/O2 sealed raw targets/current prep4 native input roles; no whole138 comparer invocation',counts=counts,source_cases=len(rows),archive_reader_opened=False,ordinary_readers_closed=True,current_MFC_pair_domain_admitted=passed,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
