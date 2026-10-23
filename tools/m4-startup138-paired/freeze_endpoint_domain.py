"""Physically sealed bothlevel zero-new-exclusion endpoint domain and controls."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 helper=pin(R/'tools/m4-startup138-paired/endpoint_policy.py');spec=importlib.util.spec_from_file_location('endpoint138',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 source=json.loads(pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052').read_bytes());assert source['passed']and source['reader_closed']and source['paired_export_readers_closed']
 pin(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');order=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes())['selected_order'];graphs=json.loads(pin(R/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes());results={}
 for level,h in [('O0','aed0c6f66246db182a52091a5a95c1328fd68fcc7a50926883a1ef5de2cf6b54'),('O2','ef72bac527e988dc7c6384829cfa9c929945b56ae7d6ddf40f83b8ae6157e120')]:
  gatepath=pin(R/f'reports/m4-startup138-paired/endpoint-cells-{level}-r1/report.json',h);gate=json.loads(gatepath.read_bytes());assert gate['native_source_pass_admission']and gate['native_source_sha256']==sha(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json')and gate['ordinary_file_readers_closed']
  cp=gatepath.parent/'cells.json';cells=json.loads(pin(cp,gate['files'][str(cp.resolve())]).read_bytes());results[level]=m.compare(cells,order,graphs)
  for label,phase,side,kind,pos in [('EAX',15,'after','CPU',0),('PC',15,'after','CPU',9),('widget-ECX',134,'after','CPU',1),('FP-value',134,'after','FX',32),('ENV-head',134,'after','ENV',0),('SPI-own-carry',65,'after','ENV',12),('postFP-metadata',74,'after','ENV',12)]:
   bad=copy.deepcopy(cells);row=next(r for r in bad if r['sequence']==0 and r['phase']==phase and r['side']==side)
   if kind=='CPU':row['native_CPU'][pos]^=1
   else:
    key='native_'+kind+'_hex';raw=bytearray.fromhex(row[key]);raw[pos]^=1;row[key]=raw.hex()
   try:m.compare(bad,order,graphs)
   except ValueError:controls.append(dict(level=level,name=label,refused=True))
   else:raise AssertionError(label)
 pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43');pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells_v2.py');pin(__file__);pin(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All six cases at both native optimization levels: unchanged accepted131 CPU/FX/ENV finite policy, physical current138 schedule, no new widget exclusions',native_source_sha256=sha(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json'),allphase_CPU_FX_ENV_lastwriter_admission=True,new_CPU_exclusions=0,new_FX_exclusions=0,new_ENV_exclusions=0,counts=results,negative_controls=controls,archive_reader_opened=False,raw_export_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
