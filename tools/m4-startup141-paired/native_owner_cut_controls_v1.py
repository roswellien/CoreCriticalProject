"""Unexecuted pure controls of the exact added adapter AST, no reader/model."""
import ast,copy,hashlib
def controls(adapter_text):
 tree=ast.parse(adapter_text);body=next(v.body for v in tree.body if isinstance(v,ast.FunctionDef)and v.name=='build')
 start=next(i for i,v in enumerate(body)if ast.unparse(v).startswith("need(owner_cut['level']"))
 stop=next(i for i in range(start,len(body))if isinstance(body[i],ast.For)and ast.unparse(body[i].iter)=='enumerate(FIXED)')
 added=body[start:stop]
 geometry=[v for v in body if ast.unparse(v).startswith('need(all((v in byguest')or ast.unparse(v).startswith("need(sum((v['kind']")]
 assert len(geometry)==2,'Extract both actual new mapped geometry/finite role guards'
 code=compile(ast.fix_missing_locations(ast.Module(body=added+geometry,type_ignores=[])),'exact-adapter-owner-cut-guards','exec')
 prefix='sequence-0/selected/registry-checkpoint-222';site=0x58af12;frame=0x20001760;root=0x4103f0
 pages=[];byguest={}
 for n in range(8):
  guest=0x31001000+n*4096;raw=bytes([n])*16;pages.append(dict(address=guest,logical_key=prefix+'-page-'+str(guest)+'.bin',bytes=16,hex=raw.hex(),sha256=hashlib.sha256(raw).hexdigest()));g=[0]*16;g[4]=16;byguest[guest]=g
 baseline=dict(owner_cut=dict(level='O0',sequence=0,root=root,checkpoint_prefix=prefix,checkpoint_name='constructor-mfc-before',pages=pages),level='O0',seq=0,root=root,starts=[prefix],first=0,current_source=dict(constructor_call_results=[[root,site,0x5abd26,frame,site+5]],whole_literal_source_accesses=[[site-4,0x604010,17,1,1],[site,frame,site+5,4,1]]),memory={},byguest=byguest,owners=[dict(kind=4)for _ in range(8)])
 def need(v,m):
  if not v:raise ValueError(m)
 def run(ns):ns['need']=need;exec(code,ns);return ns
 valid=run(copy.deepcopy(baseline));assert valid['memory']=={v['address']:bytes.fromhex(v['hex'])for v in pages}and valid['prefix'][0][4]==1
 mutations=[]
 def add(name,f):mutations.append((name,f))
 for key,value in [('level','O2'),('sequence',1),('root',0x410440),('checkpoint_prefix',prefix+'-wrong'),('checkpoint_name','constructor-mfc-after')]:add('cut-'+key,lambda n,k=key,v=value:n['owner_cut'].__setitem__(k,v))
 add('empty-pages',lambda n:n['owner_cut'].__setitem__('pages',[]))
 add('duplicate-page',lambda n:n['owner_cut']['pages'].append(copy.deepcopy(n['owner_cut']['pages'][0])))
 for key,value in [('address',0x20001000),('logical_key',prefix+'-wrong.bin'),('bytes',15),('sha256','0'*64),('hex','00')]:add('page-'+key,lambda n,k=key,v=value:n['owner_cut']['pages'][0].__setitem__(k,v))
 add('existing-input-overwrite',lambda n:n['memory'].__setitem__(0x31001000,b'unchanged'))
 add('first-call-root',lambda n:n['current_source']['constructor_call_results'][0].__setitem__(0,0x410440))
 add('first-call-target',lambda n:n['current_source']['constructor_call_results'][0].__setitem__(2,0x5abd1a))
 add('first-call-PC',lambda n:n['current_source']['constructor_call_results'][0].__setitem__(1,site+1))
 add('first-call-frame',lambda n:n['current_source']['constructor_call_results'][0].__setitem__(3,frame+4))
 add('first-call-return',lambda n:n['current_source']['constructor_call_results'][0].__setitem__(4,site+6))
 add('duplicate-call-operand',lambda n:n['current_source']['whole_literal_source_accesses'].append([site,frame,site+5,4,1]))
 add('owner-write-prefix',lambda n:n['current_source']['whole_literal_source_accesses'].insert(0,[site-8,0x31001000,1,1,1]))
 add('unaligned-boundary-owner-write',lambda n:n['current_source']['whole_literal_source_accesses'].insert(0,[site-8,0x30ffffff,1,4,1]))
 add('unknown-allocation',lambda n:n['byguest'].pop(0x31001000))
 add('mapped-extent',lambda n:n['byguest'][0x31001000].__setitem__(4,32))
 add('missing-role',lambda n:n['owners'].pop())
 add('future-role',lambda n:n['owners'].append(dict(kind=4)))
 refused=[]
 for name,mutation in mutations:
  ns=copy.deepcopy(baseline);mutation(ns)
  try:run(ns)
  except (AssertionError,ValueError,KeyError):refused.append(name)
  else:raise AssertionError('Exact current guard accepted adverse '+name)
 return dict(passed=True,scope='Synthetic exact added adapter3 guards only; no source/reader/actual owner validation',actual_added_AST_extracted=True,positive_static_prefix_write_retained=True,positive_whole_owner_bytes_retained=True,negative_controls=len(refused),refused=refused,source_execution=False,reader_opened=False)
