"""Read direct archives with the unchanged strict v1 reader; never extract."""
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import unique_object
TRANSPORT_KEYS={'emit_seconds','finalize_parts_seconds','format','logical_files','native_executed','parts','passed','payload_bytes','transport_only'}
PART_KEYS={'bundle','bundle_bytes','index_bytes','index_sha256','logical_files','payload_bytes','sha256'}

def need(ok,why):
    if not ok:raise ValueError(why)

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

class DirectSet:
    def __init__(self,path,pin):
        self.path=pin(path);self.value=read(self.path);self.bundles=[];self.entries={};self.records={}
        v=self.value
        need(set(v)==TRANSPORT_KEYS and v['passed'] is True and v['format']=='mw34.capture.direct.v1' and v['transport_only'] is True and v['native_executed'] is False,'Exact transport-only direct manifest schema')
        try:
            folded=set();physical={self.path.name};payload=0
            for number,p in enumerate(v['parts'],1):
                need(set(p)==PART_KEYS and p['bundle']==f'part-{number}.mwb','Canonical strict direct part schema/order')
                path=pin(self.path.parent/p['bundle'],p['sha256']);physical.add(path.name)
                with path.open('rb') as f:magic,index_bytes,index_sha=struct.unpack('<8sQ32s',f.read(48))
                need(magic==b'MW34CAP1' and index_bytes==p['index_bytes'] and index_sha.hex()==p['index_sha256'],'Actual unchanged strict v1 header')
                b=CaptureBundle(path,p['sha256']);self.bundles.append(b)
                need(len(b.names())==p['logical_files'] and path.stat().st_size==p['bundle_bytes'],'Actual direct part count/extent')
                part_bytes=0
                for name in b.names():
                    need(name.casefold() not in folded,'Global disjoint logical collision domain')
                    folded.add(name.casefold());self.entries[name]=b;data=b.read_bytes(name);part_bytes+=len(data)
                    import hashlib
                    self.records[name]={'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
                need(part_bytes==p['payload_bytes'],'Actual direct payload extent');payload+=part_bytes
            need(len(self.entries)==v['logical_files'] and payload==v['payload_bytes'],'Exact whole logical union')
            need({p.name for p in self.path.parent.iterdir()}==physical,'Compact archive-only physical publication')
        except BaseException:self.close();raise

    def data(self,name):
        need(name in self.entries,'Required independent logical observation: '+name)
        return self.entries[name].read_bytes(name)
    def words(self,name,count,kind='I'):
        raw=self.data(name);need(len(raw)==count*struct.calcsize(kind),'Exact observed extent: '+name)
        return struct.unpack('<'+str(count)+kind,raw)
    def names(self):return tuple(sorted(self.entries))
    def close(self):
        for b in self.bundles:b.close()
