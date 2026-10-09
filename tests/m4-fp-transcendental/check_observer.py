"""Cause-specific mutations of actual saved cosine records."""
from pathlib import Path
import copy
import json
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-fp-transcendental'))
import analyze_full as full
a=full.directed;b=a.base
original,native,directory=map(lambda p:Path(p).resolve(),sys.argv[1:4])
b.require(directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') and not directory.exists(),'Fresh observer controls required')
corpus=ROOT/'tools/m4-fp-transcendental/directed/corpus.hpp'
inputs=[int(x,16) for x in re.findall(r'0x([0-9a-f]{16})ULL',corpus.read_text())]
pack=(ROOT/'reports/m4-fp-startup/research-r1/pages.bin').read_bytes()
reference=a.originals(original.read_bytes());records=list(a.natives(native.read_bytes()));results=[]

def issues(n,o):
    return b.check([n],{n['tag'][:4]:o})['issues']+a.extra([n],{n['tag'][:4]:o},pack,inputs)+full.seed_issues([n])

def corrupt(name,field,offset,wanted,index=0,paired=False,mask=1):
    n=copy.deepcopy(records[index]);o=reference[n['tag'][:4]];raw=bytearray(n[field]);raw[offset]^=mask;n[field]=bytes(raw)
    if paired:
        other='state1' if field=='state0' else 'state0';raw=bytearray(n[other]);raw[offset]^=1;n[other]=bytes(raw)
    found=issues(n,o)
    b.require(any(wanted in r['field'] for r in found),'Wrong observer cause '+name)
    results.append({'name':name,'record':index,'field':field,'offset':offset,'xor_mask':mask,'intended_cause':wanted,'paired_mutation':paired})

for field in ['cpu0','cpu1','mem0','mem1','env0','env1']:corrupt(field,field,0,field)
for field in ['fx0','fx1']:corrupt(field+' CW',field,0,'FX')
for offset,name in [(12,'legacy FIP'),(18,'legacy FOP'),(20,'legacy FDP')]:corrupt(name,'env1',offset,'env1')
corrupt('sticky DE','fx1',2,'FX',48,mask=2)
corrupt('last-store C1','fx1',3,'FX',576,mask=2)
corrupt('FCOS range C2','fx1',3,'FX',528,mask=4)
corrupt('dead raw80','fx1',144,'FX')
corrupt('complete State allowed status','state1',2741,'Complete State after-model',528)
corrupt('complete State protected','state1',3333,'Protected State')
corrupt('paired State opaque seed','state0',3333,'Complete State seed',paired=True)
for field,offset in [('host1',0),('host1',32),('host1',160),('host1',24),('henv1',12)]:corrupt('host '+field+str(offset),field,offset,'host')
for position in range(4):
    n=copy.deepcopy(records[0]);event=list(n['events'][0]);event[position]^=1;n['events'][0]=tuple(event)
    b.require(any('Actual ordered events' in r['field'] for r in issues(n,reference[n['tag'][:4]])),'Mutated actual event admitted')
    results.append({'name':'event '+str(position),'intended_cause':'Actual ordered events'})
for position in [0,7]:
    n=copy.deepcopy(records[0]);counts=list(n['counts']);counts[position]^=1;n['counts']=tuple(counts)
    b.require(any('counts' in r['field'] for r in issues(n,reference[n['tag'][:4]])),'Mutated actual count admitted')
    results.append({'name':'count '+str(position),'intended_cause':'Actual bridge/primitive counts'})
raw=native.read_bytes()
for name,offset in [('magic',0),('count',12),('record-size',16)]:
    changed=bytearray(raw);changed[offset]^=1
    try:list(a.natives(changed))
    except ValueError as e:b.require('layout differs' in str(e),'Wrong header rejection')
    else:raise ValueError('Malformed header admitted '+name)
    results.append({'name':'header '+name,'intended_cause':'Actual directed native layout differs'})
directory.mkdir(parents=True);report={'passed':True,'scope':'Actual saved-record mutations; no new body execution or broad-state admission',
  'controls':results,'bindings':{str(p):b.digest(p) for p in [Path(__file__).resolve(),Path(full.__file__),Path(a.__file__),Path(b.__file__),corpus,original,native]}}
(directory/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('Cosine observer controls:',len(results))
