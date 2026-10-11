"""Exact normal/API assembly source relation modulo CRLF serialization only."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('review_mfc1168_connected_prelaunch.py')
BASE_SHA='a1c44f5d90ddc8a8013a51742f7ea91243348bd72f247c9189fd3bafda1d32d7'
if hashlib.sha256(BASE.read_bytes()).hexdigest()!=BASE_SHA:raise ValueError('Immutable chronological prelaunch checker')
source=BASE.read_text()
old="raw(folder/filename.replace('.obj','.asm'))==raw(R/'reports/m4-mfc1168-probe/preparation-r10'/filename.replace('.obj','.asm'))"
new="raw(folder/filename.replace('.obj','.asm')).decode().replace('\\r\\n','\\n')==raw(R/'reports/m4-mfc1168-probe/preparation-r10'/filename.replace('.obj','.asm')).decode().replace('\\r\\n','\\n')"
if source.count(old)!=1:raise ValueError('One inherited normal/API assembly relation')
source=source.replace(old,new,1)
old='        pin(__file__);pin(sys.executable);'
if source.count(old)!=1:raise ValueError('One current code closure seam')
source=source.replace(old,'        pin(BASE,BASE_SHA);'+old.strip(),1)
exec(compile(source,str(BASE),'exec'),globals())
