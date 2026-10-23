"""Discriminate literal onexit growth by current source/API operands."""
def need(v,s):
 if not v:raise ValueError(s)
def verify(row,observed,program):
 rows=row['borrowed_provider']['provider_source_rows'];names=[x['requested']for x in observed]
 need(names in (['EnterCriticalSection','HeapSize','LeaveCriticalSection'],['EnterCriticalSection','HeapSize','HeapSize','HeapReAlloc','LeaveCriticalSection']),'Exact literal typed registry API path')
 sizes=[x['witness_words']for x in observed if x['requested']=='HeapSize'];capacity=sizes[0][8]
 def source(pc,address,write):
  found=[r for r in rows if r[0]==pc and r[1]==address and r[3:]==[4,write]];need(len(found)==1,'Unique literal registry operand');return found[0][2]
 begin=source(0x78004a3c,0x7803788c,0);need(source(0x78004a47,0x7803788c,0)==begin,'Same owning source begin read before and after size query');end=source(0x78004a4e,0x78037888,0);used=end-begin
 need(begin>0 and 0<=used<=capacity and used%4==capacity%4==0 and capacity>=4 and sizes[0][22]==begin,'Actual HeapSize owns exact current source backing and finite used/capacity geometry')
 growth=used==capacity
 need(growth==(len(sizes)==2),'Literal full-capacity predicate discriminates second size query and growth')
 if growth:
  need(sizes[1][8]==capacity and sizes[1][22]==begin,'Same source owning backing/capacity independently queried twice')
  realloc=next(x['witness_words']for x in observed if x['requested']=='HeapReAlloc');new=realloc[12]
  need(realloc[22]==begin and realloc[23]==capacity+16 and realloc[13]==capacity+16 and new>0,'Whole typed source realloc old pointer/request/derived guest backing')
  need(source(0x7801e2aa,0x7803788c,1)==new and source(0x7801e2b5,0x78037888,1)==new+used,'Literal growth begin/end publications derive preserved old used offset')
  expected=129;callback_slot=new+used
 else:expected=67;callback_slot=end
 stores=[r for r in rows if r[0]==0x78004a67 and r[3:]==[4,1]];need(stores==[[0x78004a67,callback_slot,row['borrowed_provider']['callback'],4,1]],'Literal callback store owns exact derived current slot')
 need(source(0x78004a69,0x78037888,1)==callback_slot+4,'Literal source end advances one callback DWORD')
 need(len(rows)==expected,'Exact physically discriminated operand extent')
 for pc,a,v,n,w in rows:
  need(pc in program and program[pc]['bytes_hex'] and program[pc]['width']>0,'Every borrowed provider operand joins retained literal physical instruction')
 return dict(growth=growth,used_bytes=used,actual_capacity=capacity,callback_slot=callback_slot,expected_provider_operands=expected)
