"""Whole native component targets compared to independently computed source."""
import struct,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]
NAMED=R/'reports/m4-138-validation-review/constructor-provider-named-proof-r1/report.json'
DEPENDENCY=R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json'
def need(v,s):
 if not v:raise ValueError(s)
def install_named(m,o):
 d=json.loads(o.pin(NAMED,'0bfde9d0b381efd15ed762cb8ecb81a79a61a26f7a9439f3c3897f6a21aef6ec').read_bytes());e=json.loads(o.pin(DEPENDENCY,'4c91796493b1a91d9df78f3221fb53d146d9990da9edee4454d779adc3473755').read_bytes())
 need(d['passed']and e['passed']and e['program_rows']==7389 and e['callback_sites']==415,'Current exact physical named-provider and full literal54 dependency closure')
 for path,h in d['files'].items():o.pin(path,h)
 targets=d['targets'];need(targets=={'823':0x5f401ea0,'825':0x5f401782,'malloc':0x780012b3,'free':0x78001390,'_onexit':0x78004a36},'Whole independently named PE export identities')
 bindings={(0x5abd1a,0x5bb4c8):(0x80000339,targets['825']),(0x5abd26,0x5bb4bc):(0x80000337,targets['823']),(0x5ac11e,0x5bb52c):(0x1decb0,targets['_onexit'])}
 def prove(machine,pc,address,raw,target):
  need((pc,address)in bindings and bindings[pc,address]==(raw,target)and int.from_bytes(machine.bytes(address,4),'little')==raw,'Same carried owning raw ordinal/named import cell joins physical module proof')
  row=machine.program[pc];need(machine.bytes(pc,row['width']).hex()==row['bytes_hex'],'Entire carried literal import instruction equals pinned physical source')
  need(row['mnemonic']==('call'if pc==0x5ac11e else'jmp'),'Exact original owning CALL/JMP import form')
  return True
 m.constructor_named_input_prover=prove
def compare(a,seq,root,before,m,proof,o):
 stem=f'sequence-{seq}/Constructors/root-{root}/'
 for side,state,cpu,fx in(('before',before['State'],before['CPU'],before['FX']),('after',m.state,m.projected_cpu(),m.fx)):
  need(a.data(stem+side+'/State.bin')==bytes(state),'Whole constructor '+side+' State from same carried source')
  need(a.data(stem+side+'/CPU.bin')==struct.pack('<10I',*cpu),'Whole constructor '+side+' CPU from same carried source')
  need(a.data(stem+side+'/FX.bin')==bytes(fx),'Whole constructor '+side+' FX from same carried source')
 def delta(name,fmt,expected):
  first=a.data(stem+'before/'+name+'.bin');last=a.data(stem+'after/'+name+'.bin');need(last.startswith(first),'Complete unchanged cumulative constructor '+name+' prefix');n=struct.calcsize(fmt);need(len(first)%n==len(last)%n==0,'Whole typed constructor '+name+' extent');actual=list(struct.iter_unpack(fmt,last[len(first):]));need(actual==[tuple(r)for r in expected],'Entire constructor '+name+' source-derived delta')
 delta('accesses','<IIQII',proof['component_source_accesses'])
 delta('calls','<12I',proof['constructor_call_results'])
 delta('FS-events','<12I',proof['component_FS_rows'])
 getters=[]
 for g in proof['source_getters']:
  owner=next(a for a in m.responses.allocations if a['guest']==g['published_owner']and a['live']);getters.append((root,g['PC'],g['frame']-4,g['PC']+5,g['receiver'],g['vptr'],g['slot'],g['target'],g['header'],g['count'],owner['generation'],len(g['graph'])))
 delta('getters','<12I',getters)
 need(a.data(stem+'after/frames.bin')==a.data(stem+'after/FS-frames.bin')==b'','Whole source constructor call/FS stacks returned empty')
 proof['whole_native_component_journals_compared']=True;proof['whole_native_State_CPU_FX_compared']=True;proof['source_seed']=False
