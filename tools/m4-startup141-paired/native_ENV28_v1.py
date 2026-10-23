"""Exact guest ENV28 projector from own SOURCE-computed State3504.

Native protocol zeros metadata in FX6..23; this projector deliberately uses
complete State instead. It makes no hardware FNSTENV or original API claim.
"""
import struct
def project(state):
 assert len(state)==3504
 x87=2768;sw=2736
 word=lambda at:struct.unpack_from('<H',state,at)[0]
 dword=lambda at:struct.unpack_from('<I',state,at)[0]
 assert state[x87+4]==0,'Exact physical protocol empty guest x87 tag requirement'
 flags=((word(x87+2)&0xb880)|(state[sw+19]<<0)|(state[sw+17]<<1)|(state[sw+15]<<2)|(state[sw+13]<<3)|(state[sw+11]<<4)|(state[sw+9]<<5)|(state[sw+21]<<6)|(state[sw+1]<<8)|(state[sw+3]<<9)|(state[sw+5]<<10)|(state[sw+7]<<14))
 assert all(state[sw+i]in(0,1)for i in(1,3,5,7,9,11,13,15,17,19,21))
 return struct.pack('<7I',0xffff0000|word(x87),0xffff0000|flags,0xffffffff,dword(x87+8),word(x87+12)|(word(x87+6)<<16),dword(x87+16),0xffff0000|word(x87+20))
