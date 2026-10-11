"""Verify preserved actual REA observations and their explicit unknowns."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 base=ROOT/'reports/m4-vtable-rea';out=base/name;assert not out.exists();out.mkdir()
 source=base/'observations-r1.json';v=json.loads(source.read_bytes());pins={str(source):sha(source),str(Path(__file__).resolve()):sha(__file__)}
 assert v['format']=='preserved-REA-MCP-observations-v1' and not v['official_session_bundle']
 game=ROOT/'MW3/Mech3.exe';assert sha(game)==v['subject_sha256']=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf';pins[str(game)]=sha(game)
 rows={x['key']:x['result']['structuredContent'] for x in v['observations']};assert len(rows)==10
 for r in rows.values():
  e=r['evidence'];assert e['subject']['digest']['sha256']==v['subject_sha256'] and e['provider']['id']=='ghidra' and e['provider']['version']=='12.1.4' and e['authority']=='shipped-artifact' and e['confidence']=='observed'
  assert e['normalized_result']==r['result'] and e['raw_result']==r['result'] and e['evidence_id']==r['evidence_id']
 for key,address,size in [('rea59ff00Boundary','0x59ff00',14),('reaBoundary0x40e820','0x40e820',10),('reaBoundary0x59fba0','0x59fba0',35),('reaBoundary0x59fda0','0x59fda0',66),('reaBoundary0x59ff60','0x59ff60',20)]:
  r=rows[key]['result'];assert r['found'] and r['procedure']['address']==address and r['procedure']['body']['total_bytes']==size
 for pc,target in [('0x59fbab','0x40e820'),('0x59fdc5','0x59ff00')]:
  r=rows['reaCall'+pc]['result'];assert r['status']=='resolved-indirect' and r['mechanism']=='computed' and len(r['targets'])==1 and r['targets'][0]['address']==target
 assert rows['reaCall0x59ff6e']['result']['status']=='unresolved' and not rows['reaCall0x59ff6e']['result']['targets']
 assert rows['reaBoundary0x59ff80']['result']==dict(query_address='0x59ff80',found=False,procedure=None,reason='not_in_procedure')
 assert len(rows['rea59ff00Dossier']['result']['assembly'])==5
 report=dict(passed=True,scope='Actual REA static provider observations preserved directly from MCP results; missing boundary and unresolved computed call are explicit. Physical recovery and runtime gates remain separate.',counts=dict(preserved_observations=10,observed_boundaries=5,resolved_computed_sites=2,unresolved_computed_sites=1,missing_boundaries=1,function_dossiers=1),automatic_full_call_closure=False,official_session_bundle=False,native_executed=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
