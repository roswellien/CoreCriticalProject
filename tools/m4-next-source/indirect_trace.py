"""Observation-only literal indirect prefix tracing for finite120 proofs."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'reports/m4-next-source/recovery-r1/indirect-call-inputs.json'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='a329e3988a4d77137e1270d9606c2c65f8b6aee95d1f04fb5928eb9a28a90d9a'
INPUTS={(r['root'],r['CALL_pc']):r for r in json.loads(P.read_bytes())}
RET={0x40e820:0x40e827,0x59ff00:0x59ff0d,0x59ff80:0x59ffa1}

def configure(machine,projector,context):
    machine.indirect_projector=projector
    machine.indirect_context=dict(context)
    machine.indirect_derivations=[]
    machine.indirect_pending=[]

def snapshot(machine,pc):
    cpu=list(machine.projected_cpu());cpu[9]=pc
    fx,env=machine.indirect_projector(machine)
    return dict(CPU=cpu,State_hex=bytes(machine.state).hex(),FX_hex=fx.hex(),ENV_hex=env.hex(),
                ESP=cpu[4],frame_hex=machine.bytes(cpu[4],16).hex(),
                FS0=int.from_bytes(machine.bytes(0x7ffde000,4),'little'))

def before_step(machine):
    if not hasattr(machine,'indirect_pending'):return
    pc=machine.cursor
    root=machine.call_stack[0][0] if machine.call_stack else 0
    item=INPUTS.get((root,pc))
    if item:
        machine.I.need(not machine.indirect_pending,'No nested admitted indirect helper') if hasattr(machine,'I') else None
        assert not machine.indirect_pending,'No nested admitted indirect helper'
        assert machine.reg('ecx')==item['entry_ECX'],'Source-derived exact helper ECX'
        assert machine.bytes(item['slot'],4)==struct.pack('<I',item['target']),'Exact raw physical cell persists'
        if item['argument'] is not None:assert machine.bytes(machine.reg('esp'),4)==struct.pack('<I',item['argument'])
        local=list(machine.accesses)
        dominating=None
        if 'source_vtable' in item:
            writes=[(i,r) for i,r in enumerate(local) if r[0]==item['dominating_vtable_store_PC'] and r[1]==item['source_object'] and r[3:]==(4,1)]
            assert len(writes)==1 and writes[0][1][2]==item['source_vtable'],'One genuine dominating source vptr publication'
            dominating=dict(source_access_index=writes[0][0],access=list(writes[0][1]))
        row=dict(machine.indirect_context,root=root,CALL_pc=pc,slot=item['slot'],target=item['target'],
                 return_pc=item['return_pc'],argument=item['argument'],RET_cleanup=item['RET_cleanup'],
                 call_BEFORE=snapshot(machine,pc),dominating_vptr_store=dominating,
                 source_access_start=len(machine.accesses),PC_start=len(machine.PCs))
        machine.indirect_pending.append(row)
    elif machine.indirect_pending:
        row=machine.indirect_pending[-1]
        if pc==RET[row['target']]:
            row['RET_pc']=pc;row['RET_BEFORE']=snapshot(machine,pc)

def after_step(machine):
    if not getattr(machine,'indirect_pending',None):return
    row=machine.indirect_pending[-1]
    pc=machine.PCs[-1]
    if pc==row['CALL_pc']:
        assert machine.cursor==row['target'],'Genuine source CALL delivered exact literal target'
        row['ENTRY_BEFORE']=snapshot(machine,machine.cursor)
        row['actual_source_CALL_frame']=list(machine.call_stack[-1])
        assert int.from_bytes(machine.bytes(machine.reg('esp'),4),'little')==row['return_pc']
    if pc==RET[row['target']]:
        assert machine.cursor==row['return_pc'],'Physical literal helper RET to genuine caller'
        row['RET_AFTER']=snapshot(machine,row['return_pc'])
        assert row['RET_AFTER']['ESP']==row['ENTRY_BEFORE']['ESP']+4+row['RET_cleanup']
        row['source_access_end']=len(machine.accesses)
        row['actual_prefix_PCs']=list(machine.PCs[row['PC_start']:])
        row['source_accesses']=[list(x) for x in machine.accesses[row['source_access_start']:]]
        row['nonzero_pointer_path_admitted']=False
        if row['target']==0x59ff80:
            assert row['actual_prefix_PCs']==[0x59ff6e,0x59ff80,0x59ff84,0x59ff86,0x59ffa1]
            assert not any(0x59ff88<=x[0]<=0x59ff9e for x in row['source_accesses']),'No unadmitted pointee read/copy'
        if row['target']==0x59ff00:
            assert row['actual_prefix_PCs']==[0x59fdc5,0x59ff00,0x59ff05,0x59ff08,0x59ff0a,0x59ff0d]
            object_=INPUTS[(row['root'],row['CALL_pc'])]['entry_ECX']
            g=[x for x in row['source_accesses'] if x[0]==0x59ff00 and x[1]==0x5f49b8 and x[3:]==[4,0]]
            r=[x for x in row['source_accesses'] if x[0]==0x59ff05 and x[1]==object_+12 and x[3:]==[4,0]]
            w=[x for x in row['source_accesses'] if x[0]==0x59ff0a and x[1]==object_+12 and x[3:]==[4,1]]
            assert len(g)==len(r)==len(w)==1 and w[0][2]==(g[0][2]|r[0][2]),'Literal arbitrary-DWORD OR prefix byteflow'
        machine.indirect_pending.pop();machine.indirect_derivations.append(row)
