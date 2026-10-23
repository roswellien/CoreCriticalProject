"""Finite current CRT page relations: exact own initial carry and typed fields.
No page wildcard. Every nonregistry byte must equal its own initial input.
Registry pointer bytes must match independently source-derived own metadata.
"""
import struct
def need(v,m):
 if not v:raise ValueError(m)
class Policy:
 def __init__(self,original,native,patches,unused_input_offsets):
  self.original=original;self.native=native;self.patches=patches;self.unused=set(unused_input_offsets)
  need(set(original)==set(native)=={0x7802e000,0x78037000},'Exact two whole own CRT input pages')
  need(all(len(v)==4096 for v in list(original.values())+list(native.values())),'Whole4096 input extents')
 def page(self,phase,side,page,original,native,original_meta,native_meta):
  if page not in self.original:return set()
  ao=bytearray(self.original[page]);bo=bytearray(self.native[page]);declared=set()
  if page==0x78037000:
   for raw,meta in((ao,original_meta),(bo,native_meta)):
    begin,nxt=meta[:2];need(begin and nxt>=begin and (nxt-begin)%4==0,'Typed own source registry begin/one-past-end');struct.pack_into('<II',raw,0x888,nxt,begin)
   declared.update(range(0x888,0x890));declared.update(self.unused)
  else:
   if phase==13:
    for row in self.patches:
     need(row['kind']=='registry-IAT'and row['pc']&~4095==page,'Exact physical eight API shim cells');offset=row['pc']&4095;ao[offset:offset+4]=bytes.fromhex(row['original_hex'])
   declared.update(i for i,(a,b)in enumerate(zip(ao,bo))if a!=b)
  need(original==bytes(ao)and native==bytes(bo),'Every whole current CRT byte from exact own input plus only typed registry fields/exact installed import shim DWORDs')
  need(all(i in declared for i,(a,b)in enumerate(zip(original,native))if a!=b),'No undeclared CRT byte difference')
  return declared
