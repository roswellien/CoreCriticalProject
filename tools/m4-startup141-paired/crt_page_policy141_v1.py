"""Finite current141 CRT page relations (derived from crt_page_policy_v5).

Only two v5 constants become explicit measured parameters: the observer shim
restore phase (v5: 13; current141 import-cells141-r1: 15) and the lock13
Enter/Leave counts (v5: [108,108]; current141 lock13-counts141-r1: [111,111]).
Every other predicate is byte-identical to v5.
No page wildcard. Every nonregistry byte must equal its own initial input.
Registry pointer bytes must match independently source-derived own metadata.
"""
import struct
def need(v,m):
 if not v:raise ValueError(m)
class Policy:
 def __init__(self,original,native,patches,unused_input_offsets,physical_import_cells,typed_CRT_loader_cells,typed_CRT_lock13_objects,restore_phase,lock13_counts):
  self.restore_phase=restore_phase;need(type(restore_phase)is int and type(lock13_counts)is list and len(lock13_counts)==2,'Explicit measured current141 shim restore phase and derived lock13 counts')
  self.lock13_objects=typed_CRT_lock13_objects
  need(len(typed_CRT_lock13_objects)==1,'Exact single current initialized lock13 API resource')
  r=typed_CRT_lock13_objects[0]
  need(r['offset']==0x130 and r['size']==24 and r['guest_address']==0x78037130 and r['role']=='initialized_lock13_opaque_API_resource','Exact whole24 typed lock13 descriptor scope')
  need(bytes.fromhex(r['original_initial_hex'])==original[0x78037000][0x130:0x148]and bytes.fromhex(r['native_initial_hex'])==native[0x78037000][0x130:0x148],'Whole own original/native lock13 descriptor inputs')
  need(struct.unpack('<6I',bytes.fromhex(r['original_initial_hex']))==(0xffffffff,0xffffffff,0,0,0,0x020007d0)and bytes.fromhex(r['native_initial_hex'])==bytes(24),'Genuine original unlocked OS CS24 and immutable native guest descriptor representation')
  need(r['native_resource_extent']==40 and r['native_resource_pointer']and r['native_initializations']==1 and r['original_enter_leave']==r['native_enter_leave']==lock13_counts and r['opaque_API_internals_equivalent']is False,'Same-instance finite actual API ownership; no opaque transient Win32 equivalence claim')
  need(not set(range(0x130,0x148))&set(unused_input_offsets),'API-consumed whole CS24 cannot be declared unused')
  self.loader_cells=typed_CRT_loader_cells
  need(len(typed_CRT_loader_cells)==1 and typed_CRT_loader_cells[0]['offset']==0x8c and typed_CRT_loader_cells[0]['role']=='initialized_lock25','Exact retained current MFC lock25 loader cell')
  for r in typed_CRT_loader_cells:
   need(struct.unpack_from('<I',original[0x78037000],r['offset'])[0]==r['original_target']and struct.unpack_from('<I',native[0x78037000],r['offset'])[0]==r['native_target']and r['original_target']and r['native_target'],'Exact independently source/API-bound own lock25 descriptor pointer')
  self.import_cells=physical_import_cells
  need(len(physical_import_cells)==144 and len({r['offset']for r in physical_import_cells})==144,'Exact144 distinct physical named MSVCRT import cells')
  for r in physical_import_cells:
   need(r['library'].lower()=='kernel32.dll'and r['name']and r['offset']%4==0,'Exact named physical import DWORD')
   need(struct.unpack_from('<I',original[0x7802e000],r['offset'])[0]==r['original_installed_target']and struct.unpack_from('<I',native[0x7802e000],r['offset'])[0]==r['native_raw_thunk'],'Every own initial import target matches physically resolved actual export/current shim and physical raw thunk')
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
   for r in self.loader_cells:declared.update(range(r['offset'],r['offset']+4))
   for r in self.lock13_objects:declared.update(range(r['offset'],r['offset']+r['size']))
  else:
   if phase==self.restore_phase:
    for row in self.patches:
     need(row['kind']=='registry-IAT'and row['pc']&~4095==page,'Exact physical eight API shim cells');offset=row['pc']&4095;ao[offset:offset+4]=bytes.fromhex(row['original_hex'])
   for r in self.import_cells:
    offset=r['offset'];actual=struct.unpack_from('<I',ao,offset)[0];need(actual==(r['original_real_target']if phase==self.restore_phase and r['observer_shim']else r['original_installed_target']),'Exact real export/typed installed observer import relation')
    declared.update(range(offset,offset+4))
   need(all(i in declared for i,(a,b)in enumerate(zip(ao,bo))if a!=b),'All initial IAT differences reside in physically attributed named import cells')
  need(original==bytes(ao)and native==bytes(bo),'Every whole current CRT byte from exact own input plus only typed registry fields/exact installed import shim DWORDs')
  need(all(i in declared for i,(a,b)in enumerate(zip(original,native))if a!=b),'No undeclared CRT byte difference')
  return declared
