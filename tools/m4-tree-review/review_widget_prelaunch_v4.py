"""Separate finite loader-supplied pages from the physical sparse page carrier."""
from pathlib import Path
import hashlib
V3 = Path(__file__).with_name('review_widget_prelaunch_v3.py')
V3_SHA = 'c497a2152cb51c44a6727f2cc25212db798bfd3d3edcec466067c0a82222beda'
if hashlib.sha256(V3.read_bytes()).hexdigest() != V3_SHA:
    raise ValueError('Immutable finite padding-overlay checker')
program = V3.read_text()
anchor = "exec(compile(source, str(BASE), 'exec'), globals())"
if program.count(anchor) != 1:
    raise ValueError('One source checker invocation')
transform = r'''
old_pages = """        for address in contracts['whole_pages']:
            need(address in sparse_pages, 'Every captured source page has declared BEFORE backing')"""
new_pages = """        pin(V3,V3_SHA)
        loader_pages = set(contracts['whole_pages']) - set(sparse_pages)
        eq(loader_pages,{0x5f498000,0x5f4cc000,0x780c1000,0x7810a000,0x78115000,0x78145000,0x78146000}, 'Exact inherited genuine DLL page domain outside sparse carrier')
        mfc = P.PEImage(raw(R / 'local/mw3-staged/Shared_DLLs/MFC42.DLL'))
        for address in loader_pages:
            owner = mfc if address < 0x78000000 else cp
            nt_off = struct.unpack_from('<I',owner.data,60)[0]
            image_size = struct.unpack_from('<I',owner.data,nt_off+24+56)[0]
            need(owner.image_base <= address and address+4096 <= owner.image_base+image_size, 'Whole loader input page belongs to exact physical DLL image')
            need(address not in sparse_pages, 'Loader page has no sparse overwrite')
        source_cpp = raw(directory / 'reference.cpp').decode()
        for marker in ('require(reinterpret_cast<unsigned>(cp)==0x780c0000', 'require(reinterpret_cast<std::uintptr_t>(mfc)==0x5f400000', 'LoadLibraryExW', 'Same-worker actual initialized borrowed DWORD', 'Actual DLL initialized page owner'):
            need(marker in source_cpp, 'Actual authenticated loader-supplied BEFORE page preparation '+marker)
        counts['whole_sparse_backed_observed_pages'] = len(contracts['whole_pages'])-len(loader_pages)
        counts['whole_genuine_loader_observed_pages_prepared'] = len(loader_pages)"""
if source.count(old_pages)!=1:
    raise ValueError('One complete observed page domain')
source=source.replace(old_pages,new_pages,1)
exec(compile(source, str(BASE), 'exec'), globals())
'''
program=program.replace(anchor,transform,1)
exec(compile(program,str(V3),'exec'),globals())
