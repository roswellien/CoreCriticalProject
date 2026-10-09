"""Full-width owned HeapCreate witness through the live stack-probe frontier."""
import importlib.util
import struct
from consumer import F

path = F.pin(F.ROOT/'tools/m4-crt-heap-create-root/ownership.py',
    'b9b8cb6590a020c3fc4930a1179166e45fa90a950afd7ac15609c3e40f81a6c8')
spec = importlib.util.spec_from_file_location('heap_mode_frozen_API_identity',path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
TOKEN = 0x48450001


def witness(row,job):
    raw = (row/'heap-mode-witness.bin').read_bytes()
    registry = (row/'heap-mode-registry.bin').read_bytes()
    F.require(len(raw)==128 and len(registry)==144,'Complete full-width heap-mode ownership witness')
    w,r = struct.unpack('<16Q',raw),struct.unpack('<18Q',registry)
    F.require(w[:6]==(1,0,1,0,4096,0),'Genuine noninjected HeapCreate request')
    F.require(w[6]!=0 and w[6]!=TOKEN and w[7]==TOKEN and w[11]==w[6],
              'Private complete HANDLE and distinct opaque guest token')
    F.require(w[8]==w[10]==job[22]==job[23],'Measured incoming/restored caller error')
    F.require(w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),
              'Unchanged declared checked HeapCreate return model')
    F.require(r[0]==1 and r[1]!=0 and r[2:11]==(1,TOKEN,w[6],1,1,0,1,1,1),
              'Exactly one private real heap acquisition and successful release')
    F.require(r[12:]==(1,0,0,1,w[6],0),'Single same-full-HANDLE cleanup and closed token lifecycle')
    F.require(w[9]<=0xffffffff and r[11]<=0xffffffff,'Actual DWORD API/cleanup error words')
    return dict(token=TOKEN,full_host_handle=w[6],registry_owner=r[1],witness_words=w,registry_words=r,
        create=prior.api_identity(row,'heap-mode-create'),destroy=prior.api_identity(row,'heap-mode-destroy'))


def phase_ownership(tag,actual):
    zero = {'heap-create-witness.bin':bytes(128),'heap-create-registry.bin':bytes(144)}
    if not tag.startswith(('heap-create-','heap-mode-')) and tag not in ('entry-after-fault','retry-after'):
        return zero
    if tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before'):
        zero['heap-create-registry.bin'] = struct.pack('<18Q',1,actual['registry_owner'],1,*([0]*15))
        return zero
    witness_bytes = struct.pack('<16Q',*actual['witness_words'])
    if tag in ('heap-create-after','entry-after-fault','retry-after'):
        registry = actual['registry_words']
    else:
        F.require(tag in ('heap-create-api-return-before','heap-create-api-returned','heap-create-published',
            'heap-create-mode-before','heap-mode-probe-before','heap-mode-probe-after','heap-mode-query-before'),
            'Exact live HeapCreate/selector/probe/query ownership phase')
        registry = (1,actual['registry_owner'],1,TOKEN,actual['full_host_handle'],1,1,1,1,*([0]*9))
    return {'heap-create-witness.bin':witness_bytes,'heap-create-registry.bin':struct.pack('<18Q',*registry)}
