"""Finite architectural flag definedness, independent of observed flag values.

Literal Remill representatives remain untouched. Original hardware undefined
bits are projected only while an exact preceding source operation makes them
undefined. A later source definition closes that projection immediately.
"""
BITS={'CF':0,'PF':2,'AF':4,'ZF':6,'SF':7,'DF':10,'OF':11}
ARITH=('CF','PF','AF','ZF','SF','OF')
def count(machine,operand):
    if operand['kind']=='register':return machine.reg(operand['register'])&31
    if operand['kind']=='immediate':return operand['value']&31
    return int.from_bytes(machine.bytes(machine.address(operand),operand['bits']//8),'little')&31
def advance(machine,row,prior):
    out=dict(prior);op=row['mnemonic'];args=row['decoded_operands'];pc=row['pc']
    def defined(names):
        for name in names:out.pop(name,None)
    def undefined(name,why):out[name]=dict(PC=pc,mnemonic=op,reason=why)
    if op in('add','adc','sub','sbb','neg','cmp'):defined(ARITH)
    elif op in('inc','dec'):defined(tuple(n for n in ARITH if n!='CF'))
    elif op in('and','or','xor','test'):
        defined(('CF','PF','ZF','SF','OF'));undefined('AF','logical source instruction has architecturally undefined AF')
    elif op in('shl','shr','sar'):
        n=count(machine,args[1])if len(args)>1 else 1
        if n:
            defined(('PF','ZF','SF'));undefined('AF','nonzero source shift has architecturally undefined AF')
            if n==1:defined(('OF',))
            else:undefined('OF','multi-bit source shift has architecturally undefined OF')
            if n<args[0]['bits']:defined(('CF',))
            else:undefined('CF','source shift count reaches the operand width')
    elif op=='scasb'and(not row.get('repeat')or machine.reg('ecx')):defined(ARITH)
    elif op in('std','cld'):defined(('DF',))
    return out
def mask(domain):return sum(1<<BITS[name]for name in domain)
def project(cpu,domain):
    result=list(cpu);result[8]&=~mask(domain);return result
