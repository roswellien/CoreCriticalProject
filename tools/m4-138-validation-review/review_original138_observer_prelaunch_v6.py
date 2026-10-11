"""Retain all parent physical/link gates; invert exact three observer changes separately."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-tree-review/review_original138_prelaunch_v5.py'
scope={'__file__':str(p),'__name__':'materialize_review'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
changes=[]
def one(a,b):
 global t
 assert t.count(a)==1,a
 changes.append((a,b));t=t.replace(a,b,1)
one("PH = 'e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'", "PH = '9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'")
one("BH = '748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'", "BH = 'da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'")
one("out = R / 'reports/m4-tree-review' / name", "out = R / 'reports/m4-138-validation-review' / name")
one("folder = R/'reports/m4-startup138-original/preparation-r7'", "folder = R/'reports/m4-startup138-original/preparation-r8'")
one("bf = R/'reports/m4-startup138-original/build-r4'", "bf = R/'reports/m4-startup138-original/build-r5'")
one('        inverted=normalize(cpp)', '''        parentfolder=folder.with_name('preparation-r7')
        parentprep=read(parentfolder/'report.json','e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2')
        expected_changes=[
          ('if(i>=256||registry_API_kind!=0||!registry_API_after.eax)return;','if(i>=256||(registry_API_kind!=0&&registry_API_kind!=3)||!registry_API_after.eax)return;'),
          ('std::memcpy(registry_initial_bytes[i],pointer,size);fs_observe_allocation','std::memcpy(registry_initial_bytes[i],pointer,size);if(registry_API_kind!=0)return;fs_observe_allocation'),
          ('for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){require(registry_initial_sizes[ai]>=registry_API_ledger[ai].args[2]&&registry_initial_sizes[ai]<=1024,"Actual HeapAlloc initial backing captured before guest writes");','for(unsigned ai=0;ai<registry_API_count;++ai)if((registry_API_ledger[ai].kind==0||registry_API_ledger[ai].kind==3)&&registry_API_ledger[ai].after.eax){const auto requested=registry_API_ledger[ai].args[registry_API_ledger[ai].kind==3?3:2];require(registry_initial_sizes[ai]>=requested&&registry_initial_sizes[ai]<=1024,"Actual HeapAlloc/HeapReAlloc API-return backing captured before guest writes");')]
        assert [(d['old'],d['new']) for d in p['realloc_observer_delta']]==expected_changes
        previous=cpp
        for d in reversed(p['realloc_observer_delta']):
            pos=d['position'];assert previous[pos:pos+len(d['new'])]==d['new']
            previous=previous[:pos]+d['old']+previous[pos+len(d['new']):]
        assert previous==text(parentfolder/'reference.cpp')
        for f in parentfolder.iterdir():
            if f.is_file() and f.name not in ('report.json','pins.json','reference.cpp'):
                assert pin(f).read_bytes()==pin(folder/f.name).read_bytes()
                counts['whole_unchanged_parent_observer_inputs']+=1
        pin(R/'tools/m4-startup138-original/prepare_realloc_observer.py')
        pin(R/'tools/m4-tree-review/review_original138_prelaunch_v5.py')
        counts['exact_realloc_observer_changes_inverted']=3
        inverted=normalize(previous)''')
reverse=t
for a,b in reversed(changes):
 assert reverse.count(b)==1;reverse=reverse.replace(b,a,1)
assert reverse==scope['t']
exec(compile(t,str(Path(__file__)),'exec'),globals())
