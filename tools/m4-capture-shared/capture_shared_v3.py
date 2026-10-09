"""Additive shared transport pilot. Immutable logical bytes, no execution credit.

One part owns each contiguous blob once. Logical names still identify every
observation. Unique bytes are authenticated once into immutable Python bytes;
the opened Windows handles deny write and delete until close. Canonical v1
readers/writers are unchanged and deliberately reject this new magic.
"""
import hashlib,json,math,mmap,os,stat,struct
from pathlib import Path
from capture_bundle import HEADER,MAX_FILES,MAX_INDEX,MAX_FILE,MAX_TOTAL,_digest,_json,_locked_stream
from paths import logical_name,reject_reparse,workspace_path

MAGIC=b'MW34SHR1'
FORMAT='mw34.capture.shared.v1'
DIRECT_FORMAT='mw34.capture.direct.shared.v1'

def _need(value,message):
    if not value:raise ValueError(message)

def _integer(value,maximum,message):
    _need(type(value) is int and 0<=value<=maximum,message)
    return value

def _object(pairs):
    result={}
    for key,value in pairs:
        _need(key not in result,'Duplicate JSON key')
        result[key]=value
    return result

def _load(raw,canonical=True):
    def invalid(value):raise ValueError('Nonfinite JSON constant')
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=_object,parse_constant=invalid)
    if canonical:_need(_json(value)==raw,'Noncanonical shared JSON')
    return value

class SharedBundle:
    def __init__(self,path,expected_sha256):
        self.path=workspace_path(path,reports=True)
        self._stream=None;self._map=None;self._entries={};self._blobs=()
        self.authenticated_blobs=0;self.authenticated_blob_bytes=0;self.logical_bytes=0
        _digest(expected_sha256)
        try:
            info=reject_reparse(self.path)
            _need(stat.S_ISREG(info.st_mode) and HEADER.size<=info.st_size<=HEADER.size+MAX_INDEX+MAX_TOTAL,'Invalid shared bundle type/size')
            self._stream=_locked_stream(self.path)
            info=os.fstat(self._stream.fileno())
            _need(stat.S_ISREG(info.st_mode) and HEADER.size<=info.st_size<=HEADER.size+MAX_INDEX+MAX_TOTAL,'Invalid opened shared bundle type/size')
            self._map=mmap.mmap(self._stream.fileno(),0,access=mmap.ACCESS_READ)
            _need(hashlib.sha256(self._map).hexdigest()==expected_sha256,'External shared bundle SHA256 mismatch')
            magic,index_size,index_sha=HEADER.unpack(self._map[:HEADER.size])
            _need(magic==MAGIC and 1<=index_size<=MAX_INDEX and HEADER.size+index_size<=len(self._map),'Invalid shared bundle header')
            raw=self._map[HEADER.size:HEADER.size+index_size]
            _need(hashlib.sha256(raw).digest()==index_sha,'Shared index hash mismatch')
            index=_load(raw)
            _need(type(index) is dict and set(index)=={'blobs','files','format','logical_bytes','unique_bytes'} and index['format']==FORMAT,'Invalid shared index schema')
            unique_bytes=_integer(index['unique_bytes'],MAX_TOTAL,'Invalid unique payload count')
            self.logical_bytes=_integer(index['logical_bytes'],MAX_FILES*MAX_FILE,'Invalid logical payload count')
            blobs=index['blobs'];files=index['files']
            _need(type(blobs) is list and 1<=len(blobs)<=MAX_FILES,'Invalid shared blob count')
            _need(type(files) is list and 1<=len(files)<=MAX_FILES,'Invalid shared logical count')
            offset=0;payload=HEADER.size+index_size;owned=[];keys={}
            for blob in blobs:
                _need(type(blob) is dict and set(blob)=={'offset','sha256','size'},'Invalid unique blob schema')
                at=_integer(blob['offset'],MAX_TOTAL,'Invalid blob offset');size=_integer(blob['size'],MAX_FILE,'Invalid blob size');pin=_digest(blob['sha256'])
                _need(at==offset and size<=unique_bytes-offset,'Noncontiguous unique blob extent')
                value=bytes(self._map[payload+at:payload+at+size])
                _need(len(value)==size and hashlib.sha256(value).hexdigest()==pin,'Shared blob SHA256 mismatch')
                # Repeated bytes must share an ID, not a redundant physical blob.
                key=(pin,size)
                for old in keys.get(key,()):_need(old!=value,'Duplicate physical blob')
                keys.setdefault(key,[]).append(value);owned.append(value);offset+=size
                self.authenticated_blobs+=1;self.authenticated_blob_bytes+=size
            _need(offset==unique_bytes and payload+offset==len(self._map),'Shared archive exact extent/trailing bytes')
            self._blobs=tuple(owned);names=[];folded=set();used=set();logical_bytes=0
            for entry in files:
                _need(type(entry) is dict and set(entry)=={'blob_id','path'},'Invalid logical reference schema')
                name=logical_name(entry['path']);bid=_integer(entry['blob_id'],len(owned)-1,'Invalid logical blob reference')
                _need(name.casefold() not in folded,'Duplicate normalized shared name')
                folded.add(name.casefold());names.append(name);used.add(bid);self._entries[name]=bid;logical_bytes+=len(owned[bid])
            _need(names==sorted(names),'Unsorted shared logical inventory')
            _need(used==set(range(len(owned))),'Unreferenced physical blob')
            _need(logical_bytes==self.logical_bytes,'Shared logical payload count mismatch')
        except BaseException:
            self.close();raise
    def names(self):return tuple(self._entries)
    def read_bytes(self,name):
        _need(self._stream is not None,'Closed shared owner')
        return self._blobs[self._entries[logical_name(name)]]
    data=read_bytes
    def close(self):
        self._entries.clear();self._blobs=()
        if self._map is not None:self._map.close();self._map=None
        if self._stream is not None:self._stream.close();self._stream=None
    def __enter__(self):return self
    def __exit__(self,*unused):self.close()

class SharedDirectSet:
    """Explicit new-format analogue of DirectSet.data/words/entries."""
    def __init__(self,manifest,expected_sha256):
        self.path=workspace_path(manifest,reports=True);self._manifest_stream=None;self.readers=[];self.entries={};self.meta=None
        _digest(expected_sha256)
        try:
            info=reject_reparse(self.path)
            _need(stat.S_ISREG(info.st_mode) and 1<=info.st_size<=MAX_INDEX,'Invalid shared manifest type/size')
            self._manifest_stream=_locked_stream(self.path);raw=self._manifest_stream.read(MAX_INDEX+1)
            _need(len(raw)<=MAX_INDEX and hashlib.sha256(raw).hexdigest()==expected_sha256,'External shared manifest SHA256 mismatch')
            meta=_load(raw,canonical=False)
            _need(type(meta) is dict and set(meta)=={'emit_seconds','finalize_parts_seconds','format','logical_files','native_executed','parts','passed','payload_bytes','transport_only','unique_blobs','unique_payload_bytes'},'Invalid shared direct manifest schema')
            _need(meta['format']==DIRECT_FORMAT and meta['passed'] is True and meta['transport_only'] is True and meta['native_executed'] is False,'Shared transport declaration mismatch')
            for name in ['emit_seconds','finalize_parts_seconds']:_need(type(meta[name]) in (int,float) and math.isfinite(meta[name]) and meta[name]>=0,'Invalid transport timing')
            _need(type(meta['parts']) is list and 1<=len(meta['parts'])<=MAX_FILES,'Invalid shared part count')
            inventory={'transport.json'};names=set();counts={'logical_files':0,'payload_bytes':0,'unique_blobs':0,'unique_payload_bytes':0}
            for part in meta['parts']:
                _need(type(part) is dict and set(part)=={'bundle','bundle_bytes','index_bytes','index_sha256','logical_files','payload_bytes','sha256','unique_blobs','unique_payload_bytes'},'Invalid shared part schema')
                file=logical_name(part['bundle']);_need('/' not in file and file.endswith('.mwb') and file.casefold() not in {n.casefold() for n in inventory},'Invalid shared part name')
                inventory.add(file);reader=SharedBundle(self.path.parent/file,_digest(part['sha256']));self.readers.append(reader)
                magic,index_size,index_sha=HEADER.unpack(reader._map[:HEADER.size])
                bundle_bytes=_integer(part['bundle_bytes'],HEADER.size+MAX_INDEX+MAX_TOTAL,'Invalid part bundle extent type/bound')
                declared_index=_integer(part['index_bytes'],MAX_INDEX,'Invalid part index extent type/bound')
                _need(bundle_bytes>=HEADER.size and declared_index>=1,'Invalid part header extent minimum')
                _need(bundle_bytes==len(reader._map) and declared_index==index_size and _digest(part['index_sha256'])==index_sha.hex(),'Shared part header/count mismatch')
                observed={'logical_files':len(reader.names()),'payload_bytes':reader.logical_bytes,'unique_blobs':reader.authenticated_blobs,'unique_payload_bytes':reader.authenticated_blob_bytes}
                for key,value in observed.items():_need(type(part[key]) is int and part[key]==value,'Shared part logical/physical count mismatch');counts[key]+=value
                for name in reader.names():
                    _need(name.casefold() not in names,'Duplicate shared name across parts');names.add(name.casefold());self.entries[name]=reader
            for key,value in counts.items():_need(type(meta[key]) is int and meta[key]==value,'Shared set logical/physical count mismatch')
            physical=set()
            for file in self.path.parent.iterdir():
                info=reject_reparse(file);_need(stat.S_ISREG(info.st_mode),'Unexpected shared capture directory member');physical.add(file.name)
            _need(physical==inventory,'Shared physical inventory mismatch')
            self.meta=meta
        except BaseException:self.close();raise
    def data(self,name):
        _need(self._manifest_stream is not None,'Closed shared set')
        return self.entries[name].read_bytes(name)
    def words(self,name,count,code='I'):
        _need(code in ('I','Q') and type(count) is int and count>=0,'Bounded scalar protocol')
        value=self.data(name);_need(len(value)==count*struct.calcsize('<'+code),'Shared scalar record extent mismatch');return struct.unpack('<'+str(count)+code,value)
    def close(self):
        for reader in self.readers:reader.close()
        self.readers.clear();self.entries.clear()
        if self._manifest_stream is not None:self._manifest_stream.close();self._manifest_stream=None
    def __enter__(self):return self
    def __exit__(self,*unused):self.close()
