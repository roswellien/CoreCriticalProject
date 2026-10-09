"""Independent disjoint union of unchanged strict non-extracting readers."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,HEADER,MAGIC,MAX_INDEX
from manifests import unique_object


def need(value,why):
    if not value:raise ValueError(why)


class StrictUnion:
    def __init__(self,path,digest,add):
        self.path=add(path,digest);self.readers=[];self.entries={};self.parts=[]
        self.value=json.loads(self.path.read_bytes(),object_pairs_hook=unique_object)
        value=self.value
        need(value['passed'] is True and value['format']=='mw34.capture.direct.v1' and value['transport_only'] is True and
             value['native_executed'] is False,'Typed completed direct transport; native credit solely from actual stage')
        need(isinstance(value['parts'],list) and value['parts'] and type(value['logical_files']) is int and
             type(value['payload_bytes']) is int,'Complete typed direct part inventory')
        need(all(isinstance(value[key],(int,float)) and math.isfinite(value[key]) and value[key]>=0
                 for key in ('emit_seconds','finalize_parts_seconds')),'Finite direct transport timing metadata')
        physical={self.path.name.casefold()};keys=set();payload=0
        try:
            for part in value['parts']:
                need(set(part)=={'bundle','bundle_bytes','index_bytes','index_sha256','logical_files','payload_bytes','sha256'},'Exact direct part schema')
                name=part['bundle'];need(isinstance(name,str) and Path(name).name==name and not any(c in name for c in '/\\:') and
                     name.endswith('.mwb') and name.casefold() not in physical,'Distinct safe direct archive basename')
                physical.add(name.casefold());archive=add(self.path.parent/name,part['sha256'])
                # The unchanged frozen reader takes exactly2arguments. Its
                # whole-file pin authenticates this separately read header.
                reader=CaptureBundle(archive,part['sha256']);self.readers.append(reader)
                with archive.open('rb') as stream:
                    magic,index_bytes,index_digest=HEADER.unpack(stream.read(HEADER.size));raw=stream.read(index_bytes)
                need(magic==MAGIC and 1<=index_bytes<=MAX_INDEX and len(raw)==index_bytes and
                     hashlib.sha256(raw).digest()==index_digest and index_digest.hex()==part['index_sha256'] and index_bytes==part['index_bytes'],
                     'Actual whole-file authenticated direct index identity and extent')
                need(all(type(part[key]) is int and part[key]>=0 for key in ('bundle_bytes','index_bytes','logical_files','payload_bytes')) and
                     archive.stat().st_size==part['bundle_bytes'] and len(reader.names())==part['logical_files'],'Exact direct part record/physical extent')
                current_payload=0
                for logical in reader.names():
                    need(logical.casefold() not in keys,'Case-disjoint complete strict union');keys.add(logical.casefold())
                    self.entries[logical]=reader;current_payload+=len(reader.read_bytes(logical))
                need(current_payload==part['payload_bytes'],'Exact full direct part payload bytes');payload+=current_payload
                self.parts.append(dict(part,path=str(archive)))
            need(len(self.entries)==value['logical_files'] and payload==value['payload_bytes'],'Exact union record/payload totals')
            need({item.name.casefold() for item in self.path.parent.iterdir()}==physical and
                 all(item.is_file() for item in self.path.parent.iterdir()),'Published capture contains only manifest/strict parts; no flat records or loose additions')
        except Exception:self.close();raise
    def names(self):return tuple(sorted(self.entries))
    def exists(self,name):return name in self.entries
    def read_bytes(self,name):
        need(name in self.entries,'Required current actual record '+name);return self.entries[name].read_bytes(name)
    def close(self):
        for reader in self.readers:reader.close()
    def __enter__(self):return self
    def __exit__(self,*values):self.close()
