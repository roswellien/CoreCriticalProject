from pathlib import Path
import json,hashlib,ast,importlib.util,struct,copy,collections,sys
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p):
  p=Path(p).resolve();pins[str(p)]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 H=load('tools/m4-138-validation-review/constructor_input_capture_phase_v1.py','h');V=load('tools/m4-138-validation-review/validate_constructor_input_capture_v2.py','v');run=load('tools/m4-138-validation-review/run_constructor_input_capture_v2.py','r')
 for p in ('tools/m4-constructor-original/validate_v7.py','tools/m4-constructor-original/run.py','tools/m4-138-validation-review/validate_constructor_input_capture_v1.py','tools/m4-138-validation-review/validate_constructor_input_capture_v2.py','tools/m4-138-validation-review/run_constructor_input_capture_v2.py'):ast.parse(pin(R/p).read_text())
 assert run.main.__code__.co_argcount==5 and V.main.__code__.co_argcount==6 and H.validate.__code__.co_argcount==5
 parent=pin(R/'tools/m4-constructor-original/run.py').read_text();current=pin(R/'tools/m4-138-validation-review/run_constructor_input_capture_v2.py').read_text();assert current.replace("pin(R/'tools/m4-constructor-original/derive_runner.py');pin(R/'tools/m4-constructor-original/run.py');pin(R/'tools/m4-138-validation-review/prepare_constructor_input_capture_v5.py');pin(Path(b['preparation'])/'report.json',b['preparation_sha256'])","pin(Path(__file__).with_name('derive_runner.py'))").replace("BASE=R/'reports/m4-138-validation-review'","BASE=R/'reports/m4-constructor-original'")==parent
 stem='phase/0/13';root=0x4103f0;shims=[0x18010000+0x10*i for i in range(8)];data={};page=bytearray(4096);bindings=[]
 for i,cell in enumerate(H.CELLS):struct.pack_into('<I',page,cell%4096,shims[i]);bindings.extend((i,cell,shims[i],0x77010000+0x100*i,shims[i],0x77000000,0x77000000))
 pages=(0x7802e000,0x78035000,0x78037000);data[stem+'/CRT-image/metadata.bin']=b''.join(struct.pack('<3I',a,4,0x1000000)for a in pages)
 for a in pages:
  for side in('before','after'):data[stem+'/CRT-image/'+side+'/'+str(a)+'.bin']=bytes(page)if a==pages[0]else bytes(4096)
 data[stem+'/constructor-input/named-API-bindings.bin']=struct.pack('<56I',*bindings);segments=[1,root,77,0xffffffff]
 for name in('cs','ds','es','ss','fs','gs'):
  base=0x211000 if name=='fs'else 0;selector=0x3b if name=='fs'else 0;segments.extend((selector,base,0xfffff if selector else 0,0x21 if selector else 0,1))
 data[stem+'/constructor-input/segments-before.bin']=struct.pack('<34I',*segments);data[stem+'/fs-events.bin']=struct.pack('<8I',1,root,0x4c0317,0,0xffffffff,0xffffffff,0xffffffff,0)+bytes(1184);api=[0]*26;api[20]=0x78037150;api[24]=5;api[25]=0x78004b00;data[stem+'/api-ledger.bin']=struct.pack('<26I',*api);cs=stem+'/constructor-input/CS-API/0/';data[cs+'identity.bin']=struct.pack('<5I',1,0,5,api[20],api[25]);data[cs+'before.bin']=bytes(24);data[cs+'after.bin']=bytes(24)
 class Reader:
  def __init__(self,d):self.d=d
  def data(self,k):return self.d[k]
 for path in ('tools/m4-constructor-original/derive_runner.py','tools/m4-constructor-original/run.py','tools/m4-138-validation-review/prepare_constructor_input_capture_v5.py','tools/m4-startup131-original/run.py','tools/m4-pipeline/stages.py'):
  assert (R/path).is_file();pin(R/path)
 H.validate(Reader(data),stem,root,collections.Counter(),shims);controls=[]
 def bad(name,key,change):
  d=copy.deepcopy(data);d[key]=change(d[key]);rejected=False
  try:H.validate(Reader(d),stem,root,collections.Counter(),shims)
  except (AssertionError,KeyError,struct.error):rejected=True
  assert rejected,name;controls.append(name)
 bad('wrong own FS head',stem+'/constructor-input/segments-before.bin',lambda b:b[:12]+struct.pack('<I',0)+b[16:]);bad('wrong descriptor FS base',stem+'/constructor-input/segments-before.bin',lambda b:b[:100]+struct.pack('<I',0)+b[104:]);bad('missing dynamic CRT page',stem+'/CRT-image/metadata.bin',lambda b:b[:24]);bad('wrong raw shim',stem+'/constructor-input/named-API-bindings.bin',lambda b:b[:8]+struct.pack('<I',0)+b[12:]);bad('short CRT page',stem+'/CRT-image/before/'+str(pages[1])+'.bin',lambda b:b[:-1]);bad('wrong API occurrence identity',cs+'identity.bin',lambda b:b[:4]+struct.pack('<I',1)+b[8:]);bad('short opaque CS output',cs+'after.bin',lambda b:b[:-1]);bad('unexpected IAT endpoint mutation',stem+'/CRT-image/after/'+str(pages[0])+'.bin',lambda b:b[:-1]+bytes([1]));pin(__file__)
 for p in ('reports/m4-138-validation-review/constructor-input-capture-preparation-r5/report.json','reports/m4-138-validation-review/constructor-input-capture-build-r2/build.json','reports/m4-138-validation-review/constructor-input-capture-prelaunch-r2/report.json'):pin(R/p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Unexecuted current37 controller/strict supplement imports/API arity and namespace-only writer inverse; one positive typed synthetic plus eight rejected corruptions. Full inherited validation body retained; new observations append before phase checks.',synthetic_positive=1,rejected_controls=controls,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
