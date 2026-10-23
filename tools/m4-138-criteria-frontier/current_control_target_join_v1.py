"""Exact owning COFF REL32 target predicate; no library/API execution."""
import struct
def join(address,raw,actual,row,target):
 assert 4<=row['type']<=9 and len(actual)==len(raw)
 offset=row['offset'];assert 0<offset and offset+4<=len(raw)
 decoded=address+offset+4+(row['type']-4)+struct.unpack_from('<i',actual,offset)[0]
 assert decoded==target
 return dict(offset=offset,typed_REL32=row['type'],target_address=decoded,CALL_opcode=raw[offset-1]==0xe8)
