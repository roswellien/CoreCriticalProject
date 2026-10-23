"""Pure disjointness guard for supplied current141 source/API byte spans.

This cannot establish completeness of a source domain or API buffer inventory.
Physical named144 cells, retained229 mode1 closure and exact two-page relation
remain separate required proofs. No source values or endpoint bytes are seeded.
"""
PAGE=0x78037000

def overlap_offsets(address,width):
 assert type(address)is int and type(width)is int and 0<=address<2**32 and 0<width<=2**32 and address+width<=2**32
 lo=max(address,PAGE);hi=min(address+width,PAGE+4096)
 return range(lo-PAGE,max(lo,hi)-PAGE)

def check_supplied_spans(unused_input_offsets,source_operands,API_buffers,physical_direct_offsets):
 assert type(unused_input_offsets)is list and len(unused_input_offsets)==len(set(unused_input_offsets))
 assert all(type(i)is int and 0<=i<4096 for i in unused_input_offsets)
 unused=set(unused_input_offsets)
 assert all(type(i)is int and 0<=i<4096 for i in physical_direct_offsets)
 assert not unused.intersection(physical_direct_offsets),'Retained physical mode1 direct operand touches opaque input difference'
 source_count=0;buffer_count=0;origins=[]
 for row in source_operands:
  assert type(row)in(list,tuple)and len(row)==5
  pc,address,value,width,writing=row
  assert type(pc)is int and 0<=pc<2**32 and type(value)is int and 0<=value<2**64 and type(writing)is int and writing in(0,1)
  offsets=overlap_offsets(address,width)
  assert not unused.intersection(offsets),'Current own source operand consumes/writes opaque input difference'
  source_count+=1
 for row in API_buffers:
  assert set(row)=={'PC','address','bytes','role','direction','origin'}
  assert type(row['PC'])is int and 0<=row['PC']<2**32
  assert row['direction']in('read','write','read_write')and type(row['role'])is str and row['role']and type(row['origin'])is str and row['origin']
  assert not unused.intersection(overlap_offsets(row['address'],row['bytes'])),'Typed API buffer consumes/writes opaque input difference'
  origins.append(row['origin']);buffer_count+=1
 return dict(supplied_spans_disjoint=True,source_operand_rows=source_count,typed_API_buffer_spans=buffer_count,API_buffer_origins=origins,complete_current141_footprint=False,physical_named_import_cells_proven=False,whole_CRT_pages_proven=False,source_machine_executed=False,accepted_function_credit=0)
