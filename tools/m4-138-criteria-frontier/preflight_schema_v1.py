"""Synthetic/adverse checks and exact extraction inverse only; no worker/resources."""
from pathlib import Path
import ast, collections, hashlib, json, runpy, struct, sys, textwrap, types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name,preparation,expected):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists()
 prep=Path(preparation).resolve();p=prep/'report.json';assert sha(p)==expected
 report=json.loads(p.read_bytes());assert report['passed'];pins={str(p):expected}
 for path,h in report['files'].items():
  if Path(path).suffix=='.py':assert sha(path)==h;pins[path]=h
 for r in report['relations']:
  p=prep/r['file'];assert sha(p)==report['files'][str(p)];s=p.read_text();ast.parse(s)
  for c in reversed(r['changes']):assert c['after']in s;s=s.replace(c['after'],c['before'])
  parent=(prep/'accepted131-materialized.py').read_text();assert textwrap.indent(s,'  ')in parent or textwrap.indent(s,'   ')in parent
 # Checker definitions only; its strict admitted main is never called.
 ns=runpy.run_path(str(R/'tools/m4-138-criteria-frontier/check_schema138_v2.py'),run_name='synthetic_definition_only')
 tests=[]
 def good(label,f):f();tests.append(dict(label=label,passed=True,adverse=False))
 def bad(label,f):
  try:f()
  except (AssertionError,KeyError,ValueError,struct.error):tests.append(dict(label=label,passed=True,adverse=True))
  else:raise AssertionError('Adverse incorrectly admitted: '+label)
 sparse=ns['sparse'];unique=ns['unique']
 packet=b'SYNTHETC'+struct.pack('<I',1)+struct.pack('<II',0x401000,1)+bytes(4096)
 good('one whole sparse page',lambda:sparse(packet))
 bad('truncated sparse endpoint',lambda:sparse(packet[:-1]))
 bad('extra undeclared sparse endpoint byte',lambda:sparse(packet+b'x'))
 bad('duplicate sparse physical owner',lambda:sparse(packet[:8]+struct.pack('<I',2)+packet[12:]*2))
 good('two distinct physical keys',lambda:unique([dict(k=1),dict(k=2)],lambda x:x['k']))
 bad('duplicate physical function identity',lambda:unique([dict(k=1),dict(k=1)],lambda x:x['k']))
 class C:
  @staticmethod
  def linked_candidates(image,raw,relocs):return [(image.image_base,raw)]
 class N:
  dirty=False
  @staticmethod
  def directories(image):return {9:(0x100,40)}
  @staticmethod
  def image_bytes(image,address,size):
   if size==40:return struct.pack('<4Q2I',0x1000,0x1040,0,0,0,0)
   return bytes([1 if N.dirty else 0])*size
 env=dict(C=C,N=N,struct=struct,links=[],counts=collections.Counter())
 exec(compile((prep/'native-TLS.py').read_text(),str(prep/'native-TLS.py'),'exec'),env)
 image=types.SimpleNamespace(image_base=0x140000000)
 symbol=dict(name='?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA',section=1,value=0)
 rel=dict(type=11,offset=0,symbol=symbol)
 raw=bytes(4);sections={1:dict(bytes=bytes(24))}
 good('exact retained named TLS relocation',lambda:env['linked_candidates'](image,raw,[rel]))
 bad('unknown TLS symbol',lambda:env['linked_candidates'](image,raw,[dict(rel,symbol=dict(symbol,name='arbitrary_owner'))]))
 bad('TLS unresolved section',lambda:env['linked_candidates'](image,raw,[dict(rel,symbol=dict(symbol,section=0))]))
 bad('unsupported relocation kind',lambda:env['linked_candidates'](image,raw,[dict(rel,type=3)]))
 bad('relocation field outside whole function',lambda:env['linked_candidates'](image,raw,[dict(rel,offset=1)]))
 good('exact initialized eight-byte TLS subspan',lambda:env['TLS_relations'](image,raw,raw,[rel],sections))
 N.dirty=True
 bad('nonzero actual TLS initialization',lambda:env['TLS_relations'](image,raw,raw,[rel],sections));N.dirty=False
 bad('TLS initialized extent overflow',lambda:env['TLS_relations'](image,raw,struct.pack('<i',60),[rel],sections))
 bad('nonzero source TLS declaration',lambda:env['TLS_relations'](image,raw,raw,[rel],{1:dict(bytes=b'\1'+bytes(23))}))
 linked=ast.parse((prep/'native-linked.py').read_text());fn=next(n for n in linked.body if isinstance(n,ast.FunctionDef)and n.name=='current_body_matches')
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'synthetic_body_attribution','exec'),env)
 env.update(image=image,bridge_targets={'source_bridge':image.image_base+4})
 source=dict(type=4,offset=0,symbol=dict(name='source_bridge',section=1,value=0))
 good('exact source bridge target',lambda:env['current_body_matches'](raw,[source]))
 good_rows=env['current_body_matches'](raw,[source]);assert len(good_rows)==1
 env['bridge_targets']['source_bridge']+=1
 # A no-match is correctly returned to the retained caller's exact len==1 assertion.
 bad('wrong actual source bridge target',lambda:assert_one(env['current_body_matches'](raw,[source])))
 bad('body without owned source bridge',lambda:env['current_body_matches'](raw,[dict(source,symbol=dict(name='arbitrary',section=1,value=0))]))
 out.mkdir(parents=True)
 for p in [Path(__file__).resolve(),R/'tools/m4-138-criteria-frontier/check_schema138_v1.py',R/'tools/m4-138-criteria-frontier/check_schema138_v2.py']:pins[str(p)]=sha(p)
 result=dict(passed=True,scope='Exact baseline fragment inverse plus synthetic/adverse bounded schema guards only, no actual physical gate evaluation',checks=len(tests),tests=tests,actual_current_schema_checker_executed=False,resource_main_invoked=False,archive_reader_opened=False,source_machine_executed=False,worker_launched=False,allowance_created=False,configuration_created=False,acceptance_executed=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),checks=len(tests))))
def assert_one(rows):assert len(rows)==1
if __name__=='__main__':main(*sys.argv[1:])
