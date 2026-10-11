"""Finite architectural flag-read validation, before any source step.

Serializer reads and incidental interpreter implementation reads are excluded.
The declared instruction operation determines architectural consumers.
"""
import flag_domain as F

CC = {'o':('OF',),'no':('OF',),'b':('CF',),'c':('CF',),'nae':('CF',),'ae':('CF',),'nb':('CF',),'nc':('CF',),'e':('ZF',),'z':('ZF',),'ne':('ZF',),'nz':('ZF',),'be':('CF','ZF'),'na':('CF','ZF'),'a':('CF','ZF'),'nbe':('CF','ZF'),'s':('SF',),'ns':('SF',),'p':('PF',),'pe':('PF',),'np':('PF',),'po':('PF',),'l':('SF','OF'),'nge':('SF','OF'),'ge':('SF','OF'),'nl':('SF','OF'),'le':('ZF','SF','OF'),'ng':('ZF','SF','OF'),'g':('ZF','SF','OF'),'nle':('ZF','SF','OF')}
def names(machine,row):
 op=row['mnemonic']
 if op in('adc','sbb','cmc'):return ('CF',)
 if op in('lahf',):return ('CF','PF','AF','ZF','SF')
 if op in('pushf','pushfd'):return tuple(F.BITS)
 if op in('loopz','loope','loopnz','loopne'):return ('ZF',)
 for prefix in('cmov','set','j'):
  if op.startswith(prefix):
   suffix=op[len(prefix):]
   if op in('jmp','jecxz','jcxz'):return ()
   if suffix not in CC:raise ValueError('Unadmitted architectural condition '+op)
   return CC[suffix]
 if op in('rcl','rcr'):
  args=row['decoded_operands'];n=F.count(machine,args[1])if len(args)>1 else 1;return ('CF',)if n else ()
 if op in('scasb','scasw','scasd','lodsb','lodsw','lodsd','stosb','stosw','stosd','movsb','movsw','movsd','cmpsb','cmpsw','cmpsd'):
  return ('DF',)if not row.get('repeat')or machine.reg('ecx')else ()
 return ()
def check(machine,row,prior):
 used=names(machine,row)
 if any(n in prior for n in used):raise ValueError('Source consumes architecturally undefined flag at '+hex(row['pc'])+' '+str({n:prior[n]for n in used if n in prior}))
 return dict(PC=row['pc'],mnemonic=row['mnemonic'],flags=list(used),values={n:int(machine.flag(n))for n in used},undefined_before=dict(prior),all_consumers_defined=True)if used else None
def advance(machine,row,prior):
 """Source semantics plus physically recovered undefined-flag callbacks."""
 out=F.advance(machine,row,prior)
 inverse={2065:'CF',2067:'PF',2069:'AF',2071:'ZF',2073:'SF',2075:'DF',2077:'OF'}
 for offset in machine.callbacks.get(row['pc'],()):
  if offset in inverse:out[inverse[offset]]=dict(PC=row['pc'],mnemonic=row['mnemonic'],reason='Physically recovered source undefined-flag output callback',State_offset=offset)
 return out
