"""Make two disjoint bounded byte-identical bounded copy views of a completed immutable native tree."""
import json,os,re,shutil,stat,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import MAX_FILES,MAX_FILE,sha_file
from paths import logical_name,publish_bytes,reject_reparse,workspace_path

def need(ok,why):
    if not ok:raise ValueError(why)

def scan(source):
    files={}
    for current,directories,filenames in os.walk(source,followlinks=False):
        for child in directories+filenames:
            info=reject_reparse(Path(current)/child)
            need(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),'Only regular source capture entries')
        for filename in filenames:
            path=Path(current)/filename;name=logical_name(path.relative_to(source).as_posix())
            need(name.casefold() not in files,'Unique native logical path')
            size=path.stat().st_size;need(0<=size<=MAX_FILE,'Unchanged individual transport extent limit')
            files[name.casefold()]=(name,path,size)
    need(files and len(files)<=2*MAX_FILES,'Bounded aggregate source tree')
    return tuple(sorted(files.values()))

def main(tree,target,manifest):
    source=workspace_path(tree,reports=True);out=workspace_path(target,reports=True);receipt=workspace_path(manifest,reports=True)
    need(source.is_dir() and not out.exists() and not receipt.exists(),'Completed source and fresh partition destination')
    need(not out.is_relative_to(source) and not source.is_relative_to(out),'Separate original and copy view namespaces')
    need((source/'COMPLETE').read_bytes()==b'COMPLETE','Native completion marker before partitioning')
    initial=scan(source);out.mkdir();roots=[out/'part-1',out/'part-2']
    for root in roots:root.mkdir()
    maps=[{},{}];records={};made=set();root_entries=set();cases=set();diagnostics=set()
    for name,path,size in initial:
        top=name.split('/',1)[0]
        match=re.fullmatch(r'case-([1-9][0-9]*)',top)
        if match:
            number=int(match[1]);need(1<=number<=122,'Exact bounded native case range');part=0 if number<=61 else 1;cases.add(number)
        elif top in ('direct-query-failure-1','direct-query-failure-2'):
            diagnostics.add(top);part=0
        else:
            need(name==top and name in ('COMPLETE','controls.json'),'Closed native root metadata');root_entries.add(top);part=0
        need(len(maps[part])<MAX_FILES,'Each original strict archive stays within file limit')
        row={'bytes':size,'sha256':sha_file(path)};destination=roots[part]/name
        if destination.parent not in made:destination.parent.mkdir(parents=True,exist_ok=True);made.add(destination.parent)
        shutil.copyfile(path,destination)
        need(destination.stat().st_size==size and sha_file(destination)==row['sha256'] and sha_file(path)==row['sha256'],'Exact original-file copy identity')
        records[name]=row;maps[part][name]=row
    need(cases==set(range(1,123)) and root_entries=={'COMPLETE','controls.json'} and diagnostics=={'direct-query-failure-1','direct-query-failure-2'},'Full closed integrated and separate diagnostic corpus')
    need(scan(source)==initial,'Original native tree inventory unchanged by partitioning')
    need(not(set(maps[0])&set(maps[1])) and set(maps[0])|set(maps[1])==set(records),'Exact disjoint logical union')
    for i,root in enumerate(roots):
        need(tuple(name for name,_,_ in scan(root))==tuple(sorted(maps[i])),'Exact bounded hardlink partition inventory')
    result={'passed':True,'scope':'Hardlink views only; no native execution or hardware success credit','source':str(source),'source_files_modified':False,'hardlinks_only':False,'byte_identical_copies_only':True,'original_relative_paths_preserved':True,'logical_files':len(records),'files':dict(sorted(records.items())),'parts':[{'part':i+1,'pack_source':str(root),'logical_files':len(maps[i]),'files':dict(sorted(maps[i].items()))} for i,root in enumerate(roots)],'native_executed':False,'original_executed':False,'transport_limit_unchanged':MAX_FILES}
    publish_bytes(receipt,(json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'passed':True,'manifest_sha256':sha_file(receipt),'logical_files':len(records),'part_counts':[len(m) for m in maps]}))

if __name__=='__main__':main(*sys.argv[1:])
