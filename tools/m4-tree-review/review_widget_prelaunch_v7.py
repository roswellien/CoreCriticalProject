"""Independent current broker reservation coverage and complete observer review."""
from pathlib import Path
import hashlib
V5=Path(__file__).with_name('review_widget_prelaunch_v5.py')
V5_SHA='be3458ecd0ba96c871927c365b4d2c186d4b0ea3f32a3ed5a760a6024a49b5f4'
if hashlib.sha256(V5.read_bytes()).hexdigest()!=V5_SHA:raise ValueError('Immutable page/observer review')
program=V5.read_text()
anchor="exec(compile(source,str(BASE),'exec'),globals())"
if program.count(anchor)!=1:raise ValueError('One source checker invocation')
transform=r'''
old="asm = raw(directory / 'reference_x86.asm').decode()"
new="asm = raw(directory / 'reference_x86.asm').decode().replace('\\r\\n','\\n')"
if source.count(old)!=1:raise ValueError('One assembly CRLF grammar amendment')
source=source.replace(old,new,1)
anchor_pages="        sparse_pages = sparse(raw(directory / 'pages.bin'))"
amendment="""
        pin(V5,V5_SHA)
        previous=read(R/'reports/m4-tree-review/widget-prelaunch-r6/report.json','6d9081bba650a667d4d464c86348108d84bd56da7d910629e7a41b57cc440c71')
        need(previous['passed'] and previous['prelaunch_justified'], 'Exact independently reviewed prior observer/source candidate')
        old_directory=R/'reports/m4-widget-original/preparation-r8'
        changed=[]
        for old_file in old_directory.iterdir():
            if not old_file.is_file() or old_file.name=='report.json':continue
            new_file=directory/old_file.name
            need(new_file.is_file(),'Complete inherited prepared source file')
            if raw(old_file)!=raw(new_file):changed.append(old_file.name)
        eq(sorted(changed),['original_broker.hpp','reference.cpp'],'Only finite reservation inventory/commit diagnostic code changes')
        old_broker=raw(old_directory/'original_broker.hpp').decode()
        new_broker=raw(directory/'original_broker.hpp').decode()
        pattern=r'inline constexpr std::array<std::uint32_t,(\\d+)> bases\\{([^}]+)\\};'
        x=re.search(pattern,old_broker);y=re.search(pattern,new_broker)
        need(x and y,'Actual compiler broker base inventory')
        old_bases=[int(v,16) for v in x[2].split(',')];new_bases=[int(v,16) for v in y[2].split(',')]
        eq((len(old_bases),len(new_bases)),(34,35),'Measured current reservation inventory extent')
        eq(new_bases,old_bases+[0x5d0000],'Only exact missing physical page allocation base added')
        eq(old_broker[:x.start()]+old_broker[x.end():],new_broker[:y.start()]+new_broker[y.end():],'Every other broker byte preserved')
        current_pages=sparse(raw(directory/'pages.bin'))
        need(len(new_bases)==len(set(new_bases)) and all(base%65536==0 for base in new_bases),'Unique exact64KiB reservation bases')
        for page in current_pages:
            need(page&~65535 in new_bases and page+4096 <= (page&~65535)+65536,'Every159 complete actual source page fits reserved region')
        eq(sorted(set(page&~65535 for page in current_pages)-set(old_bases)),[0x5d0000],'Exact independently derived missing reservation')
        old_cpp=raw(old_directory/'reference.cpp').decode();new_cpp=raw(directory/'reference.cpp').decode()
        diagnostic='        if(pages[i]!=reinterpret_cast<void*>(page_bases[i]))std::cerr<<"Source page commit address="<<std::hex<<page_bases[i]<<" Win32="<<GetLastError()<<std::dec<<"\\\\n";'
        need(new_cpp.count(diagnostic)==1,'Exact finite pre-assert diagnostic hunk')
        eq(new_cpp.replace(diagnostic,'',1),old_cpp,'Every source phase/observer effect byte unchanged')
        need(new_broker.count('MEM_RESERVE')>=4 and 'reservation_size=0x10000' in new_broker.replace(' ','') and 'VirtualAllocEx(child.value,pointer,reservation_size,MEM_RESERVE,PAGE_NOACCESS)' in new_broker,'Actual pre-CRT fixed reservation admission')
        counts['complete_source_page_reservation_relations']=len(current_pages)
        counts['pre_CRT_reservation_bases']=len(new_bases)
        counts['exact_added_reservation_bases']=1
        pin(R/'tools/m4-widget-original/derive_prepare_v8.py')
        pin(R/'tools/m4-widget-original/prepare_v8.py')
"""
if source.count(anchor_pages)!=1:raise ValueError('One reservation/domain review seam')
source=source.replace(anchor_pages,anchor_pages+'\n'+amendment,1)
exec(compile(source,str(BASE),'exec'),globals())
'''
program=program.replace(anchor,transform,1)
exec(compile(program,str(V5),'exec'),globals())
