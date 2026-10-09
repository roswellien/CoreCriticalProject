"""Actual additive pilot validation. All corrupt files are fresh owned fixtures."""
import copy,ctypes,hashlib,json,os,struct,sys,time,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tools/m4-pipeline'),str(HERE),str(ROOT/'tools/m4-crt-allocation-root')]
from capture_shared_v2 import SharedBundle,SharedDirectSet,MAGIC,FORMAT,_json,HEADER
from capture_bundle import CaptureBundle,sha_file
from manifests import verify_manifest
def need(value,why):
    if not value:raise ValueError(why)
def pin(files,path,expected=None):
    path=Path(path).resolve();sha=sha_file(path);need(expected is None or sha==expected,'Physical pin changed: '+str(path));files[str(path)]=sha;return path
def native_build(files):
    path=pin(files,ROOT/'reports/m4-capture-shared/build-r1/build.json');build=json.loads(path.read_text(encoding='utf-8-sig'));need(build['passed'],'Passed native writer build')
    for field in ('sources','tools','artifacts','objects','libraries','compiler_read_headers'):
        for name,digest in build[field].items():pin(files,name,digest)
    for name in ('capture_shared_v2.py','prepare_reader_v2.py','validate_pilot.py'):pin(files,HERE/name)
    for name in ('capture_bundle.py','paths.py','manifests.py'):pin(files,ROOT/'tools/m4-pipeline'/name)
    pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r1/report.json');pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r1/reader.diff')
    return build
def hardware(path):
    raw=path.read_bytes();need(len(raw)==60*1128,'Actual complete 60 pair sample stream');checks=0
    for at in range(0,len(raw),1128):
        b=raw[at:at+560];a=raw[at+560:at+1120];errors=struct.unpack_from('<II',raw,at+1120)
        need(errors==(0x734612ab,0x734612ab),'Actual caller LastError')
        need(b[512:540]==a[512:540] and any(b[524:532]),'Full ENV28 including nonzero pointer metadata')
        need(b[:5]==a[:5] and struct.unpack_from('<H',b)[0]==0xa7f,'Actual seeded x87 CW/SW/FTW')
        need(b[24:28]==a[24:28] and struct.unpack_from('<I',b,24)[0]==0x5fa5,'Actual seeded MXCSR')
        for i in range(8):need(b[32+16*i:42+16*i]==a[32+16*i:42+16*i],'Actual eight raw80 registers')
        for i in range(6,16):
            need(b[160+16*i:176+16*i]==a[160+16*i:176+16*i]==bytes((i*31+j*17+7)&255 for j in range(16)),'Actual nonvolatile XMM sentinels')
        need(struct.unpack_from('<Q',b,544)[0]&0x400==struct.unpack_from('<Q',a,544)[0]&0x400==0x400,'Actual set direction flag')
        checks+=24
    return {'pairs':60,'independent_field_checks':checks,'volatile_XMM0_5_claimed':False,'raw_sha256':sha_file(path)}
def lock_attempts(owner,path):
    need(os.name=='nt','This pilot explicitly requires Windows readonly ownership')
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];api.CreateFileW.restype=ctypes.c_void_p;api.CloseHandle.argtypes=[ctypes.c_void_p];api.DeleteFileW.argtypes=[ctypes.c_wchar_p];api.MoveFileExW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32]
    before=sha_file(path);observations=[]
    handle=api.CreateFileW(str(path),0x40000000,3,None,3,0x80,None);err=ctypes.get_last_error()
    if handle!=ctypes.c_void_p(-1).value:api.CloseHandle(handle)
    need(handle==ctypes.c_void_p(-1).value and err==32,'Held file must refuse writable open with sharing violation');observations.append({'operation':'writable-open','error':err})
    result=api.DeleteFileW(str(path));err=ctypes.get_last_error();need(not result and err==32,'Held file must refuse deletion');observations.append({'operation':'delete','error':err})
    target=path.with_name('held-rename-target-'+path.name);need(not target.exists(),'Fresh held rename probe');result=api.MoveFileExW(str(path),str(target),0);err=ctypes.get_last_error();need(not result and err==32,'Held file must refuse rename');observations.append({'operation':'rename','error':err})
    need(path.exists() and sha_file(path)==before and not target.exists(),'Read ownership probes preserve exact original file');return observations
def validate_controls(files):
    result={}
    for level in ('O0','O2'):
        folder=ROOT/f'reports/m4-capture-shared/controls-r1-{level}';actual=json.loads((folder/'controls.json').read_bytes());need(actual['passed'] and actual['hardware_pairs']==60 and actual['refusals']==27 and actual['default_limit_records']==200001,'Actual native fixture counts')
        unions={};lock_records=[]
        for name in ('count-split','split-0','split-1','split-2','default-overflow','factory','collision'):
            manifest=folder/name/'transport.json'
            with SharedDirectSet(manifest,sha_file(manifest)) as data:
                need(len(data.entries)==data.meta['logical_files'],'Complete logical inventory')
                for logical in data.entries:
                    value=data.data(logical)
                    if name=='count-split':expected=b'' if logical=='z/empty' else bytes(range(256))
                    elif name=='split-0':i=ord(logical)-ord('a');expected=bytes((i,i+1))
                    elif name=='collision':
                        modified=bytes(range(255))+bytes([127]);expected={'a/original':bytes(range(256)),'b/one-byte-change':modified,'c/repeated-change':modified,'d/different-size':bytes(range(255)),'e/empty':b''}[logical]
                    else:expected=b''
                    need(value==expected,'Exact independent authored input bytes: '+name+'/'+logical)
                if name=='collision':
                    need(data.data('b/one-byte-change') is data.data('c/repeated-change'),'Repeated logical record reuses one immutable authenticated blob')
                    need(data.meta['unique_blobs']==4 and data.meta['unique_payload_bytes']==767,'Collision/full bytes/native copy evidence')
                    saved=data.data('a/original')
                    try:saved[0]=0
                    except TypeError:pass
                    else:raise ValueError('Reader returned mutable bytes')
                    for path in (manifest,data.readers[0].path):lock_records.extend(lock_attempts(data,path))
                    need(data.data('a/original')==saved,'Unchanged authenticated read after refused mutations')
                unions[name]={key:data.meta[key] for key in ('logical_files','payload_bytes','unique_blobs','unique_payload_bytes')};unions[name]['parts']=len(data.readers)
            try:data.data('absent')
            except ValueError:pass
            else:raise ValueError('Closed owner read admitted')
        for path in folder.rglob('*'):
            if path.is_file():pin(files,path)
        result[level]={'native_receipt':actual,'hardware':hardware(folder/'hardware.bin'),'unions':unions,'held_readonly_probes':lock_records}
    return result
def archive(index,payload,raw_index=None,magic=MAGIC,index_sha=None,trailer=b''):
    raw=_json(index) if raw_index is None else raw_index
    return HEADER.pack(magic,len(raw),hashlib.sha256(raw).digest() if index_sha is None else index_sha)+raw+payload+trailer
def corruptions(out):
    source=ROOT/'reports/m4-capture-shared/controls-r1-O0/collision/part-1.mwb';raw=source.read_bytes();_,size,_=HEADER.unpack(raw[:48]);base=json.loads(raw[48:48+size]);payload=raw[48+size:];tests=[]
    def reject(name,value,expected,external=None):
        path=out/(name+'.mwb');path.write_bytes(value);error=None
        try:
            with SharedBundle(path,external or hashlib.sha256(value).hexdigest()):pass
        except (ValueError,OSError,KeyError,TypeError) as exc:error=str(exc)
        need(error is not None and expected in error,'Corruption cause not reached: '+name+' '+str(error));tests.append({'name':name,'rejection':error,'sha256':sha_file(path)})
    reject('outer-pin',raw,'External shared bundle',external='0'*64)
    reject('magic',archive(base,payload,magic=b'MW34CAP1'),'header')
    reject('index-hash',archive(base,payload,index_sha=b'\0'*32),'index hash')
    reject('index-noncanonical',archive(base,payload,raw_index=json.dumps(base,indent=2).encode()),'Noncanonical')
    duplicate=_json(base).replace(b'"format":',b'"format":"duplicate","format":',1);reject('duplicate-json-key',archive(base,payload,raw_index=duplicate),'Duplicate JSON')
    cases=[('format','Invalid shared index',lambda x:x.update(format='unknown')),('index-field','schema',lambda x:x.update(extra=1)),('unique-count','exact extent',lambda x:x.update(unique_bytes=x['unique_bytes']+1)),('logical-count','logical payload',lambda x:x.update(logical_bytes=x['logical_bytes']+1)),('offset-gap','Noncontiguous',lambda x:x['blobs'][0].update(offset=1)),('offset-overlap','Noncontiguous',lambda x:x['blobs'][1].update(offset=0)),('size-bool','Invalid blob size',lambda x:x['blobs'][0].update(size=True)),('digest-syntax','lowercase SHA256',lambda x:x['blobs'][0].update(sha256='A'*64)),('blob-digest','blob SHA256',lambda x:x['blobs'][0].update(sha256='0'*64)),('id-out-of-range','reference',lambda x:x['files'][0].update(blob_id=999)),('id-bool','reference',lambda x:x['files'][0].update(blob_id=True)),('id-negative','reference',lambda x:x['files'][0].update(blob_id=-1)),('name-traversal','component',lambda x:x['files'][0].update(path='../outside')),('name-duplicate','normalized',lambda x:x['files'][1].update(path=x['files'][0]['path'].upper())),('unsorted','Unsorted',lambda x:x['files'].reverse()),('unreferenced','Unreferenced',lambda x:x['files'].__setitem__(3,{'blob_id':0,'path':x['files'][3]['path']}))]
    for name,expected,mutate in cases:index=copy.deepcopy(base);mutate(index);reject(name,archive(index,payload),expected)
    reject('payload-one-byte',archive(base,bytes([payload[0]^1])+payload[1:]),'blob SHA256')
    reject('truncated',raw[:-1],'exact extent') # final empty blob keeps prior extent valid, trailing extent check catches.
    reject('trailing',raw+b'x','trailing')
    index={'blobs':[{'offset':0,'sha256':hashlib.sha256(b'a').hexdigest(),'size':1},{'offset':1,'sha256':hashlib.sha256(b'a').hexdigest(),'size':1}], 'files':[{'blob_id':0,'path':'a'},{'blob_id':1,'path':'b'}],'format':FORMAT,'logical_bytes':2,'unique_bytes':2};reject('redundant-physical-blob',archive(index,b'aa'),'Duplicate physical')
    try:
        with CaptureBundle(source,sha_file(source)):pass
    except ValueError as exc:need('header' in str(exc),'Old reader rejects new magic explicitly')
    else:raise ValueError('Old reader silently accepted shared format')
    return tests
def manifest_corruptions(out):
    source=ROOT/'reports/m4-capture-shared/controls-r1-O0/count-split';base=json.loads((source/'transport.json').read_bytes());tests=[]
    def test(name,mutate,expected,extra=None):
        target=out/name;target.mkdir();meta=copy.deepcopy(base);mutate(meta)
        for part in base['parts']:(target/part['bundle']).write_bytes((source/part['bundle']).read_bytes())
        if extra:(target/extra).write_bytes(b'x')
        path=target/'transport.json';path.write_bytes(_json(meta));error=None
        try:
            with SharedDirectSet(path,sha_file(path)):pass
        except (ValueError,OSError) as exc:error=str(exc)
        need(error is not None and expected in error,'Manifest corruption cause: '+name+' '+str(error));tests.append({'name':name,'rejection':error,'sha256':sha_file(path)})
    test('unknown-direct-format',lambda x:x.update(format='unknown'),'declaration')
    test('duplicate-part',lambda x:x['parts'].append(x['parts'][0]),'part name')
    test('part-logical-count',lambda x:x['parts'][0].update(logical_files=9),'count mismatch')
    test('part-unique-count',lambda x:x['parts'][0].update(unique_blobs=9),'count mismatch')
    test('set-payload',lambda x:x.update(payload_bytes=99),'count mismatch')
    test('outer-part-pin',lambda x:x['parts'][0].update(sha256='0'*64),'External shared bundle')
    test('extra-physical',lambda x:None,'physical inventory','extra.bin')
    return tests
def main(directory):
    out=Path(directory).resolve();need(out.parent==ROOT/'reports/m4-capture-shared' and not out.exists(),'Fresh pilot validation receipt');out.mkdir();files={};report={'passed':False,'format_adopted':False,'game_executed':False,'transport_only':True}
    try:
        native_build(files);report['controls']=validate_controls(files)
        (out/'corrupt').mkdir();report['blob_corruptions']=corruptions(out/'corrupt')
        (out/'manifest-corrupt').mkdir();report['manifest_corruptions']=manifest_corruptions(out/'manifest-corrupt')
        for path in out.rglob('*'):
            if path.is_file():pin(files,path)
        report.update(passed=True,native_transport_executed=True,hardware_pairs=120,actual_refusals=54,corruption_refusals=len(report['blob_corruptions'])+len(report['manifest_corruptions'])+1,held_readonly_refusals=12,current_physical_closure=verify_manifest(files),files=files,logical_semantics='Every exact logical name returns immutable original bytes. Blobs are authenticated once at open; no payload or count is derived from game AFTER evidence.',scope='Authored transport fixtures only; no production consumer adoption or game credit')
    except BaseException as exc:report.update(error=str(exc),traceback=traceback.format_exc(),files=files);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','controls','blob_corruptions','manifest_corruptions')}))
if __name__=='__main__':main(*sys.argv[1:])
