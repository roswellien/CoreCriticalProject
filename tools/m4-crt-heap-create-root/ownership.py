"""Validate declared real-API identities and full-width closed ownership witness."""
from pathlib import Path
import struct
from consumer import F

TOKEN = 0x48450001


def api_identity(row, name):
    before=(row/(name+'-api-before.bin')).read_bytes()
    after=(row/(name+'-api-after.bin')).read_bytes()
    F.require(len(before)==2184 and before==after,'Exact before/after measured executable API identity '+name)
    address,named,owner,owner_named=struct.unpack_from('<4Q',before)
    base,size,allocation,state,image_type,protection,_=struct.unpack_from('<3Q4I',before,32)
    F.require(address!=0 and owner!=0 and address==named==owner_named and owner==allocation and
              allocation<=base<=address<base+size<=2**64,
              'Named actual forwarded API and owner association '+name)
    F.require(state==0x1000 and image_type==0x1000000 and protection&0xf0 and not protection&0x101,
              'Committed executable native API image '+name)
    digest=before[72:136].decode('ascii')
    text=before[136:].decode('utf-16-le')
    filename,separator,tail=text.partition('\0')
    F.require(bool(separator) and bool(filename) and all(char=='\0' for char in tail),'Exact terminated/padded native API module path '+name)
    F.pin(Path(filename),digest)
    return dict(target=address,owner=owner,path=filename,sha256=digest)


def witness(row, job):
    captured=(row/'heap-create-witness.bin').read_bytes()
    registry=(row/'heap-create-registry.bin').read_bytes()
    F.require(len(captured)==128 and len(registry)==144,'Complete typed full-width API/ownership witness')
    w=struct.unpack('<16Q',captured)
    r=struct.unpack('<18Q',registry)
    F.require(w[:6]==(1,0,1,0,4096,0),'Actual HeapCreate request and noninjected execution provenance')
    F.require(w[6]!=0 and w[6]!=TOKEN and w[7]==TOKEN and w[11]==w[6],'Private full host handle and independent opaque guest token')
    F.require(w[8]==w[10]==job[22]==job[23],'Inner and outer observed caller LastError restored')
    F.require(w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Declared checked stdcall return model')
    F.require(r[:1]==(1,) and r[1]!=0 and r[2:11]==(1,TOKEN,w[6],1,1,0,1,1,1),
              'Exactly one private full-width acquisition, registration and successful real destruction')
    F.require(r[12:]==(1,0,0,1,w[6],0),'Single actual cleanup, no skip/rollback/duplicate destruction or lookup denial')
    # API and cleanup LastError result words are measured witness inputs. They
    # are not assigned an expected success value by the Win32 contract.
    F.require(w[9]<=0xffffffff and r[11]<=0xffffffff,'Actual DWORD API/cleanup error witnesses')
    create=api_identity(row,'heap-create')
    destroy=api_identity(row,'heap-destroy')
    return dict(token=TOKEN,full_host_handle=w[6],registry_owner=r[1],create=create,destroy=destroy,
                witness_words=w,registry_words=r,
                owned_handle_closed=True,original_x86_API_implementation_equivalence=False)


def phase_ownership(tag,actual):
    if not tag.startswith('heap-create-') and tag not in ('entry-after-fault','retry-after'):
        return dict(zip(('heap-create-witness.bin','heap-create-registry.bin'),(bytes(128),bytes(144))))
    initial=(1,actual['registry_owner'],1,*([0]*15))
    if tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before'):
        return {'heap-create-witness.bin':bytes(128),'heap-create-registry.bin':struct.pack('<18Q',*initial)}
    w=struct.pack('<16Q',*actual['witness_words'])
    if tag in ('heap-create-api-return-before','heap-create-api-returned','heap-create-published','heap-create-mode-before'):
        h=actual['full_host_handle']
        live=(1,actual['registry_owner'],1,TOKEN,h,1,1,1,1,*([0]*9))
        return {'heap-create-witness.bin':w,'heap-create-registry.bin':struct.pack('<18Q',*live)}
    F.require(tag in ('heap-create-after','entry-after-fault','retry-after'),'Exact declared ownership phase')
    return {'heap-create-witness.bin':w,'heap-create-registry.bin':struct.pack('<18Q',*actual['registry_words'])}
