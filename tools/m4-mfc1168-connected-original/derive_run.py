"""Reuse the direct physically bound writer controller, with a separate namespace."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-widget-original/run.py';q=R/'tools/m4-mfc1168-connected-original/run.py'
if q.exists():raise ValueError('Fresh controller')
s=p.read_text().replace('reports/m4-widget-original','reports/m4-mfc1168-connected-original').replace('normal widget capture','chronological MFC capture').replace('Actual widget execution stage failed','Actual chronological MFC execution stage failed').replace('Genuine bounded shared five-widget original normal execution only; source/semantic/resource validation follows','Genuine chronological13 accepted roots followed by MFC1168 original normal execution; source/semantic/resource validation follows')
s=s.replace('pin(__file__);pin(sys.executable);',"pin(__file__);pin(R/'tools/m4-mfc1168-connected-original/derive_run.py');pin(R/'tools/m4-widget-original/run.py','"+hashlib.sha256(p.read_bytes()).hexdigest()+"');pin(sys.executable);")
q.write_text(s);print(hashlib.sha256(q.read_bytes()).hexdigest())
