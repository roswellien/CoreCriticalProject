"""Finite current141 CRT data-page source/API operand disjointness probe (v2).

v2: v1 collected only [pc,address,value,width,write] rows and silently found
zero rows in five native source6 artifacts. v2 also extracts dict-shaped
accesses (address+width, field, read_address, record_address, slot, guest_CS24,
provenance) and [pc,address,value] state_reads (width4, conservative), and
refuses any artifact that still yields zero operands.

Recomputes the unused CRT page 78037000 input offsets U from the current own
original141/native141 BEFORE inputs (all six sequences, O0/O2) minus the typed
lock25/lock13/registry cells, checks U equals the inherited set, then streams
every current original and native source/API derivation artifact (case by case;
the 181MB widget file is never loaded whole) and collects every well-typed access
row [pc,address,value,width,write]. Any byte of any row on U is a violation.
Proves disjointness for the ledgers present only; inventory completeness,
whole-page policy and paired141 credit are NOT claimed.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PAGE=0x78037000
TYPED=set(range(0x8c,0x90))|set(range(0x130,0x148))|set(range(0x888,0x890))
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
INHERITED_DOMAINS='reports/m4-startup138-paired/CRT-lock13-domain-r2/domains.json'
WIDTHS={1,2,4,8,10,16}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def is_row(v):
 return type(v)is list and len(v)==5 and all(type(x)is int for x in v)and v[3]in WIDTHS and v[4]in(0,1)and 0<=v[1]<2**32
NAMED_WIDTH={'address':None,'field':4,'read_address':4,'record_address':8,'slot':4,'guest_CS':24}
def scan(node,path,found):
 if type(node)is dict:
  for k,w in NAMED_WIDTH.items():
   a=node.get(k)
   if type(a)is int and 0<=a<2**32 and a!=0xffffffff:
    width=(node.get('width')if type(node.get('width'))is int else 4)if w is None else w
    if type(width)is int and width>0:found[path+('@'+k,)].append([node.get('pc',node.get('write_pc',node.get('PC',0)))or 0,a,0,width,1 if node.get('writing')else 0])
  for k,v in node.items():
   if k=='state_reads'and type(v)is list and v and all(type(t)is list and len(t)==3 and all(type(x)is int for x in t)for t in v):found[path+(k,)].extend([t[0],t[1],t[2],4,0]for t in v);continue
   scan(v,path+(k,),found)
 elif type(node)is list:
  if node and all(is_row(x)for x in node):found[path].extend(node)
  else:
   for x in node:
    if type(x)in(dict,list):scan(x,path+('[]',),found)
def stream_cases(path,J):
 with Path(path).open(encoding='utf-8')as f:
  s=J.StreamJSON(f);s.expect('[');first=True
  while True:
   s.trim()
   if s.buf.startswith(']'):s.buf=s.buf[1:];break
   if not first:s.expect(',')
   first=False;yield s.value()
  s.finish()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);D=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');J=load('stream_json',R/'tools/m4-138-controls-review/full_raw_review_v2.py')
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());assert V['passed']and V['reader_closed']
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True
 def page_reader(row,pattern):
  i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256']);es=D.entries(i,re.compile(pattern))
  def rd(k):
   z=es[k]
   with p.open('rb')as f:f.seek(z['offset']);b=f.read(z['bytes'])
   assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
  return i,p,rd
 oi,op,ord_=page_reader(next(e for e in V['paired_exports']if e['branch']=='original'),r'phase/[0-5]/0/CRT-before/2013491200\.bin')
 unused=set();per_domain={}
 for lv in('O0','O2'):
  ni,np_,nrd=page_reader(next(e for e in N['paired_exports']if e['branch']==lv),r'sequence-[0-5]/phase-0-before-page-2013491200\.bin')
  for s in range(6):
   a=ord_(f'phase/{s}/0/CRT-before/2013491200.bin');b=nrd(f'sequence-{s}/phase-0-before-page-2013491200.bin');u={i for i in range(4096)if a[i]!=b[i]}-TYPED;unused|=u;per_domain[f'{lv}-{s}']=len(u)
  assert sha(ni)==pins[str(ni)]and sha(np_)==pins[str(np_)]
 assert sha(oi)==pins[str(oi)]and sha(op)==pins[str(op)]
 inherited=json.loads(pin(R/INHERITED_DOMAINS).read_bytes());inherited_unused=set().union(*(set(d['unused_input_offsets'])for d in inherited))-set(range(0x8c,0x90))
 # Current source/API derivation artifacts: original six families plus
 # constructor18, native36 and every native source6 family derivation file.
 artifacts=[]
 for leaf in sorted((R/'reports/m4-original141-source/source-r4-constructors').glob('original-*/source-derivation.json')):artifacts.append(('original','constructor18',leaf))
 artifacts+=[('original','formatter4',R/'reports/m4-original141-source/source-r4-formatters/source-derivations.json'),('original','old4',R/'reports/m4-original141-source/source-r4-old4/original-source-access-ledgers.json'),
  ('original','MFC',R/'reports/m4-original141-source/source-r5-MFC/source-derivations.json'),('original','widget',R/'reports/m4-original141-source/source-r7-widgets/source-derivations.json'),('original','tree',R/'reports/m4-original141-tree-source/source-r1/original-Tree-source-derivations.json')]
 for leaf in sorted((R/'reports/m4-startup141-paired/native36-source-r9').glob('O*-*/source-derivation.json')):artifacts.append(('native','native36',leaf))
 for leaf in sorted((R/'reports/m4-startup141-source/combined-source-provider-r6').glob('*-derivations.json')):artifacts.append(('native','source6-'+leaf.stem,leaf))
 assert sum(1 for a in artifacts if a[1]=='constructor18')==18 and sum(1 for a in artifacts if a[1]=='native36')==36
 inventory=[];violations=[];rows_total=0;crt_rows=0
 for branch,family,path in artifacts:
  pin(path);found=collections.defaultdict(list);cases=0
  if path.name in('source-derivation.json',):scan(json.loads(path.read_bytes()),(),found);cases=1
  else:
   for case in stream_cases(path,J):scan(case,(),found);cases+=1
  n=0;on_page=0
  for keypath,rows in found.items():
   for pc,address,value,width,write in rows:
    n+=1
    if address+width<=PAGE or address>=PAGE+4096:continue
    on_page+=1;hit=sorted({x-PAGE for x in range(max(address,PAGE),min(address+width,PAGE+4096))}&unused)
    if hit:violations.append(dict(branch=branch,family=family,artifact=str(path),key='/'.join(keypath),pc=pc,address=address,width=width,write=write,unused_offsets=hit))
  assert n>0,'Every artifact yields collected operands: '+str(path)
  rows_total+=n;crt_rows+=on_page;inventory.append(dict(branch=branch,family=family,artifact=str(path),cases=cases,access_rows=n,CRT_data_page_rows=on_page,keys=sorted('/'.join(k)for k in found)))
 for p_,h in list(pins.items()):assert sha(p_)==h,'Whole input unchanged after reads: '+p_
 rp=out/'footprint.json';rp.write_text(json.dumps(dict(unused_offsets=sorted(unused),inventory=inventory,violations=violations[:5000]),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=not violations and unused==inherited_unused,scope='Current141 CRT data page unused-offset disjointness for every collected source/API access row in current original/native derivation artifacts; not inventory completeness, typed buffer closure, whole-page policy or credit',
  unused_offsets=len(unused),unused_equals_inherited=unused==inherited_unused,per_domain_unused=per_domain,artifacts=len(artifacts),access_rows=rows_total,CRT_data_page_rows=crt_rows,violations=len(violations),
  families={f:sum(1 for a in artifacts if a[1]==f)for f in sorted({a[1]for a in artifacts})},inventory_completeness_claim=False,output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),
  capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','unused_offsets','unused_equals_inherited','artifacts','access_rows','CRT_data_page_rows','violations','families')}))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
