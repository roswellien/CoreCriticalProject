"""Bounded independent actual ordinary API4/80/83 diagnosis, no models or readers."""
from pathlib import Path
import json,hashlib,struct
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-Lockit-contract-diagnostic-r1';assert not out.exists();out.mkdir();np=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';assert sha(np)=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3';N=json.loads(np.read_bytes());e=next(v for v in N['paired_exports']if v['branch']=='O0');ip=Path(e['index_path']);pp=Path(e['payload_path']);assert sha(ip)==e['index_sha256'];I=json.loads(ip.read_bytes());assert pp.stat().st_size==e['payload_bytes'];failure=R/'reports/m4-startup141-paired/native36-source-r7/report.json';assert sha(failure)=='1fdd3461bdb457c3ffe83d1e2f3d1f97554648a0b3ec29c73370b72e38b75140';F=json.loads(failure.read_bytes());assert F['passed']is False and F['ordinary_reader_closed']is True and F['files'][str(pp)]==e['payload_sha256'];oldcp=R/'reports/m4-startup141-paired/native-owner-metadata-preparation-r2/physical-API-contracts.json';C=json.loads(oldcp.read_bytes());reads={};actual={}
 with pp.open('rb')as f:
  for j in (4,80,83):
   k=f'sequence-0/selected/locale-api-{j}-witness.bin';x=I['entries'][k];assert x['bytes']==256;f.seek(x['offset']);b=f.read(256);assert hashlib.sha256(b).hexdigest()==x['sha256'];actual[j]=list(struct.unpack('<32Q',b));reads[k]=x
 assert actual[4][31]==1 and actual[4][16]==actual[80][16]==actual[83][16]
 for j,site,slot,raw,depth in[(80,0x7810a30b,0x78146198,0x771143e0,1),(83,0x7810a35e,0x78146184,0x77113460,0)]:
  w=actual[j];assert str(site)not in C and [w[2],w[3],w[4],w[7],w[19],w[20],w[18]]==[site,slot,raw,1,0,0x78145640,depth]and w[14:16]==[1,1]and w[29:31]==[1,1]and w[13]==24 and w[17]==40
 files=[np,ip,failure,oldcp,Path(__file__),R/'reports/m4-startup141-runway/service-preparation-r2/lockit_contract.inc',R/'reports/m4-startup141-runway/service-preparation-r2/lockit_operations.inc',R/'reports/m4-startup141-runway/service-preparation-r2/locale_batch_operations.inc'];q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Code-independent O0sequence0 lifecycle4 and omitted normal Lockit API80/83 actual raw diagnosis; not source/admission',actual_API_words=actual,ordinary_entry_hashes=reads,ordinary_bytes_read=768,missing_physical_contract_sites=[0x7810a30b,0x7810a35e],same_causal_lifecycle_native_CS=True,depth_sequence=[1,0],payload_whole_hash_recomputed_here=False,payload_declared_sha256=e['payload_sha256'],ROOT_closed_failed_report_payload_pin=sha(failure),model_executed=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in files}),indent=2)+'\n');print(dict(report_sha256=sha(q),ordinary_bytes_read=768))
if __name__=='__main__':main()
