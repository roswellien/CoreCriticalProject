"""Existing finite registry suffix proof, now joining newly observed whole pages.

Only pointer/cursor and preserved backing are claimed. Full provider CPU and
new unused growth capacity bytes remain outside this suffix proof.
"""
import struct
def need(v,s):
 if not v:raise ValueError(s)
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def prove(reader,sequence,phase,machine,callback,raw,API):
 begin=words(machine.bytes(0x7803788c,4))[0];nxt=words(machine.bytes(0x78037888,4))[0]
 previous=reader.data(f'phase/{sequence}/{phase-1}.bin');prior=words(previous,356464,4);after=words(raw,356464,4)
 actual_before=reader.data(f'phase/{sequence}/{phase}/registry-before-meta.bin');backing=reader.data(f'phase/{sequence}/{phase}/registry-before-backing.bin')
 need(len(actual_before)==16 and words(actual_before,0,4)==prior,'Whole immediately prior registry metadata equals own root BEFORE')
 need(len(backing)==prior[2]and backing==previous[356480:356480+prior[2]],'Whole genuine registry BEFORE backing and carried capacity')
 need(prior[0]==begin and prior[1]==nxt and begin and nxt>=begin and nxt-begin<=prior[2]<=512,'Literal prefix current registry fields join genuine BEFORE')
 used=nxt-begin;new_begin=begin;growth=[]
 if used+4>prior[2]:
  growth=[(i,f)for i,f in enumerate(API)if f[24]==3 and f[22]==begin]
  need(len(growth)==1,'One finite typed original registry HeapReAlloc response at source growth branch')
  index,fact=growth[0]
  need(fact[21]==0and fact[23]==prior[2]+16and fact[10]and after[2]>=fact[23],'Literal capacity+16 request and genuine returned owner extent')
  new_begin=fact[10]
 else:need(after[2]==prior[2],'Exact unchanged no-growth capacity')
 need(after[0]==new_begin and after[1]==new_begin+used+4,'Independent literal registry pointer and cursor stores from own BEFORE')
 expected=bytearray(backing)
 if used+4<=len(expected):struct.pack_into('<I',expected,used,callback)
 else:expected.extend(struct.pack('<I',callback))
 need(bytes(expected)==raw[356480:356480+len(expected)],'Every preserved registry backing byte plus exact literal callback store')
 return dict(BEFORE_begin=begin,BEFORE_next=nxt,BEFORE_capacity=prior[2],source_derived_AFTER_begin=new_begin,source_derived_AFTER_next=new_begin+used+4,callback=callback,whole_preserved_backing_bytes=len(expected),finite_growth_API_rows=[dict(index=i,words=list(f))for i,f in growth],literal_cursor_store_PC=0x78004a69,literal_callback_store_PC=0x78004a67,new_unused_growth_tail_claimed=False,full_provider_CPU_executed=False,AFTER_seed=False)
def page(predicted,address,proof):
 need(len(predicted)==4096,'Entire source-derived endpoint page')
 out=bytearray(predicted)
 if address==0x78037000:struct.pack_into('<II',out,0x888,proof['source_derived_AFTER_next'],proof['source_derived_AFTER_begin'])
 return bytes(out)
