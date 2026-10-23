"""Derive sparse CRT source globals from genuine finite bootstrap birth.

The recorded publication journal is solely an equality target. Neither its
operand values nor any candidate AFTER bytes initialize these source inputs.
"""
import struct
def need(v,s):
 if not v:raise ValueError(s)
def derive(getter,sequence):
 stem=f'sequence-{sequence}/cleaned/'
 create=getter(stem+'heap-create-witness.bin');query=getter(stem+'heap-query-witness.bin')
 need(len(create)==128 and len(query)==160,'Entire actual HeapCreate16Q/query20Q birth witnesses')
 w=struct.unpack('<16Q',create);q=struct.unpack('<20Q',query)
 need(w[:6]==(1,0,1,0,4096,0)and w[6]>0 and w[7]==0x48450001 and w[11]==w[6],'Genuine successful private heap flags/extent and separately derived opaque guest token')
 need(w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual source HeapCreate stdcall saved frame/return')
 need(q[:3]==(1,1,1)and q[3]>0 and q[4:8]==(148,0x200017b8,0x20000618,0x78003a31)and q[8]==q[10]and q[11:18]==(37,1,1,1,1,1,0),'Exact accepted finite mode1 version-query branch and full source call frame')
 input_bytes=getter(stem+'heap-query-input.bin');output=getter(stem+'heap-query-output.bin')
 need(len(input_bytes)==len(output)==148 and struct.unpack_from('<I',input_bytes)[0]==148 and struct.unpack_from('<I',output)[0]==148,'Entire finite query input/output structures')
 need(q[18:]==(6,2)and struct.unpack_from('<I',output,4)[0]==q[18]and struct.unpack_from('<I',output,16)[0]==q[19],'Current actual NT6/platform2 selector domain remains fixed')
 # This is the already accepted qualifying source selector domain and literal
 # mode1 continuation. The journal must corroborate both derived stores.
 token=w[7];mode=1;raw=getter(stem+'heap-source-accesses.bin')
 need(len(raw)==128*20,'Entire current128 original bootstrap source operands')
 rows=list(struct.iter_unpack('<5I',raw))
 publications=[r for r in rows if r[1]in(0x78035000,0x78035004)]
 need(publications==[(0x780039d8,0x78035000,token,4,1),(0x780039eb,0x78035004,mode,4,1)],'Recorded source publications are exact equality targets for independently derived birth words')
 return struct.pack('<2I',token,mode)
