"""Stage completed, registered local assets without touching game installations."""
from pathlib import Path
import array,hashlib,json,os,struct,sys
try:
    from PIL import Image
except ImportError as exc:
    raise RuntimeError(
        'Pillow could not be loaded by '+sys.executable+
        '. Launch through Play MW3Remaster.cmd to select a runtime with Pillow.'
    ) from exc

def write_atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);os.replace(temp,path)

def prepare(root,models):
    folder=root/'local/remaster/prepared';folder.mkdir(parents=True,exist_ok=True)
    manifest=root/'local/work-ahead/texture-launcher-audit-v2/configured-banks.json'
    rows=json.loads(manifest.read_text(encoding='utf-8-sig'))
    local_cache=folder/'bank-hashes.json'
    shared=root/'local/work-ahead/mw3-d7vk-wrapper/launcher-hash-cache.json'
    cache=json.loads((local_cache if local_cache.exists() else shared).read_text()) if local_cache.exists() or shared.exists() else {}
    banks=bytearray(b'MWBANK1\0'+struct.pack('<I',len(rows)));receipt=[];base=root/'local/work-ahead/training-terrain-game-test/install'
    for row in rows:
        relative=Path(row['target']).relative_to(base).as_posix().lower()
        if not relative.startswith('zbd/') or '..' in relative.split('/'):raise RuntimeError('Invalid published bank target '+relative)
        source=Path(row['source']);st=source.stat();key=str(source.resolve()).lower();record=cache.get(key,{})
        if record.get('size')==st.st_size and record.get('mtime_ns')==st.st_mtime_ns:digest=record['sha256']
        else:
            print('Verifying texture bank '+relative,flush=True)
            with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            after=source.stat()
            if (st.st_size,st.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Texture bank changed during verification')
            cache[key]=dict(size=st.st_size,mtime_ns=st.st_mtime_ns,sha256=digest)
        if digest.lower()!=row['expected_sha256'].lower():raise RuntimeError('Published texture bank hash mismatch: '+relative)
        a=relative.encode();b=str(source.resolve()).encode();banks.extend(struct.pack('<II',len(a),len(b)));banks.extend(a);banks.extend(b)
        receipt.append(dict(bank=relative,source=str(source),sha256=digest))
    write_atomic(local_cache,json.dumps(cache,indent=1).encode());bankfile=folder/'texture-banks.bin';write_atomic(bankfile,banks)
    environment={'MW34_REMASTER_BANKS':str(bankfile)}
    model_receipts=[]
    for model in models:
        # An adapter can only be published once its executable implements these bindings.
        for key,value in model.get('environment',{}).items():
            if not key.startswith('MW34_'):raise RuntimeError('Invalid model environment binding')
            path=root/value
            if not path.is_file():raise RuntimeError('Model payload missing: '+str(path))
            environment[key]=str(path)
        if not model.get('textures'):continue
        metadata=json.loads((root/model['batch_metadata']).read_text());names=list(model['textures']);count=len(metadata['batches'])
        out=bytearray(b'BWTEX1\0\0'+struct.pack('<II',count,len(names)))
        out.extend(struct.pack('<'+'I'*count,*[names.index(b['material']) for b in metadata['batches']]))
        for name,relative in model['textures'].items():
            source=root/relative;im=Image.open(source).convert('RGB');im.thumbnail((2048,2048),Image.Resampling.LANCZOS);im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            pixels=array.array('H',(((r>>3)<<11)|((g>>2)<<5)|(b>>3) for r,g,b in im.getdata()))
            if sys.byteorder!='little':pixels.byteswap()
            data=pixels.tobytes();digest=hashlib.sha256(data).digest();out.extend(name.encode().ljust(32,b'\0'));out.extend(struct.pack('<IIQ',*im.size,int.from_bytes(digest[:8],'little')));out.extend(data)
        path=folder/(model['id']+'-textures.bin');write_atomic(path,out);environment[model['texture_environment']]=str(path)
        model_receipts.append(dict(id=model['id'],sidecar=str(path),sha256=hashlib.sha256(out).hexdigest(),texture_sources=model['textures']))
    write_atomic(folder/'asset-receipt.json',json.dumps(dict(banks=receipt,models=model_receipts),indent=2).encode())
    return environment
