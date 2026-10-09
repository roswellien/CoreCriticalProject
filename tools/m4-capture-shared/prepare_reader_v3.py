"""Additive strict integer admission, following independent parent review."""
from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
def main():
 p=H/'capture_shared_v2.py';old=p.read_text()
 needle="                _need(part['bundle_bytes']==len(reader._map) and part['index_bytes']==index_size and _digest(part['index_sha256'])==index_sha.hex(),'Shared part header/count mismatch')"
 replacement="""                bundle_bytes=_integer(part['bundle_bytes'],HEADER.size+MAX_INDEX+MAX_TOTAL,'Invalid part bundle extent type/bound')
                declared_index=_integer(part['index_bytes'],MAX_INDEX,'Invalid part index extent type/bound')
                _need(bundle_bytes>=HEADER.size and declared_index>=1,'Invalid part header extent minimum')
                _need(bundle_bytes==len(reader._map) and declared_index==index_size and _digest(part['index_sha256'])==index_sha.hex(),'Shared part header/count mismatch')"""
 assert old.count(needle)==1;new=old.replace(needle,replacement)
 target=H/'capture_shared_v3.py';assert not target.exists();target.write_text(new,encoding='utf-8',newline='\n')
 out=R/'reports/m4-capture-shared/reader-repair-r2';out.mkdir(parents=True,exist_ok=False)
 (out/'reader.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(target))))
 (out/'report.json').write_text(json.dumps({'passed':True,'old_reader_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'new_reader_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'difference':'Part bundle_bytes/index_bytes now admit exact bounded integers only, following independent root review. All logical/payload/blob counts already required exact int. Canonical blob index and immutable held ownership unchanged.','bounds':'Unique payload <=2GiB per part; up to200000 logical refs with each blob<=256MiB. Logical referenced bytes may exceed2GiB and are validated independently.','native_executed':False,'format_adopted':False},indent=2)+'\n')
if __name__=='__main__':main()
