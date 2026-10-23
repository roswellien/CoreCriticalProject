"""Literal one callback store/growth publications over actual APIinitial backing.
No AFTER bytes supply an input or an expected byte. Opaque unused padding
retains each own API-produced initial bytes; crossbranch padding is not equal.
"""
import struct
def need(v,m):
 if not v:raise ValueError(m)
def derive(before_meta,before_backing,callback,birth=None):
 begin,nxt,capacity,mode=before_meta;need(begin and mode==1 and len(before_backing)==capacity and 0<=nxt-begin<=capacity and (nxt-begin)%4==0,'Complete own registry BEFORE backing/metadata');offset=nxt-begin
 if callback is None:
  need(birth is None,'No registration creates no registry growth');return dict(metadata=list(before_meta),backing=bytes(before_backing),source_store=None,growth=False)
 need(callback>0,'Exact literal callback')
 if offset>=capacity:
  need(birth is not None and birth['old_begin']==begin and birth['requested']==capacity+16 and birth['source_CALL_pc']==0x78011c27 and birth['return_word']==0x78011c2d,'Exact literal full-registry growth request/call/return');raw=bytes(birth['initial']);need(birth['pointer']and len(raw)>=capacity+16 and raw[:capacity]==before_backing,'Actual successful APIinitial backing retains full old prefix');begin=birth['pointer'];capacity=len(raw);expected=bytearray(raw)
 else:
  need(birth is None,'Nonfull registry invokes no reallocation');expected=bytearray(before_backing)
 struct.pack_into('<I',expected,offset,callback);return dict(metadata=[begin,begin+offset+4,capacity,mode],backing=bytes(expected),source_store=dict(PC=0x78004a67,address=begin+offset,width=4,value=callback),growth=birth is not None)
