"""Normalize three physical string instructions to their complete operands."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'trace-preparation-r4';out=B/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','8b09847fd3b4262e95c1ad76cff2d9375c95eca57db26c3c1e7441c49392ee8f').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 out.mkdir()
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 path=out/'trace-instruction-contracts.json';data=json.loads(path.read_bytes());by_pc={r['pc']:r for r in data['instructions']};fixes=[]
 def memory(reg,write):
  coef=[0]*8;coef[reg]=1;return dict(displacement=0,coefficients=coef,width=4,read=int(not write),write=int(write),segment=0)
 for pc,op,cells in [(0x78001041,'stosd',[memory(7,True)]),(0x78010752,'movsd',[memory(6,False),memory(7,True)]),(0x780108b3,'movsd',[memory(6,False),memory(7,True)])]:
  r=by_pc[pc];assert r['mnemonic']==op;fixes.append(dict(pc=pc,mnemonic=op,before_cells=r['cells'],after_cells=cells));r['cells']=cells;r['contract']['explicit_memory_reads']=[];r['contract']['explicit_memory_writes']=[]
 path.write_text(json.dumps(data,indent=2)+'\n')
 cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
 header='#pragma once\nstruct HypotTraceMemory{unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct HypotTracePoint{unsigned pc,width,opcode,count;HypotTraceMemory cells[4];};\ninline constexpr std::array<HypotTracePoint,'+str(len(data['instructions']))+'> hypot_trace_points{{\n'
 for d in data['instructions']:header+='{'+','.join(map(str,[d['pc'],d['width'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c)for c in d['cells'])+'}},\n'
 (out/'trace_points.hpp').write_text(header+'}};\n');(out/'string-operand-corrections.json').write_text(json.dumps(fixes,indent=2)+'\n')
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report={**old,'scope':old['scope']+'; three literal string operands normalized to one STOSD write and two MOVSD read/write operands','previous_trace_preparation_sha256':sha(parent/'report.json'),'normalized_string_instruction_rows':3,'physical_source_rows_changed':0,'normalization_claim':'Actual source memory effects only; no implicit read of STOSD destination or MOVSD destination, no duplicated implicit/explicit operands','files':pins};q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
