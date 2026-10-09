"""Independent original-provider interpreter and registry ownership checks.

The caller supplies only complete BEFORE State/FX/pages, original decoded rows,
and finite actual API scalar/byte witnesses. It never supplies an AFTER machine.
"""
from pathlib import Path
import copy, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-crt-locale-batch-model-review'))
import interpreter_v2 as I
import batch as B

class Machine(B.OwnedMachine):
    """Adds original SAR; all other instructions use the sealed independent interpreter."""
    def step(self):
        pc=self.cursor
        if pc not in self.program or self.program[pc]['mnemonic']!='sar': return super().step()
        row=self.program[pc]; self.steps+=1
        I.need(self.steps<=1000000,'Finite bounded source execution')
        self.word(2472,pc); self.PCs.append(pc); self.emit('instruction-before',row=row)
        args=row['decoded_operands']; bits=args[0]['bits']; value=self.operand(args[0]); count=self.operand(args[1])&31
        self.cursor=(pc+row['width'])&0xFFFFFFFF
        if count:
            mask=(1<<bits)-1; value &= mask
            signed=value-(1<<bits) if value&(1<<(bits-1)) else value
            result=(signed>>count)&mask
            self.flag('CF', (value>>(count-1))&1 if count<=bits else signed<0)
            self.flag('PF',(result&255).bit_count()%2==0); self.flag('AF',0)
            self.flag('ZF',result==0); self.flag('SF',result>>(bits-1)); self.flag('OF',0)
            self.destination(args[0],result)
        for offset in self.callbacks.get(pc,()):
            self.state[offset]=0; self.undefined.append((pc,offset,0)); self.emit('undefined',pc=pc,offset=offset,value=0)
        self.emit('instruction-after',row=row)

def source_program(path, callbacks=None):
    source=json.loads(Path(path).read_bytes())
    I.need(source['schema']=='mw34-onexit-independent-provider-source-v1' and not source['AFTER_machine_seed'],
           'Original-only fresh provider source interface')
    return {r['pc']:r for r in source['instructions']}, callbacks or {}

def registry_vector(machine, capacity, expected_callbacks):
    """Check source-established begin/next and the exact live ordered vector."""
    begin=int.from_bytes(machine.bytes(0x7803788C,4),'little')
    next_=int.from_bytes(machine.bytes(0x78037888,4),'little')
    I.need(begin and begin<=next_ and (next_-begin)%4==0 and next_-begin<=capacity,
           'Actual source registry bounded ordered begin/next')
    actual=struct.unpack('<'+str((next_-begin)//4)+'I',machine.bytes(begin,next_-begin))
    I.need(actual==tuple(expected_callbacks),'Exact literal callback registration order')
    return dict(begin=begin,next=next_,capacity=capacity,callbacks=actual,
                callback_execution=False)

def verify_reallocation(old, result, capacity, before_bytes, after_bytes, requested, rounded, actual_size):
    """API witness validation without candidate ownership or guard logic."""
    I.need(old['native'] and old['live'] and old['guest'] and capacity>=len(before_bytes),
           'Current privately owned native allocation and measured API capacity')
    I.need(requested==capacity+16 and rounded==(requested+15)&~15 and rounded>capacity,
           'Original msize+16 request followed by source mode1 rounding')
    if not result:
        I.need(after_bytes==before_bytes,'Actual null reallocation retains complete old bytes')
        return dict(native=old['native'],guest=old['guest'],generation=old['generation'],live=True,
                    moved=False,null_preserved=True,capacity=capacity)
    I.need(actual_size>=rounded and len(after_bytes)==actual_size and after_bytes[:len(before_bytes)]==before_bytes,
           'Successful actual heap capacity and complete old-byte preservation')
    return dict(native=result,live=True,moved=result!=old['native'],null_preserved=False,
                capacity=actual_size)
