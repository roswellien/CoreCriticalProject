"""Cause-specific corruption checks against actual directed saved records."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('directed',ROOT/'tools/m4-fp-directed/analyze.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
original,native,output=map(lambda p:Path(p).resolve(),sys.argv[1:4])
if output.exists():raise ValueError('Fresh control report required')
corpus=(ROOT/'tools/m4-fp-directed/corpus.hpp').read_text();inputs=[int(v,16) for v in a.re.findall(r'0x[0-9a-f]{8}',corpus)]
reference=a.parse_original(original.read_bytes(),inputs,(ROOT/'reports/m4-fp-startup/research-r1/pages.bin').read_bytes());records=list(a.parse_native(native.read_bytes()))
results=[]
def corrupt(name,field,offset,cause,index=0):
    r=copy.deepcopy(records[index]);key=r['tag'][:4];raw=bytearray(r[field]);raw[offset]^=1;r[field]=bytes(raw)
    result=a.first.check([r],{key:reference[key]})
    if not any(cause in issue['field'] for issue in result['issues']):raise ValueError('Wrong observer cause: '+name)
    results.append({'name':name,'record':index,'field':field,'offset':offset,'intended_cause':cause})
for field in ('cpu0','cpu1','mem0','mem1','env0','env1'):corrupt(field,field,0,field)
for field in ('state0','state1'):corrupt('protected '+field,field,3333,'protected State')
for field in ('fx0','fx1'):corrupt(field+' CW',field,0,'architectural span')
corrupt('legacy store FIP','env1',12,'env1');corrupt('legacy store FOP','env1',18,'env1');corrupt('legacy store FDP','env1',20,'env1')
corrupt('DE accumulated','fx1',2,'architectural span',48)
corrupt('C1 rounding','fx1',3,'architectural span',240)
corrupt('raw dead ST storage','fx1',32+7*16,'architectural span')
for field,offset in (('host1',0),('host1',32),('host1',160),('host1',24),('henv1',12)):corrupt('host '+field+' '+str(offset),field,offset,'host')
for name in ('event address','event value','event width','event operation','count','complete domain key'):
    r=copy.deepcopy(records[0]);key=r['tag'][:4]
    if name.startswith('event'):
        pos=('event address','event value','event width','event operation').index(name);event=list(r['events'][0]);event[pos]^=1;r['events'][0]=tuple(event);wanted='actual ordered bridge events'
    elif name=='count':values=list(r['counts']);values[0]^=1;r['counts']=tuple(values);wanted='bridge counts'
    else:r['tag']=(12345,*r['tag'][1:]);wanted='Native key'
    try:result=a.first.check([r],{key:reference[key]})
    except ValueError as e:
        if wanted not in str(e):raise
    else:
        if not any(wanted in issue['field'] for issue in result['issues']):raise ValueError('Observer admitted: '+name)
    results.append({'name':name,'record':0,'intended_cause':wanted})
for name,mutation in [('magic',lambda b:b.__setitem__(0,b[0]^1)),('count',lambda b:b.__setitem__(12,b[12]^1)),('record extent',lambda b:b.__setitem__(16,b[16]^1))]:
    changed=bytearray(native.read_bytes());mutation(changed)
    try:list(a.parse_native(changed))
    except ValueError as e:
        if 'extent/header' not in str(e):raise
    else:raise ValueError('Observer admitted malformed header: '+name)
    results.append({'name':'native header '+name,'intended_cause':'Directed native extent/header'})
output.parent.mkdir(parents=True,exist_ok=True);report={'passed':True,'controls':results,'scope':'Cause-specific actual record corruptions, not a fresh execution or full-domain admission',
    'bindings':{str(p):a.digest(p) for p in (Path(__file__).resolve(),Path(a.__file__),ROOT/'tools/m4-fp-native/analyze_first.py',original,native)}}
output.write_text(json.dumps(report,indent=2)+'\n');print('Directed raw observer controls:',len(results))
