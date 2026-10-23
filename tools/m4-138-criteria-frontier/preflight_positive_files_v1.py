"""Bounded source-only full-file inverse/adverse checks; no checker main."""
from pathlib import Path
import json,hashlib,ast,runpy,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prepdir=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r6';pr=json.loads((prepdir/'report.json').read_bytes());out=prepdir.parent/'positive-files-preflight-r1';assert not out.exists();pins={str(prepdir/'report.json'):sha(prepdir/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for p,h in pr['files'].items():assert sha(Path(p))==h;pins[p]=h
base=R/'tools/m4-138-criteria-frontier/check_schema138_v3.py';ns=runpy.run_path(str(base),run_name='definition_only');s=(R/'tools/m4-138-criteria-frontier/check_schema138_v5.py').read_text();d=pr['checker_source_delta'];assert s.replace(d['anchor']+d['addition'],d['anchor']).replace(d['after'],d['before'])==ns['s']
tree=ast.parse(s);m=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');tr=next(x for x in m.body if isinstance(x,ast.Try));fn=next(x for x in tr.body if isinstance(x,ast.FunctionDef)and x.name=='prove_positive_file');isolated=ast.Module(body=[fn],type_ignores=[])
def blob(p,h=None):
 p=Path(p).resolve();assert p.stat().st_size<16*1024*1024;v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p.read_bytes()
def read(p,h=None):return json.loads(blob(p,h))
folder=R/'reports/m4-joint-startup138/preparation-r4';p=read(folder/'report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a');pf=R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5'
wc=read(p['widget_component_preparation'],p['widget_component_preparation_sha256']);wp=Path(p['widget_component_preparation']).parent;contracts=read(wp/'contracts.json',wc['files'][str(wp/'contracts.json')]);newroots=[x['root']for x in contracts['roots']]
original=read(R/'reports/m4-fps-original/preparation-r1/report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1');fixed=[int(v,16)for v in re.search(r' pages\{([^}]+)',blob(pf/'joint_protocol.hpp').decode())[1].split(',')]
env=dict(re=re,blob=blob,read=read,prep=p,folder=folder,original_widget=original,fixed=fixed,newroots=newroots,contracts=contracts);exec(compile(isolated,'exact positive source inverse','exec'),env);f=env['prove_positive_file'];tests=[]
def trial(label,rel,before,after,bad=False):
 try:f(Path(rel),before,after)
 except (AssertionError,KeyError):assert bad
 else:assert not bad,'Adverse admitted '+label
 tests.append(dict(label=label,passed=True,adverse=bad))
for n in ['onexit_session.hpp','registration_contract.hpp']:
 a=blob(pf/n);b=blob(folder/n);trial('actual whole '+n,n,a,b)
 trial('undeclared byte '+n,n,a,b+b' ' ,True)
 if n=='onexit_session.hpp':
  trial('additional field changes class layout',n,a,b.replace(b' void finish()',b' unsigned extra;\n void finish()'),True)
  trial('alter borrowed ABI',n,a,b.replace(b'unsigned frame',b'unsigned long long frame'),True)
 else:
  trial('remove inherited root',n,a,b.replace(b'0x410210,',b''),True)
  trial('alter old callback order',n,a,b.replace(b'0x410210,0x410260',b'0x410260,0x410210'),True)
  trial('arbitrary added observation page',n,a,b.replace(b'0x5d0000',b'0x5d1000'),True)
out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Actual bounded positive header inverses and adverse mutations only; no main checker, compiler, guest worker, archive, or source machine',exact_checker_inverse=True,tests=tests,files=pins),indent=2)+'\n');print(sha(q))
