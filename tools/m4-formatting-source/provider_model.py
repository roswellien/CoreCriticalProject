"""Literal bounded formatter provider; consumes explicit BEFORE memory only.

Default %s%s is the intended domain, but executed source paths and all inputs
are independently checked by a caller. There are no host string/printf calls
and no predicted output allocation. Unknown external helpers remain denied.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('format_base_source',R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py')
I=importlib.util.module_from_spec(sp);sp.loader.exec_module(I)
REC=R/'reports/m4-formatting-source/provider-recovery-r2'
REC_SHA='2aa9a712983ab98a08c3f59adf8e29b24c17f1f8c0d41ebb786a55c7241a13b9'

def source_program():
    raw=(REC/'report.json').read_bytes();I.need(hashlib.sha256(raw).hexdigest()==REC_SHA,'Frozen provider physical recovery')
    receipt=json.loads(raw);raw=Path(receipt['instructions']).read_bytes()
    I.need(hashlib.sha256(raw).hexdigest()==receipt['instructions_sha256'],'Frozen literal provider instructions')
    rows=json.loads(raw)['instructions'];return {r['pc']:r for r in rows},{}

class Machine(I.Machine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.string_iterations=[];self.output_dispatches=[]
        self.initial_EFLAGS=struct.unpack_from('<I',self.cpu,32)[0]

    def projected_cpu(self):
        flags=self.initial_EFLAGS
        for name,bit in (('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):
            flags=(flags&~(1<<bit))|(int(bool(self.flag(name)))<<bit)
        return tuple(self.reg(k) for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)

    def condition(self,op):
        if op=='js':return bool(self.flag('SF'))
        if op=='jns':return not self.flag('SF')
        return super().condition(op)

    def step(self):
        pc=self.cursor;row=self.program.get(pc);I.need(row is not None,'Literal provider PC, no external formatter fallback')
        if pc==0x7800fcef:
            index=self.reg('eax');I.need(index<=7,'Literal _output EAX bounds before eight-way source table')
            table=0x780103fa+4*index;target=int.from_bytes(self.bytes(table,4),'little')
            self.output_dispatches.append(dict(PC=pc,index=index,table_read=table,target=target,source_access_index=len(self.accesses),steps=self.steps))
        op=row['mnemonic']
        if op not in ('scasb','std','cld','not','movsx','sar'):return super().step()
        self.steps+=1;I.need(self.steps<=1000000,'Finite literal provider instruction budget')
        self.word(2472,pc);self.PCs.append(pc);self.emit('instruction-before',row=row)
        args=row['decoded_operands'];self.cursor=(pc+row['width'])&0xffffffff
        if op in ('std','cld'):self.flag('DF',op=='std')
        elif op=='not':self.destination(args[0],~self.operand(args[0]))
        elif op=='movsx':
            width=args[1]['bits'];value=self.operand(args[1]);sign=1<<(width-1)
            self.destination(args[0],value-(1<<width) if value&sign else value)
        elif op=='sar':
            bits=args[0]['bits'];value=self.operand(args[0]);count=self.operand(args[1])&31
            if count:
                value&=(1<<bits)-1;signed=value-(1<<bits) if value&(1<<(bits-1)) else value
                result=(signed>>count)&((1<<bits)-1)
                self.flag('CF',(value>>(count-1))&1 if count<=bits else signed<0)
                self.flag('PF',(result&255).bit_count()%2==0);self.flag('AF',0)
                self.flag('ZF',result==0);self.flag('SF',result>>(bits-1));self.flag('OF',0)
                self.destination(args[0],result)
        else:
            repeat=row.get('repeat');I.need(repeat in (None,'repne','repnz'),'Only exact selected SCASB repeat contract')
            incoming=self.reg('ecx');direction=self.flag('DF')
            if not repeat or incoming:
                address=(self.word(I.BASE['es'])+self.reg('edi'))&0xffffffff
                byte=self.read(address,1);self.arith(self.reg('al'),byte,8,sub=True)
                self.reg('edi',self.reg('edi')+(-1 if direction else 1))
                if repeat:self.reg('ecx',incoming-1)
                continuing=bool(repeat and self.reg('ecx') and not self.flag('ZF'))
                if continuing:self.cursor=pc
                self.string_iterations.append(dict(PC=pc,address=address,value=byte,AL=self.reg('al'),DF=direction,ECX_before=incoming,ECX_after=self.reg('ecx'),ZF=self.flag('ZF'),continued=continuing,source_access_index=len(self.accesses)-1))
                I.need(len(self.string_iterations)<=262144,'Bounded actual readable REP stream')
        for offset in self.callbacks.get(pc,()):
            self.state[offset]=0;self.undefined.append((pc,offset,0));self.emit('undefined',pc=pc,offset=offset,value=0)
        self.emit('instruction-after',row=row)

def from_boundary(boundary,memory,hook=None):
    """Construct only provider architecture from genuine cdecl entry metadata.

    Complete source memory must come from BEFORE or measured initial allocation
    backings. This function never imports any candidate/original AFTER bytes.
    """
    cpu=boundary['cpu'];I.need(len(cpu)==10,'Complete actual cdecl CPU40 input')
    state=bytearray(3504)
    for name,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,I.REG[name],value)
    for name,bit in (('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[I.FLAGS[name]]=(cpu[8]>>bit)&1
    struct.pack_into('<I',state,2472,cpu[9]);program,callbacks=source_program()
    machine=Machine(state,bytes.fromhex(boundary['FX512_hex']),struct.pack('<10I',*cpu),memory,program=program,callbacks=callbacks,hook=hook)
    machine.call_stack.append((cpu[9],cpu[4],int.from_bytes(machine.bytes(cpu[4],4),'little'),boundary['CALL_pc'],cpu[5],cpu[3],cpu[6],cpu[7],0))
    return machine
