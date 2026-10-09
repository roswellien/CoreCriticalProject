"""Independent iterative wire/source review of the host-only asset parser."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def require(ok,why):
    if not ok:raise ValueError(why)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def parse_wire(data,base):
    nodes=[];cursor=0;frames=[[None,1]]
    while frames:
        parent,remaining=frames[-1]
        if remaining==0:
            if parent is not None:nodes[parent]['end']=base+cursor
            frames.pop();continue
        frames[-1][1]-=1
        require(len(frames)<=130 and len(nodes)<1000000 and cursor+8<=len(data),'Iterative token bounds')
        kind,value=struct.unpack_from('<II',data,cursor);begin=cursor;cursor+=8
        require(kind in (1,2,3,4),'Unknown wire token')
        item={'index':len(nodes),'type':kind,'offset':base+begin}
        nodes.append(item)
        if parent is not None:nodes[parent]['children'].append(item['index'])
        if kind in (1,2):item['word']=value
        elif kind==3:
            require(value<=16*1024*1024 and cursor+value<=len(data),'Wire string bounds')
            item['string_offset']=base+cursor;item['string_hex']=data[cursor:cursor+value].hex();cursor+=value
        else:
            require(1<=value<=0x7fffffff and value-1<=(len(data)-cursor)//8,'Wire list bounds')
            item['children']=[];frames.append([item['index'],value-1])
        if kind!=4:item['end']=base+cursor
    require(cursor==len(data),'Wire trailing bytes')
    return nodes

def main():
    out=ROOT/'reports/m4-assets/independent-root-r1'
    require(not out.exists(),'Fresh asset review required')
    buildpath=ROOT/'reports/m4-assets/parser-r1/build.json'
    require(sha(buildpath)=='8d648bda3890a0b5eb38396a920a856bb4b67df0d1ead8047c066be708926b0f','Frozen parser build changed')
    build=json.loads(buildpath.read_text())
    bindings={}
    for group in ('source_files','tool_files','artifacts'):
        for path,digest in build[group].items():
            require(sha(path)==digest,'Parser binding changed: '+path);bindings[path]=digest
    for item in build['literal_source_copies']:
        require(Path(item['original_path']).read_bytes()==Path(item['preserved_path']).read_bytes(),'Source snapshot differs')
        bindings[item['preserved_path']]=item['sha256']
    archive=ROOT/'MW3/zbd/reader.zbd'
    require(sha(archive)=='5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a','Reader source identity differs')
    data=archive.read_bytes();version,count=struct.unpack_from('<II',data,len(data)-8)
    require(version==1 and count==178,'Actual directory footer differs')
    directory=len(data)-8-148*count
    entries=[]
    for i in range(count):
        start=directory+i*148;position,size=struct.unpack_from('<II',data,start)
        require(position+size<=directory,'Actual payload range differs')
        name=data[start+8:start+72].split(b'\0',1)[0].decode('latin1')
        entries.append({'index':i,'directory_offset':start,'offset':position,'bytes':size,'name':name,
                        'opaque_word':struct.unpack_from('<I',data,start+72)[0],'metadata_hex':data[start+76:start+148].hex()})
    out.mkdir(parents=True)
    commands=[]
    def run(name,args):
        p=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,timeout=35)
        (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
        commands.append({'name':name,'command':list(map(str,args)),'exit_code':p.returncode})
        require(p.returncode==0 and not p.stderr,'Native parser review command failed: '+name)
        return p.stdout
    host=ROOT/'build/m4-assets-parser-r1/mw34_m4_assets.exe'
    controls=run('authored-controls',[ROOT/'build/m4-assets-parser-r1/mw34_m4_assets_tests.exe'])
    require(b'51' in controls,'Authored control count differs')
    actual=json.loads(run('directory',[host,'--directory',archive]))
    require(actual['entries']==entries and actual['directory_offset']==directory and actual['source']['sha256']==sha(archive),'Complete native directory differs')
    documents=[]
    for name in ('dialog.zrd','detail.zrd','fonts.zrd','sounds.zrd'):
        entry=next(e for e in entries if e['name']==name)
        payload=data[entry['offset']:entry['offset']+entry['bytes']]
        nodes=parse_wire(payload,entry['offset'])
        args=[host,'--document',archive,name]+(['MAINMENU'] if name=='dialog.zrd' else [])
        native=json.loads(run(name,args));observed=native['document']
        require(observed['nodes']==nodes and observed['payload_sha256']==hashlib.sha256(payload).hexdigest() and
                observed['view_offset']==entry['offset'] and observed['view_bytes']==entry['bytes'],
                'Complete native token/span/bit stream differs: '+name)
        require(not native['original_x86_executed'] and not native['widgets_created'],'Incorrect execution scope')
        label=None
        if name=='dialog.zrd':
            parents={child:(n['index'],i) for n in nodes if n['type']==4 for i,child in enumerate(n['children'])}
            match=next(n for n in nodes if n['type']==3 and bytes.fromhex(n['string_hex']).split(b'\0')[0]==b'MAINMENU')
            parent,index=parents[match['index']];label=nodes[parent]['children'][index+1]
            require(native['label_node']==label and nodes[label]['offset']==85822,'Actual MAINMENU successor/span differs')
        documents.append({'name':name,'nodes':len(nodes),'source_span':[entry['offset'],entry['offset']+entry['bytes']],
                          'payload_sha256':hashlib.sha256(payload).hexdigest(),'MAINMENU_node':label})
    # Both root and author source models are static format discovery. No
    # original reader/widget machine code is executed or replaced here.
    result={'passed':True,'scope':'Independent iterative byte-model/native parser agreement; host-only asset prerequisite',
            'bindings_rehashed':len(bindings),'authored_controls_replayed':51,'directory_records':178,
            'documents':documents,'tokens':sum(d['nodes'] for d in documents),'commands':commands,
            'source_review':['Immutable owner retained by views','Subview/token/string/count arithmetic bounded before use',
                'Absolute spans and numeric/string raw bits retained','No host pointer used as guest object/handle',
                'ASCII lookup, DFS label successor, synthetic list slot and absent wire string terminator explicitly scoped'],
            'limits':['No original reader/provider/parser execution proof','No textual document fallback or full locale service',
                'Original shared HANDLE cursor/object/guest heap layout unimplemented','Native widgets/graphics/input/audio/menus remain open',
                'Malformed input rejections are bounded host policy, not original failure equivalence'],
            'M4_complete':False}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    require(sha(archive)=='5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a','Reader mutated during review')
    bindings[str(archive)]=sha(archive);bindings[str(buildpath)]=sha(buildpath);bindings[str(Path(__file__).resolve())]=sha(__file__)
    for path in out.rglob('*'):
        if path.is_file():bindings[str(path.resolve())]=sha(path)
    (out/'pins.json').write_text(json.dumps({'files':bindings},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':True,'tokens':result['tokens'],'bindings':len(bindings),'M4_complete':False}))

if __name__=='__main__':main()
