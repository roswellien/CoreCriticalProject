"""Bind exact additive builders/cache and physical full141 compile outputs."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-runway'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 prep=pin(R/'reports/m4-startup141-runway/preparation-r2/report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');p=json.loads(prep.read_bytes())
 build=pin(R/'reports/m4-startup141-runway/build-r2/build.json','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032');b=json.loads(build.read_bytes());assert b['passed']and not b['worker_executed']and not b['execution_admitted']and b['preparation_sha256']==sha(prep)
 rows=[]
 for level in('O0','O2'):
  cache=build.parent/(level+'-objects.cmake');pin(cache,b['files'][str(cache.resolve())]);line=cache.read_text();m=re.fullmatch(r'set\(MW34_OBJECTS (".*") CACHE STRING "Exact inherited physical objects" FORCE\)\n',line);assert m
  entries=json.loads(m.group(1)).split(';');assert entries==[str(Path(v)).replace('\\','/')for v in p['objects'][level]]and len(entries)==410
  command=next(x['arguments']for x in b['commands']if x['log']==level+'-configure.log');assert '-C'in command and command[command.index('-C')+1]==str(cache)
  assert f'-DMW34_CONSTRUCTOR_LIBRARY={p["constructor_libraries"][level]}'in command
  worker=b['workers'][level];pin(worker['path'],worker['sha256']);assert worker['literal_objects']==p['objects'][level]
  rows.append(dict(level=level,worker_path=worker['path'],worker_sha256=worker['sha256'],exact_inherited_COFFER_cache_entries=410,actual_constructor_library_flag=p['constructor_libraries'][level],compiler_dependencies=len(worker['compiler_dependencies'])))
 for q in ['tools/m4-138-constructor-readiness/build_full141.py','tools/m4-138-constructor-readiness/build_full141_v2.py','tools/m4-138-constructor-readiness/build_full141_v2.ps1','tools/m4-joint-startup138/build_v2.py','tools/m4-mfc1168-native/build_connected_fixture.py','tools/m4-138-constructor-readiness/prepare_full141_v2.py','tools/m4-138-constructor-readiness/prepare_union_service.py']:pin(R/q)
 pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Exact new full141 builder namespace/constructor-library flags/410COFFER cache/physical output lineage; independent full source/link prelaunch remains pending',
  preparation_sha256=sha(prep),build_sha256=sha(build),levels=rows,worker_executed=False,archive_reader_opened=False,execution_admitted=False,initializer_credit=0,independent_prelaunch_pending=True,files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),levels=rows)))
if __name__=='__main__':main(sys.argv[1])
