"""Bind exact SECREL current slot as an offset in the actual PE TLS template."""
from pathlib import Path
import hashlib
PREVIOUS=Path(__file__).with_name('review_mfc1168_resource_prelaunch_v3.py')
PREVIOUS_SHA='c1b26baf524056197ebcf4625e1e6538cd0acaf1f9ff6b4c8c603b77740600cb'
assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()==PREVIOUS_SHA
source=PREVIOUS.read_text()
before="exec(compile(text,str(BASE),'exec'),globals())"
assert source.count(before)==1
addition=r'''
before="guarded_matches=C.linked_candidates(image,guarded,guarded_relocs)"
after="""need(all(r['type']==4 or (r['type']==11 and r['symbol']['name']=='current' and r['symbol']['value']==0)for r in guarded_relocs),'Only exact REL32 and named current TLS SECREL operands')
        tls_relocs=[r for r in guarded_relocs if r['type']==11]
        need(len(tls_relocs)==(1 if level=='O0' else 2),'Exact level-specific current TLS relocation count')
        # Both relocation kinds occupy a DWORD; only the matching algorithm
        # below treats their widths alike. The type11 target is never a VA.
        guarded_matches=C.linked_candidates(image,guarded,[dict(r,type=4)for r in guarded_relocs])
        need(len(guarded_matches)==1,'Unique whole guarded invocation with exact typed relocation DWORD extents')
        pe_offset=struct.unpack_from('<I',image.data,60)[0]
        TLS_rva,TLS_size=struct.unpack_from('<II',image.data,pe_offset+24+112+9*8)
        need(TLS_size==40,'Complete actual PE32+ TLS directory')
        def rva_bytes(rva,size):
            matches=[s for s in image.sections if s['virtual_address']<=rva and rva+size<=s['virtual_address']+s['raw_size']]
            need(len(matches)==1,'Complete bounded final TLS/image backing')
            s=matches[0];at=s['raw_offset']+rva-s['virtual_address'];return image.data[at:at+size]
        TLS_raw=rva_bytes(TLS_rva,40)
        start,end,index,callbacks,zero_fill,alignment=struct.unpack('<4Q2I',TLS_raw)
        need(end-start==16 and zero_fill==0 and alignment==0x400000 and index>=image.image_base and callbacks>=image.image_base,'Actual finite16-byte aligned TLS template')
        template=rva_bytes(start-image.image_base,end-start)
        current_sections={r['symbol']['section']for r in tls_relocs}
        need(len(current_sections)==1,'One original compiler TLS current object')
        current_section=sections[next(iter(current_sections))]
        need(current_section['bytes']==bytes(8),'Whole actual eight-byte zero-initialized compiler current TLS object')
        linked_raw=guarded_matches[0][1]
        for relocation in tls_relocs:
            at=relocation['offset'];slot=struct.unpack_from('<I',linked_raw,at)[0]
            need(struct.unpack_from('<I',guarded,at)[0]==0 and slot==8 and template[slot:slot+8]==current_section['bytes'],'Exact current SECREL slot8 plus full original eight-byte TLS object, not a virtual address')
        deps.append(dict(level=level,TLS_directory_sha256=hashlib.sha256(TLS_raw).hexdigest(),TLS_template_sha256=hashlib.sha256(template).hexdigest(),current_SECREL_offsets=[r['offset']for r in tls_relocs],current_template_slot=8))"""
assert text.count(before)==1
text=text.replace(before,after)
before="    pin(BASE,SHA);"
assert text.count(before)==1
text=text.replace(before,"    pin(PREVIOUS,PREVIOUS_SHA);pin(BASE,SHA);")
exec(compile(text,str(BASE),'exec'),globals())
'''
source=source.replace(before,addition)
exec(compile(source,str(PREVIOUS),'exec'),globals())
