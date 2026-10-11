"""Independent concrete131 acceptance review; no capture payload is reopened."""
from pathlib import Path
import ast,hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={};CHECKS=[]
def need(v,s):
 if not v:raise ValueError(s)
 CHECKS.append(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact current small physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable reviewed input '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def same(a,b,s):need(type(a)is type(b)and a==b,'Exact typed '+s)
def at(r,s):
 for k in s.split('.'):r=r[int(k)]if isinstance(r,list)else r[k]
 return r
FIELDS=('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts','retained_capture_inputs')
def mapping(row):
 result={}
 for key in FIELDS:
  for p,h in row.get(key,{}).items():
   p=str(Path(p).resolve());need(p not in result or result[p]==h,'Conflict-free retained identities '+p);result[p]=h
 return result
def main(config_path,config_sha,name):
 out=R/'reports/m4-joint-startup131-source'/name;need(not out.exists(),'Fresh concrete configuration review');out.mkdir();passed=False;gates={};rows={};edge_rows=[]
 try:
  config=read(config_path,config_sha);acceptor=pin(R/'tools/m4-joint-startup131/acceptance.py');tree=ast.parse(acceptor.read_text());required=next(ast.literal_eval(v.value)for v in tree.body if isinstance(v,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in v.targets));gates=config['gates'];same(set(gates),required,'All33 mandatory distinct gates');same(len(required),33,'Current mandatory gate count')
  for field in('configuration_source','review_specification'):pin(config[field],config[field+'_sha256'])
  for name_gate,gate in gates.items():
   same(set(gate),{'path','sha256','equal'},'Exact concrete gate schema '+name_gate);need(len(gate['equal'])>=2,'At least two explicit predicates '+name_gate);row=read(R/gate['path'],gate['sha256']);same(row['passed'],True,'Passed actual gate '+name_gate)
   for k,v in gate['equal'].items():same(at(row,k),v,name_gate+':'+k)
   rows[name_gate]=row
  same(gates['parent']['sha256'],'12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa','Accepted130 identity')
  same(gates['source_provider']['sha256'],'e520d40b74a9e32dbe8102ebf892f3fd76139ae16d7622c2fdd6713eb520b86d','Actual full131 source identity')
  same(gates['controls']['sha256'],'23d10d824ce9d6b3ebfa6b57a2f8efcf71a00e385b66254063318b7b04a75a5b','Actual current24 semantic control identity')
  spec=read(R/'reports/m4-joint-startup131-source/acceptance-draft-review-r1/recommended-current-predicates.json')
  for gate,field in(('source_provider','current_source_count_predicates'),('controls','current_control_count_predicates')):
   for k,v in spec[field].items():same(rows[gate]['counts'][k],v,'Independent complete measured '+gate+':'+k)
  for field in spec['source_true_fields']:same(rows['source_provider'][field],True,'Complete source scope '+field)
  for field in spec['control_true_fields']:same(rows['controls'][field],True,'Complete control scope '+field)
  for field in spec['control_false_fields']:same(rows['controls'][field],False,'Finite control scope '+field)
  # Explicit current evidence edges, not coincidental equal summary counters.
  edges=[('original_execution','original_prelaunch'),('original_validation','original_execution'),('source_preflight','source_preparation'),('source_provider','original_validation'),('source_provider_review','source_provider'),('source_new_mfc_review','source_provider'),('source_closure','source_provider'),('pair_policy_review','pair_preparation'),('loaded_input_relation','source_provider'),('paired','source_provider'),('paired','original_validation'),('paired_review','paired'),('controls_execution','controls_prelaunch'),('controls','controls_execution'),('controls_review','controls'),('controls_equivalence','controls')]
  identities={label:mapping(row)for label,row in rows.items()}
  for left,right in edges:
   target=str((R/gates[right]['path']).resolve());h=gates[right]['sha256'];need(identities[left].get(target)==h,'Exact current evidence edge '+left+' -> '+right);edge_rows.append(dict(from_gate=left,to_gate=right,path=target,sha256=h))
  for p in('compare_provider_v6.py','mfc_source_v4.py','mfc_source_layout.py'):
   path=str((R/'tools/m4-joint-startup131'/p).resolve());h=sha(path);need(identities['source_preparation'].get(path)==identities['source_provider'].get(path)==h,'Exact generated actual reader/preparation join '+p);pin(path,h)
  path=str((R/'tools/m4-mfc1168-native/verify_connected_controls_v5.py').resolve());need(identities['controls'].get(path)==identities['controls_equivalence'].get(path)==sha(path),'Actual checker5 equivalence joins executed strict semantics');pin(path)
  same(rows['source_preflight']['source_preparation_sha256'],gates['source_preparation']['sha256'],'Current reviewed reader6 preparation')
  same(rows['controls']['execution_sha256'],gates['controls_execution']['sha256'],'Actual controls current execution')
  same(rows['controls_execution']['admission_review_sha256'],gates['controls_prelaunch']['sha256'],'Actual controls repaired worker admission')
  order=rows['native_preparation']['selected_order'];same(order,rows['original_preparation']['selected_order'],'Same actual131 native/original schedule');same(len(order),131,'131 scheduled roots');same(order[13],dict(entry=0x5ae3e4,slot=0x5e0040),'Inserted exact nonregistering MFC initializer')
  same(rows['native_preparation']['current_registration_callbacks'],101,'Parent101 callbacks conserved')
  for gate,field,expected in(('source_provider','paired_exports',spec['paired_export_extents']),('controls','raw_exports',spec['controls_export_extents'])):
   rows_export=rows[gate][field];same({r['branch']for r in rows_export},set(expected),'All bounded export branches '+gate)
   for row in rows_export:
    same([row['logical_files'],row['payload_bytes']],expected[row['branch']],'Whole current logical export extent '+gate+row['branch']);same(row['equality_targets_only'],True,'Raw-only equality exports');
    for leaf in('index','payload','transport'):need(identities[gate].get(str(Path(row[leaf+'_path']).resolve()))==row[leaf+'_sha256'],'Producing receipt seals raw '+leaf+' '+row['branch'])
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__);report=dict(passed=passed,scope='Independent concrete33-gate configuration, current immutable evidence graph, exact measured source/control extents and raw export provenance; no capture archives or acceptance credit',configuration_sha256=config_sha,gates_reviewed=len(gates),explicit_predicates_reviewed=len(CHECKS),evidence_edges=edge_rows,capture_reader_opened=False,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),gates=len(gates),predicates=len(CHECKS))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
