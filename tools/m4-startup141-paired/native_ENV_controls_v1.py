"""ROOT-called bounded State projector adverses; no files/readers/model/eval."""
import struct
def controls(project):
 s=bytearray(3504);x=2768;struct.pack_into('<H',s,x,0x37f);base=project(s);assert base==struct.pack('<7I',0xffff037f,0xffff0000,0xffffffff,0,0,0,0);tests=[]
 for name,offset,width,value,field in [('CW',x,2,0x7f,0),('IP',x+8,4,0x0045a230,3),('CS',x+12,2,0x23,4),('FOP',x+6,2,0x321,4),('DP',x+16,4,0x78037ff0,5),('DS',x+20,2,0x2b,6)]:
  q=bytearray(s);q[offset:offset+width]=value.to_bytes(width,'little');actual=project(q);assert actual!=base and [i for i,(a,b)in enumerate(zip(struct.unpack('<7I',base),struct.unpack('<7I',actual)))if a!=b]==[field];tests.append(dict(name=name,field=field,checked=True))
 for offset,bit in [(2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)]:
  q=bytearray(s);q[offset]=1;actual=project(q);assert struct.unpack_from('<I',actual,4)[0]==0xffff0000|(1<<bit);tests.append(dict(name='source-status-'+str(bit),checked=True))
 for offset in(x+6,x+8,x+12,x+16,x+20):
  q=bytearray(s);q[offset]=1;fa=bytearray(s[x:x+512]);fb=bytearray(q[x:x+512]);fa[6:24]=fb[6:24]=bytes(18);assert fa==fb and project(q)!=base;tests.append(dict(name='equal-zeroedFX-distinctENV-'+str(offset-x),checked=True))
 for name,q in [('truncated',s[:-1]),('nonempty-tag',bytearray(s)),('nonboolean-status',bytearray(s))]:
  if name=='nonempty-tag':q[x+4]=1
  if name=='nonboolean-status':q[2737]=2
  try:project(q)
  except AssertionError:tests.append(dict(name=name,rejected=True))
  else:raise AssertionError('Unrefused source projector '+name)
 return dict(passed=True,tests=tests,source_machine_executed=False,canonical_reader_opened=False,ordinary_reader_opened=False,hardware_ENV_from_FX_inferred=False,initializer_credit=0)
