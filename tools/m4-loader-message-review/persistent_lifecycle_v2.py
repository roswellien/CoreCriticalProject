"""Unexecuted carried1100 lifecycle adapter. No bootstrap or provider defaults."""
import hashlib,json

CONSUMERS={'je':('ZF',),'jne':('ZF',),'jb':('CF',),'jae':('CF',),'jbe':('CF','ZF'),'ja':('CF','ZF'),'jl':('SF','OF'),'jge':('SF','OF'),'jle':('ZF','SF','OF'),'jg':('ZF','SF','OF'),'setl':('SF','OF'),'sbb':('CF',)}
def need(v,message):
 if not v:raise ValueError(message)

class CarriedLifecycle:
 """Bind onto a live source Machine; caller imports sealed interpreter/SAR.

 provider must own current module/IAT/fdiv/heap/API effects and provide methods
 authorize_entry, authorize_control, imported_data_read, dispatch, finish.
 region_guard and flag_tracker are the retained source-owned permissions and
 flag-definition authorities. No flag, operand, frame, API return or State is
 initialized here. Caller supplies the complete exact program and callbacks.
 """
 def __init__(self,machine,program_bytes,callback_bytes,provider,region_guard,flag_tracker,ledger):
  need(hashlib.sha256(program_bytes).hexdigest()=='a25bed469f6b0e8ce5054e638b9de02a9e3303d5af01d0299298048146a86af2','Exact sealed physical1100 program bytes')
  need(hashlib.sha256(callback_bytes).hexdigest()=='71ae25eb20c57dcc3518f88b18c91a73e994315cc52f703494dae05f60caca38','Exact compiled952 callback attribution bytes')
  rows=json.loads(program_bytes)['rows'];program={r['pc']:r for r in rows};callbacks={int(k):tuple(v)for k,v in json.loads(callback_bytes)['State_offsets_by_original_PC'].items()}
  need(len(rows)==len(program)==1100 and len(callbacks)==160,'Exact1100 physical program/952 callback scope')
  need(all(k==v['pc']for k,v in program.items()),'Exact program PC identities')
  need(all(callable(getattr(provider,n,None))for n in('authorize_entry','authorize_control','imported_data_read','dispatch','finish')),'No default typed provider effects')
  need(callable(region_guard)and callable(ledger),'Explicit source owner/ledger')
  need(all(callable(getattr(flag_tracker,n,None))for n in('before','after','provider_transition')),'Complete carried flag causality authority')
  self.machine=machine;self.provider=provider;self.region_guard=region_guard;self.flags=flag_tracker;self.ledger=ledger;self.old_hook=machine.hook
  need(all(k not in machine.program or machine.program[k]==v for k,v in program.items()),'No changed inherited source instruction')
  need(all(k not in machine.callbacks or tuple(machine.callbacks[k])==tuple(v)for k,v in callbacks.items()),'No changed inherited undefined callback policy')
  machine.program.update(program);machine.callbacks.update(callbacks)
  Base=type(machine)
  class LiteralMachine(Base):
   def step(m):
    row=m.program[m.cursor]
    if row['mnemonic']not in('setl','cdq'):return super().step()
    m.steps+=1;need(m.steps<=40000000,'Finite literal lifecycle budget')
    m.word(2472,m.cursor);m.PCs.append(m.cursor);m.emit('instruction-before',row=row);m.cursor=(m.cursor+row['width'])&0xffffffff
    if row['mnemonic']=='cdq':
     need(row['bytes_hex']=='99'and not row['decoded_operands'],'Exact inherited CDQ form');m.reg('edx',0xffffffff if m.reg('eax')&0x80000000 else 0)
    else:
     need(row['bytes_hex'].startswith('0f9c')and len(row['decoded_operands'])==1,'Exact inherited SETL form');m.destination(row['decoded_operands'][0],bool(m.flag('SF'))!=bool(m.flag('OF')))
    for offset in m.callbacks.get(row['pc'],()):
     m.state[offset]=0;m.undefined.append((row['pc'],offset,0));m.emit('undefined',pc=row['pc'],offset=offset,value=0)
    m.emit('instruction-after',row=row)
  machine.__class__=LiteralMachine;machine.hook=self.hook
 def hook(self,m,event,data):
  if event=='instruction-before':
   row=data['row'];self.flags.before(m,row,CONSUMERS.get(row['mnemonic'],()))
  elif event=='instruction-after':self.flags.after(m,data['row'])
  elif event in('read-before','write-before'):
   need(self.region_guard(m,event,data)is True,'Exactly owned current physical source access')
   if event=='read-before':self.provider.imported_data_read(m,data)
  elif event=='control':self.provider.authorize_control(m,data)
  self.ledger(m,event,data)
  if self.old_hook:self.old_hook(m,event,data)
 def notify(self,instance,reason,reserved,source_entry_witness):
  """Caller has already committed genuine stdcall3 frame and source entry."""
  m=self.machine;need(reason in(0,1,2,3),'Finite genuine DLL reason')
  need(m.cursor==m.word(2472)==0x10001b30 and m.call_stack,'Genuine carried DLL entry')
  frame=m.reg('esp');need(m.call_stack[-1][0:2]==(0x10001b30,frame),'Current source entry frame')
  # Provider authenticates actual SSBASE, all16 frame bytes, caller/instance,
  # owning thread/generation, reason/reserved and current source entry witness.
  entry=self.provider.authorize_entry(m,instance,reason,reserved,source_entry_witness)
  need(entry['frame']==frame and entry['root']==0x10001b30 and entry['reason']==reason,'Exact typed DLL entry')
  need(entry['current_owned_module_identity']and entry['source_frame16_proven']is True,'Real current source owner/frame, no token-only witness')
  stop=entry['return_pc'];before=hashlib.sha256(bytes(m.state)).hexdigest();base_calls=len(m.call_stack)
  def api(machine,target):
   proof=self.provider.dispatch(machine,target)
   need(proof['complete_current_source_transfer']is True and proof['no_AFTER_or_operand_seed']is True,'Typed current CRT transfer; no guessed scalar return')
   self.flags.provider_transition(machine,proof)
  m.run(lambda x:x.cursor==stop,api=api)
  need(len(m.call_stack)==base_calls-1 and m.reg('esp')==frame+16,'Literal stdcall3 RET12/frame balance')
  result=self.provider.finish(m,entry)
  need(result['whole_source_journal_accounted']is True and result['current_allocator_lifetimes_checked']is True,'Complete source/lifecycle ownership')
  return dict(reason=reason,before_State_sha256=before,after_State_sha256=hashlib.sha256(bytes(m.state)).hexdigest(),provider_proof=result,no_reseed=True,source_frame=frame,source_return=stop)
