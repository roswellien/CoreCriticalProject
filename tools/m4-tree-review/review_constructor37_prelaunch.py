"""Independent physical admission for bounded original constructor chronology."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='75651d2e01281c8bfea102bdf4d8b32649eeff379789afadc1d2079fd6f1d507'
BH='bcf2cc5e4c9e197cf99374a47f136fa88db2e6e48fe558bc8ba565628aeeb054'

def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
    files={};counts=collections.Counter();links=[];passed=False
    def pin(path,identity=None):
        path=Path(path).resolve();assert path.suffix.lower()not in('.zip','.mwb')
        value=sha(path);assert identity is None or value==identity,(path,identity,value)
        assert str(path)not in files or files[str(path)]==value;files[str(path)]=value;return path
    def read(path,identity=None):return json.loads(pin(path,identity).read_bytes())
    def load(path,name):
        spec=importlib.util.spec_from_file_location(name,pin(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def sparse(path,identity):
        data=pin(path,identity).read_bytes();n=struct.unpack_from('<I',data,8)[0];assert len(data)==12+n*4104
        result={struct.unpack_from('<I',data,12+4104*i)[0]:(struct.unpack_from('<I',data,16+4104*i)[0],data[20+4104*i:4116+4104*i])for i in range(n)};assert len(result)==n;return result
    try:
        folder=R/'reports/m4-constructor-original/chronological-preparation-r4';bf=R/'reports/m4-constructor-original/chronological-build-r2'
        p=read(folder/'report.json',PH);b=read(bf/'build.json',BH)
        assert p['passed']and b['passed']and b['preparation_sha256']==PH
        for receipt,field in((p,'files'),(b,'sources')):
            for q,h in receipt[field].items():pin(q,h)
        assert(p['original_roots'],p['original_sequences'],p['original_phases'],p['record_bytes'],p['source_frame'])==(37,6,222,356992,0x20001800)
        assert not p['writer_executed']and not p['writer_admitted']and not p['capture_archive_opened']and p['initializer_credit']==0
        parent_path=R/'reports/m4-startup131-original/preparation-r4/report.json'
        parent=read(parent_path,'1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
        contract=read(folder/'contracts.json')
        new=[dict(entry=0x4103f0,slot=0x5e0038),dict(entry=0x410440,slot=0x5e003c),dict(entry=0x459b40,slot=0x5e00a0)]
        expected=sorted([x for x in parent['selected_order']if x['slot']<=0x5e00a0]+new,key=lambda x:x['slot'])
        assert p['selected_order']==contract['selected_order']==expected
        assert expected[13:16]==new[:2]+[dict(entry=0x5ae3e4,slot=0x5e0040)]and expected[36]==new[2]
        assert contract['MFC1168_phase']==15 and contract['source_AFTER_seed']is False
        assert contract['omitted_unaccepted_widget_slots'],'Selected chronology must explicitly distinguish omitted slots'
        PE=load(R/'tools/analysis/pe.py','ctor37_physical_pe')
        game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        cp=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        def physical(image,address,size):start,_=image.rva_range(address-image.image_base,size);return image.data[start:start+size]
        pack=sparse(folder/'pages.bin',p['pack_sha256']);oldpack=sparse(parent_path.parent/'pages.bin',parent['pack_sha256'])
        assert len(pack)==149 and len(oldpack)==134
        overlay=read(folder/'source-overlay.json');deltas={}
        for row in overlay:
            address=row['address'];before=bytes.fromhex(row['old_hex']);after=bytes.fromhex(row['source_hex']);assert len(before)==len(after)
            assert after==physical(game,row['physical_source_PC'],len(after))
            for offset,value in enumerate(after):
                at=address+offset;assert at not in deltas or deltas[at]==value;deltas[at]=value
                assert pack[at&~4095][1][at&4095]==value
            counts['whole_physical_overlay_spans']+=1
        for address,(permission,before)in oldpack.items():
            assert pack[address][0]==permission
            for offset,(a,z)in enumerate(zip(before,pack[address][1])):
                if a!=z:assert permission==1 and a==0xcc and deltas.get(address+offset)==z;counts['exact_prior_CC_to_source_bytes']+=1
            counts['whole_retained_pack_pages']+=1
        for address,(permission,data)in pack.items():
            assert address%4096==0 and len(data)==4096 and permission in(1,2)
            if address not in oldpack and permission==2:assert data==physical(game,address,4096);counts['whole_new_physical_data_pages']+=1
        for row in p['source_spans']:
            image=cp if row['origin']else game;data=physical(image,row['pc'],row['size']);assert image.data[row['image_offset']:row['image_offset']+row['size']]==data
            if not row['origin']:
                for offset,value in enumerate(data):assert pack[(row['pc']+offset)&~4095][1][(row['pc']+offset)&4095]==value
            counts['whole_physical_source_spans']+=1
        for row in expected:
            assert struct.unpack('<I',physical(game,row['slot'],4))[0]==row['entry']==struct.unpack_from('<I',pack[row['slot']&~4095][1],row['slot']&4095)[0];counts['physical_selected_pairs']+=1
        broker=pin(folder/'original_broker.hpp').read_text();bases=[int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]
        assert all(address&~65535 in bases for address in pack)
        asm=pin(folder/'constructor_observer_x86.asm').read_text();bindings=read(folder/'constructor-hook-bindings.json');assert len(bindings)==8
        for row in bindings:
            data=bytes.fromhex(row['raw_bytes']);assert data==physical(game,row['return_PC'],len(data))and row['continuation']==row['return_PC']+len(data)
            block=asm[asm.index(row['symbol']+' PROC'):asm.index(row['symbol']+' ENDP')]
            db=' db '+','.join('0%02xh'%v for v in data)
            assert db in block and 'jmp DWORD PTR ctor_continue_%x'%row['return_PC']in block
            for token in('fxsave ctor_fx','fnstenv ctor_env','fldenv ctor_env','fxrstor ctor_fx','call ctor_observe','mov esp,mixed_host_esp','mov esp,DWORD PTR ctor_cpu[16]'):assert token in block
            counts['whole_normal_stolen_return_bytes']+=1
        assert 'mov eax,DWORD PTR [ecx+4]'in asm and 'ret'in asm
        observer=pin(folder/'constructor_normal.hpp').read_text()
        for token in('sizeof(ConstructorNormalSnapshot)==189108','constructor_normal_count>=256','capacity==v.capacity','safe_read','seen.size()<256','dword(header+4)==previous'):assert token in observer
        cpp=pin(folder/'reference.cpp').read_text();main_cpp=cpp[cpp.index('int main('):]
        for token in('if(phase){mixed_input=mixed_after;','require(phase==15','constructor_graph(phase_stem+"/BEFORE-constructor")','constructor_member_graph(phase_stem+"/AFTER-member")','constructor_whole_live_owners(phase_stem+"/BEFORE-owners")','constructor_normal_dump(phase_stem+"/normal")','mfc825(reinterpret_cast<void*>(v.pointer))'):assert token in main_cpp
        assert main_cpp.index('Actual original823 named owning target')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('Restore exact original823 named target')<main_cpp.index('constructor_normal_dump(phase_stem+"/normal")')
        assert main_cpp.index('Constructor source observer permissions')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('Restore actual constructor source')
        assert 'if(phase<15)constructor_collect' in main_cpp
        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','ctor37_actual_coff')
        worker=PE.PEImage(pin(b['worker'],b['worker_sha256']).read_bytes());assert worker.machine==0x14c and worker.image_base==0x18000000
        release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
        for obj in sorted(release.glob('*.obj')):
            if obj.name=='reference.obj':continue
            sy,se=C.coff(pin(obj).read_bytes());sections=[i for i,v in se.items()if v['flags']&0x20000000 and v['bytes']]
            if not sections:continue
            assert len(sections)==1
            name=obj.stem+' complete assembly';fake={0:dict(name=name,value=0,section=sections[0],type=0x20,storage=2)}
            proof=C.linked_function(worker,fake,se,name);links.append(proof);counts['whole_linked_ASM_sections']+=1;counts['whole_linked_ASM_bytes']+=proof['bytes']
        sy,se=C.coff(pin(release/'reference.obj').read_bytes())
        names=['_main','_observe_boundary','_observe_named_API','_ctor_observe']+[v['name']for v in sy.values()if v['type']==0x20 and v['section']>0 and any(v['name'].startswith(a)for a in('?constructor_collect@@','?constructor_graph@@','?constructor_member_graph@@','?constructor_whole_live_owners@@','?constructor_normal_dump@@'))]
        assert len(names)==9
        for name in names:proof=C.linked_function(worker,sy,se,name);links.append(proof);counts['whole_linked_CPP_functions']+=1
        consumed=set();tlogs=list(release.rglob('CL.read.1.tlog'));assert len(tlogs)==1
        for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
            path=Path(line.strip().lstrip('^'))
            if path.is_absolute()and path.is_file():consumed.add(pin(path))
        assert all((folder/leaf).resolve()in consumed for leaf in('protocol.hpp','spec.hpp','constructor_normal.hpp','connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','original_broker.hpp'))
        counts['actual_compiler_input_files']=len(consumed)
        log=pin(bf/'compile.log').read_text();assert '/MACHINE:X86'in log and '/W4 /WX'in log and '0 Warning(s)'in log and '0 Error(s)'in log
        pin(R/'tools/m4-constructor-original/run.py');pin(__file__);pin(sys.executable)
        for path,identity in files.items():assert sha(path)==identity
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        path=out/'physical-links.json';path.write_text(json.dumps(links,indent=2)+'\n');pin(path)
        report=dict(passed=passed,scope='Independent physical37-root selected original chronology; all omitted unaccepted slots explicit, actual constructors and source/resource equivalence uncredited before execution',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),worker_launched=False,capture_archive_reader_opened=False,initializer_credit=0,files=files)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(path),counts=dict(counts),files=len(files))))

if __name__=='__main__':main(sys.argv[1])
