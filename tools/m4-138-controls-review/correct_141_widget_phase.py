"""Additive physical141 widget phase sidecar; unchanged runtime/source metadata."""
from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-runway/widget-phase-correction-r1';assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);pins[str(p)]=v;return p
 prep=R/'reports/m4-startup141-runway/preparation-r2';p=json.loads(pin(prep/'report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c').read_bytes());oldpath=pin(prep/'widget-phase-map.json',p['files'][str((prep/'widget-phase-map.json').resolve())]);orderpath=pin(prep/'selected-order.json',p['files'][str((prep/'selected-order.json').resolve())]);old=json.loads(oldpath.read_bytes());order=json.loads(orderpath.read_bytes());physical=json.loads(pin(R/'reports/m4-startup141-runway/readiness-r1/physical-table144.json').read_bytes())['nonzero_order'];assert order==p['selected_order']and len(order)==141 and [x for x in physical if x in order]==order
 current=copy.deepcopy(old);deltas=[]
 for row in current:
  indices=[i for i,x in enumerate(order)if(x['entry'],x['slot'])==(row['root'],row['slot'])];assert len(indices)==1;deltas.append(dict(root=row['root'],slot=row['slot'],old_phase=row['phase'],phase141=indices[0]));row['phase']=indices[0]
 assert len(current)==7 and deltas[0]['old_phase']==15 and deltas[0]['phase141']==17
 restored=copy.deepcopy(current)
 for row,prior in zip(restored,old):row['phase']=prior['phase']
 assert restored==old
 pin(__file__);pin(sys.executable);out.mkdir(parents=True);q=out/'widget-phase-map141.json';q.write_text(json.dumps(current,indent=2)+'\n');pin(q);report=dict(passed=True,scope='Additive sidecar correcting only seven141 widget phase indices from exact selectedphysical root/slot order; runtime/source/build and oldsidecar unchanged',phase_changes=deltas,component_and_source_slice_metadata_unchanged=True,exact_inverse_restores_old_sidecar=True,runtime_changed=False,build_changed=False,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
