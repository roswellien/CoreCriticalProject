"""Bind unaccepted native preflight and preserve its earlier compiler failure."""
import hashlib,json,shutil,re,struct,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    root=ROOT;out=root/'reports/m4-crt-matherr/preflight-seal-r2'
    assert not out.exists();out.mkdir()
    (out/'seal-source.py').write_bytes(Path(__file__).read_bytes())
    h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files={}
    bind=lambda p:files.setdefault(str(p.resolve()),h(p))
    try:
        for name in ['preparation-r1','abi-r1']:
            for p,s in json.loads((out.parent/name/'pins.json').read_text())['files'].items():
                assert h(Path(p))==s,p
                bind(Path(p))
            bind(out.parent/name/'pins.json')
        records=[];history=[]
        for name in ['native-build-r1','native-build-r2']:
            p=out.parent/name/'build.json'
            r=json.loads(p.read_text(encoding='utf-8-sig'));bind(p)
            for group in ['tool_files','artifacts']:
                for path,s in r[group].items():
                    assert h(Path(path))==s,path
                    bind(Path(path))
            for c in r['literal_sources']:
                preserved=Path(c['preserved_path']);assert h(preserved)==c['sha256'];bind(preserved)
                current=Path(c['original_path'])
                if h(current)!=c['sha256']:
                    history.append({'map':str(p),'original_path':str(current),'sha256':c['sha256'],'literal_path':str(preserved)})
                else:bind(current)
            for level in ['O0','O2']:
                b=p.parent/f'native-{level}.bin'
                if b.exists():
                    assert b.read_bytes()[:24]==b'MW4MTH01'+struct.pack('<4I',1,1536,3504,12288)
                    assert b.stat().st_size==50448408
                    records.append({'level':level,'path':str(b),'records':1536,'sha256':h(b)})
            for cmd in r['commands']:assert h(Path(cmd['log_path']))==cmd['log_sha256']
            assert (out.parent/name/'sources/tools/m4-crt-matherr').is_dir()
        headers=[]
        for level in ['O0','O2']:
            text=(out.parent/'native-build-r2'/f'build-{level}.log').read_text(encoding='utf-8-sig')
            for path in set(re.findall(r'Note: including file:\s+([^\r\n]+)',text)):
                p=Path(path.strip()).resolve();assert p.is_file();bind(p)
                headers.append({'level':level,'path':str(p),'sha256':h(p),'association':'actual compiler include log; post-build physical rehash'})
        assert len(records)==2 and len(history)==2
        assert {Path(x['original_path']).name for x in history}=={'context.hpp','build.ps1'}
        for p in (root/'tools/m4-crt-matherr').iterdir():
            if p.is_file():
                dest=out/'sources'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest);bind(p);bind(dest)
        for p in (out.parent/'preflight-seal-r1').iterdir():
            if p.is_file():bind(p)
        report={'passed':True,'scope':'Preflight source/lowering and actual native typed r9 service observations only; original differential/negative controls/independent acceptance pending',
            'native_observations':records,'actual_read_header_associations':headers,'historical_source_associations':history,
            'missing_header_compile_failure_preserved':True,'actual_game_CALL_site':0x5ac428,'actual_game_return_PC':0x5ac42e,
            'CALL_scope':'Static linkage plus authored r9 service orchestration; actual full CRT caller instructions not executed',
            'incoming_State_scope':'Declared raw3504byte patterns with CW/SW setting and no guest hardware FPU execution; coherent paired original FP corpus pending',
            'callback_invoked':False,'independent_acceptance':False,'whole_M4_complete':False}
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');bind(p);bind(out/'seal-source.py')
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'report_sha256':h(p),'pins_sha256':h(out/'pins.json'),'physical_bindings':len(files),
            'historical_sources':len(history),'post_build_header_records':len(headers),'native_records':3072}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main()
