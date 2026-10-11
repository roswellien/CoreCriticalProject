"""Use physical MFC named exports, retaining their actual owning entry chain."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=here/'prepare_chronological_v5.py';target=here/'prepare_chronological_v6.py'
assert not target.exists();text=source.read_text()
def one(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new,1)
one("        contracts=read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json');newroots=contracts['roots'];", """        entry_chain=read(BASE/'entry-chain-r1/report.json','80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7');need(entry_chain['passed'],'Physical named MFC export and complete finite frame chain')
        for path,digest in entry_chain['files'].items():pin(path,digest)
        mfc_targets={int(ordinal):row['target']for ordinal,row in entry_chain['MFC_exports'].items()};need(set(mfc_targets)=={823,825},'Exact two physical named exports')
        contracts=read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json');newroots=contracts['roots'];""")
one("asm+=bridge('ctor_MFC_entry',0,0x5f401eb0,b'',' jmp DWORD PTR ctor_MFC_target')", "asm+=bridge('ctor_MFC_entry',0,mfc_targets[823],b'',' jmp DWORD PTR ctor_MFC_target')")
one("require(ctor_MFC_target==0x5f401eb0,\\\"Actual named ordinal823 physical entry\\\");", "require(ctor_MFC_target==__MFC823__,\\\"Actual named ordinal823 physical entry\\\");") if False else None
old="require(ctor_MFC_target==0x5f401eb0,\"Actual named ordinal823 physical entry\");"
assert text.count(old)==1
text=text.replace(old,"require(ctor_MFC_target==__MFC823__,\"Actual named ordinal823 physical entry\");",1)
one("        # The same genuine source cleanup is restricted to roots that actually", """        ref=one(ref,'__MFC823__',hex(mfc_targets[823]))
        required='require(reinterpret_cast<unsigned>(mfc825)=='+hex(mfc_targets[825])+',"Actual named ordinal825 physical export entry");require(dword(0x5bb4c8)==reinterpret_cast<unsigned>(mfc825),"Current owning game825 target equals actual physical named export");require(dword(0x5f49814c)==reinterpret_cast<unsigned>(GetProcAddress(crt,"malloc"))&&dword(0x5f498148)==reinterpret_cast<unsigned>(GetProcAddress(crt,"free")),"Actual MFC owning named CRT malloc/free imports");const std::array<unsigned,7>ctor_named_entries{1,ctor_MFC_target,reinterpret_cast<unsigned>(mfc825),dword(0x5bb4bc),dword(0x5bb4c8),dword(0x5f49814c),dword(0x5f498148)};out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries));'
        ref=one(ref,'const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");',required+'const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");')
        # The same genuine source cleanup is restricted to roots that actually""")
one("source_MFC_entry_target=0x5f401eb0,MFC1168_phase=15", "source_MFC_entry_target=mfc_targets[823],source_MFC_release_target=mfc_targets[825],source_MFC_entry_chain_sha256=sha(BASE/'entry-chain-r1/report.json'),source_MFC_HeapAlloc_frame_delta=entry_chain['MFC823_entry_to_HeapAlloc_before_delta'],MFC1168_phase=15")
one("pin(HERE/'derive_chronological_v5.py');pin(HERE/'normal_observer.hpp');pin(ROOT/", "pin(HERE/'derive_chronological_v5.py');pin(HERE/'prepare_chronological_v5.py');pin(HERE/'derive_chronological_v6.py');pin(HERE/'normal_observer.hpp');pin(ROOT/")
target.write_text(text)
