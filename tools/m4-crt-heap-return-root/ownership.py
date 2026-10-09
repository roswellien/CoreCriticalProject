"""Private heap ownership, measured API response and genuine return progress."""
import importlib.util
import struct
from consumer import F

path=F.pin(F.ROOT/'tools/m4-crt-heap-mode-root/ownership.py',
    '89dca345d97af8754a03cd367f0ff26bc1e5d342c47631bf8ea5ab06239b43ad')
spec=importlib.util.spec_from_file_location('heap_version_fixed_API_identity',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
TOKEN=0x48450001


def witness(row,job):
    raw=(row/'heap-return-witness.bin').read_bytes();registry=(row/'heap-return-registry.bin').read_bytes()
    F.require(len(raw)==128 and len(registry)==144,'Complete full-width heap ownership witness')
    w,r=struct.unpack('<16Q',raw),struct.unpack('<18Q',registry)
    F.require(w[:6]==(1,0,1,0,4096,0) and w[6]!=0 and w[6]!=TOKEN and w[7]==TOKEN and w[11]==w[6],
              'Actual noninjected heap acquisition and distinct opaque token')
    F.require(w[8]==w[10]==job[22]==job[23] and w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),
              'Measured restored caller error and bounded HeapCreate return')
    F.require(r[0]==1 and r[1]!=0 and r[2:11]==(1,TOKEN,w[6],1,1,0,1,1,1) and
              r[12:]==(1,0,0,1,w[6],0),'Exactly one full-width owned heap and successful matching release')
    F.require(w[9]<=0xffffffff and r[11]<=0xffffffff,'Measured DWORD error values')
    q=struct.unpack('<20Q',(row/'heap-return-query-witness.bin').read_bytes())
    before=(row/'heap-return-query-input.bin').read_bytes();after=(row/'heap-return-query-output.bin').read_bytes()
    F.require(len(before)==len(after)==148 and struct.unpack_from('<I',before)[0]==148,
              'Complete actual source input and native scratch output')
    F.require(q[:3]==(1,1,1) and q[3]<=0xffffffff and q[4:8]==(148,0x200017b8,0x20000618,0x78003a31),
              'One actual named version query at the authentic source frame')
    F.require(q[8]==q[10]==job[22] and q[9]<=0xffffffff and q[11:16]==(37,1,1,1,1),
              'Measured query error restoration, complete37-DWORD transport and checked API return')
    major,platform=struct.unpack_from('<I',after,4)[0],struct.unpack_from('<I',after,16)[0]
    good=q[3]!=0 and platform==2 and major>=5
    F.require(q[16:]==(int(good),int(not good),major,platform),'Actual scratch fields determine source frontier')
    return dict(token=TOKEN,full_host_handle=w[6],registry_owner=r[1],witness_words=w,registry_words=r,
        query_words=q,query_input=before,query_output=after,selector_returned=good,
        response=dict(input=before,output=after,result=q[3]),
        create=prior.prior.api_identity(row,'heap-return-create'),destroy=prior.prior.api_identity(row,'heap-return-destroy'),
        query=prior.prior.api_identity(row,'heap-return-query'))


def phase_ownership(tag,actual):
    initial=(1,actual['registry_owner'],1,*([0]*15))
    closed=tag in ('heap-create-after','entry-after-fault','retry-after')
    active=tag.startswith(('heap-create-','heap-mode-','heap-version-','heap-return-')) or closed
    if not active: w,r=bytes(128),bytes(144)
    elif tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before'):
        w,r=bytes(128),struct.pack('<18Q',*initial)
    else:
        registry=actual['registry_words'] if closed else (1,actual['registry_owner'],1,TOKEN,actual['full_host_handle'],1,1,1,1,*([0]*9))
        w,r=struct.pack('<16Q',*actual['witness_words']),struct.pack('<18Q',*registry)
    return {'heap-create-witness.bin':w,'heap-create-registry.bin':r}


def phase_query(tag,actual,model):
    q=[0]*20;input_bytes=output_bytes=bytes(148);writes=bytes(1280)
    if tag=='heap-mode-query-before' or tag.startswith(('heap-version-','heap-return-')) or tag in ('heap-create-after','entry-after-fault','retry-after'):
        source=actual['query_words'];q=[1,1,0,0,148,0x200017b8,0x20000618,0x78003a31,source[8],0,0,0,0,0,0,0,0,0,0,0]
        input_bytes=actual['query_input']
        if tag!='heap-mode-query-before': q[12]=1
        if tag not in ('heap-mode-query-before','heap-version-query-native-before'):
            q[2:4]=source[2:4];q[9:11]=source[9:11];q[18:]=source[18:];output_bytes=actual['query_output']
        if tag not in ('heap-mode-query-before','heap-version-query-native-before','heap-version-query-native-after'):
            q[11],q[13]=37,1
            raw=b''.join(struct.pack('<5I',*value) for value in model['query_output_accesses'])
            writes=raw+bytes(1280-len(raw))
        if tag in ('heap-version-query-returned','heap-version-selector-return-after','heap-version-environment-before',
                   'heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'): q[14:16]=[1,1]
        if tag in ('heap-version-selector-return-after','heap-version-environment-before','heap-create-after','entry-after-fault','retry-after') or tag.startswith('heap-return-'):
            q[16:18]=source[16:18]
    return {'heap-version-query-witness.bin':struct.pack('<20Q',*q),'query-input.bin':input_bytes,
            'query-output.bin':output_bytes,'heap-version-output-accesses.bin':writes}


def phase_progress(tag, actual):
    closed = tag in ('heap-create-after','entry-after-fault','retry-after')
    active = tag.startswith(('heap-create-','heap-mode-','heap-version-','heap-return-')) or closed
    if not active: words = [0]*8
    else:
        before = tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before')
        words = [1,0,0,0,0,0,0,int(not before and not closed)]
        if tag.startswith('heap-return-') or closed and actual['selector_returned']:
            words[1:3] = [1,1]
            if tag != 'heap-return-mode-store-before': words[3:5] = [1,1]
            if tag not in ('heap-return-mode-store-before','heap-return-mode-store-after'): words[5] = 1
            if tag == 'heap-return-initializer-return-after' or closed: words[6] = 1
    return {'heap-return-progress.bin':struct.pack('<8I',*words)}
