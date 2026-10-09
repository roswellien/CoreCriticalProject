"""Independent allocation delta from a source-derived initializer return.

The old affine source model is immutable. This module adds only the declared
external research caller/client protocol, finite owned allocation storage, and
the separately recovered source free(NULL) branch. It performs no native/API
execution and never accepts a captured AFTER machine as its expected-state seed.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
MODEL_SHA = '6e0e37da74f17b511713b8b699a6809b703a19ad98d0b1eb3bedf67c95b36b61'
MODEL_PATH = ROOT/'tools/m4-crt-allocation-recovery/model.py'
if hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() != MODEL_SHA:
    raise ValueError('Frozen independent allocation source predictor')
spec = importlib.util.spec_from_file_location('allocation_frozen_source', MODEL_PATH)
source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
need = source.need
ALLOC = 0x31000000
MALLOC_MARKER, FREE_MARKER = 0xffffffe0, 0xffffffd0


def machine(result, phase=None):
    value = result if phase is None else result['phases'][phase]
    return dict(state=bytes(value['state']), fx=bytes(value['fx']), cpu=bytes(value['cpu']),
                memory={base:bytearray(raw) for base,raw in value['memory'].items() if isinstance(base,int)})


def word(value, offset):
    return struct.unpack_from('<I',value['state'],offset)[0]


def owned_store(value, address, number):
    owners = [(base,raw) for base,raw in value['memory'].items()
              if base <= address and address+4 <= base+len(raw)]
    need(len(owners)==1,'One declared external owned DWORD')
    base,raw = owners[0]; struct.pack_into('<I',raw,address-base,number)


def external_call(value, target, argument, marker, writes, projections):
    value = copy.deepcopy(value); state = bytearray(value['state'])
    old_pc,old_sp = word(value,2472),word(value,source.REG['esp'])
    need(old_sp==0x20001860,'Source-cleaned cdecl parent frame')
    frame = old_sp-8
    for address,number in ((frame+4,argument),(frame,marker)):
        owned_store(value,address,number); writes.append((target,address,number,4,1))
    projections.append((1,old_pc,old_sp,target,frame,argument,frame,marker))
    struct.pack_into('<I',state,source.REG['esp'],frame)
    struct.pack_into('<I',state,2472,target); value['state']=bytes(state)
    return value


def external_cleanup(value, projections):
    value=copy.deepcopy(value); state=bytearray(value['state'])
    pc,sp=word(value,2472),word(value,source.REG['esp'])
    need(sp==0x2000185c and pc in (MALLOC_MARKER,FREE_MARKER),'Authentic source export RET before research caller cleanup')
    projections.append((2,pc,sp,pc,sp+4,0,sp-4,0))
    struct.pack_into('<I',state,source.REG['esp'],sp+4);value['state']=bytes(state)
    return value


def free_null(value):
    """Actual normal NULL branch; public void result is the previous FS chain."""
    x=source.Affine(value['state'],value['fx'],value['cpu'],value['memory'])
    F=x.reg('esp'); need(x.word(2472)==0x78001390 and F==0x20001858,'Declared NULL free frame')
    base,off=x.location(F);need(struct.unpack_from('<2I',x.memory[base],off)==(FREE_MARKER,0),'Distinct external NULL argument')
    saved={name:x.reg(name) for name in ('ebp','ebx','esi','edi')}
    base,off=x.location(x.fs);previous=struct.unpack_from('<I',x.memory[base],off)[0]
    x.snapshot('null-free-before')
    x.pc(0x78001390);x.push(0x78001390,saved['ebp'])
    x.pc(0x78001391);x.reg('ebp',x.reg('esp'))
    for pc,number in ((0x78001393,0xffffffff),(0x78001395,0x7802e260),(0x7800139a,0x7800ef03)):
        x.pc(pc);x.push(pc,number)
    x.pc(0x7800139f);x.reg('eax',x.read(0x7800139f,x.fs,previous))
    x.pc(0x780013a5);x.push(0x780013a5,x.reg('eax'))
    x.pc(0x780013a6);x.write(0x780013a6,x.fs,x.reg('esp'));x.snapshot('null-free-SEH-installed')
    x.pc(0x780013ad);x.reg('esp',x.arithmetic(x.reg('esp'),24))
    for pc,name in ((0x780013b0,'ebx'),(0x780013b1,'esi'),(0x780013b2,'edi')):
        x.pc(pc);x.push(pc,saved[name])
    x.pc(0x780013b3);x.reg('esi',x.read(0x780013b3,F+4,0))
    x.pc(0x780013b6);x.logic(0x780013b6,0);x.pc(0x780013b8)
    x.pc(0x78001416);x.reg('ecx',x.read(0x78001416,F-20,previous))
    x.pc(0x78001419);x.write(0x78001419,x.fs,x.reg('ecx'));x.snapshot('null-free-SEH-restored')
    for pc,name in ((0x78001420,'edi'),(0x78001421,'esi'),(0x78001422,'ebx')):
        x.pc(pc);x.pop(pc,name)
    x.pc(0x78001423);x.reg('esp',x.reg('ebp'));x.pop(0x78001423,'ebp')
    x.pc(0x78001424);x.ret(0x78001424,FREE_MARKER);x.snapshot('null-free-returned')
    need(len(x.PCs)==22 and len(x.accesses)==18 and not x.API_reads and not x.routes and len(x.returns)==1,
         'Independent NULL branch22PC18access0API1RET')
    need(x.reg('eax')==previous and x.reg('ecx')==previous and x.reg('esp')==F+4 and
         all(x.reg(name)==number for name,number in saved.items()),'NULL free restores its source SEH/nonvolatiles; no Boolean return claim')
    result=x.result();result.update(previous_SEH=previous,public_CRT_return_type='void',actual_API_executed=False)
    return result


def predict(initializer, requested_size, native_initial, raw_free_BOOL):
    """Ordinary live allocation/free chain. Actual finite OS outputs are inputs.

    initializer must come from the pinned earlier BEFORE/source predictor and
    measured finite create/query outputs. native_initial contains exactly the
    measured rounded allocation extent. Padding to a page is declared storage.
    """
    need(initializer.get('initializer_RET') is True and initializer.get('heap_mode_value')==1,
         'Source-computed qualifying mode1 genuine initializer RET')
    need(0<=requested_size<=4096 and 0<raw_free_BOOL<=0xffffffff,'Actual functional bounded request/successful release witness')
    extent=(max(requested_size,1)+15)&0xfffffff0
    need(len(native_initial)==extent,'Complete finite actual native allocation bytes; no fabricated zero result')
    current=machine(initializer);need(len([raw for raw in current['memory'].values() if len(raw)==4096])==21 and ALLOC not in current['memory'],'Twenty-one carried whole pages plus distinct exact owned semantic extents; no allocation yet')
    phases={'allocation-caller-before':copy.deepcopy(current)};counts={'allocation-caller-before':(35,2)}
    writes,projections=[],[]
    caller=source.caller_cleanup(**current);current=machine(caller)
    phases['allocation-caller-after']=copy.deepcopy(current);counts['allocation-caller-after']=(36,2)
    current=external_call(current,0x780012b3,requested_size,MALLOC_MARKER,writes,projections)
    malloc=source.malloc_mode1(**current,size=requested_size,guest_result=ALLOC)
    backing=bytes(native_initial)+bytes(4096-extent)
    def snapshot(tag,value,accesses,API_reads,allocation=None):
        value=machine(value) if 'state' in value else value
        if allocation is None:value['memory'].pop(ALLOC,None)
        else:value['memory'][ALLOC]=bytearray(allocation)
        phases[tag]=value;counts[tag]=(accesses,API_reads)
    def malloc_phase(tag,source_tag,mapped=False):
        value=malloc['phases'][source_tag]
        snapshot(tag,value,36+value['source_accesses'],2+value['API_reads'],backing if mapped else None)
    malloc_phase('allocation-malloc-before','malloc-before')
    malloc_phase('allocation-malloc-seh-installed','malloc-SEH-installed')
    for tag in ('allocation-native-before','allocation-native-after'):
        malloc_phase(tag,'malloc-HeapAlloc-before')
    for tag in ('allocation-backing-published','allocation-api-return-before'):
        malloc_phase(tag,'malloc-HeapAlloc-before',True)
    malloc_phase('allocation-api-returned','malloc-HeapAlloc-returned',True)
    malloc_phase('allocation-malloc-seh-restored','malloc-SEH-restored',True)
    malloc_phase('allocation-malloc-returned','malloc-returned',True)
    current=machine(malloc);current['memory'][ALLOC]=bytearray(backing)
    snapshot('allocation-client-before',current,36+len(malloc['accesses']),3,backing)
    pattern=bytes(((i*37+requested_size*11+0x5a)&255) for i in range(extent))
    backing=pattern+bytes(4096-extent);current['memory'][ALLOC]=bytearray(backing)
    snapshot('allocation-client-after',current,36+len(malloc['accesses']),3,backing)
    current=external_cleanup(current,projections)
    current=external_call(current,0x78001390,ALLOC,FREE_MARKER,writes,projections)
    free=source.free_mode1(**current,guest_pointer=ALLOC,BOOL=raw_free_BOOL)
    offset=36+len(malloc['accesses'])
    def free_phase(tag,source_tag,mapped=False):
        value=free['phases'][source_tag]
        snapshot(tag,value,offset+value['source_accesses'],3+value['API_reads'],backing if mapped else None)
    free_phase('allocation-free-before','free-before',True)
    free_phase('allocation-free-seh-installed','free-SEH-installed',True)
    free_phase('allocation-free-native-before','free-HeapFree-before',True)
    free_phase('allocation-free-native-after','free-HeapFree-before')
    free_phase('allocation-free-api-returned','free-HeapFree-returned')
    free_phase('allocation-free-seh-restored','free-SEH-restored')
    free_phase('allocation-free-returned','free-returned')
    current=machine(free);current['memory'].pop(ALLOC,None)
    current=external_cleanup(current,projections)
    current=external_call(current,0x78001390,0,FREE_MARKER,writes,projections)
    null=free_null(current);offset+=len(free['accesses'])
    for tag,source_tag in (('allocation-null-free-before','null-free-before'),
                           ('allocation-null-free-seh-installed','null-free-SEH-installed'),
                           ('allocation-null-free-seh-restored','null-free-SEH-restored'),
                           ('allocation-null-free-returned','null-free-returned'),
                           ('allocation-batch-complete','null-free-returned')):
        value=null['phases'][source_tag];snapshot(tag,value,offset+value['source_accesses'],4)
    terminal=machine(null)
    for tag in ('heap-create-after','entry-after-fault','retry-after'):
        snapshot(tag,terminal,offset+len(null['accesses']),4)
    accesses=list(initializer['accesses'])+caller['accesses']+malloc['accesses']+free['accesses']+null['accesses']
    PCs=list(initializer['PCs'])+caller['PCs']+malloc['PCs']+free['PCs']+null['PCs']
    routes=list(malloc['routes'])+free['routes'];returns=list(malloc['returns'])+free['returns']+null['returns']
    need(len(accesses)==118+(2 if requested_size==0 else 0) and len(PCs)==166+(2 if requested_size==0 else 0),
         'Whole admitted source prefix and actual allocation/free/NULL path counts')
    need(len(writes)==6 and len(projections)==5 and len(routes)==4 and len(returns)==5,
         'External protocol separate from genuine allocator4CALL5RET delta')
    need(word(terminal,source.REG['eax'])==null['previous_SEH'],'Source NULL free void result retains previous FS0')
    return dict(phases=phases,counts=counts,terminal=terminal,caller=caller,malloc=malloc,free=free,null=null,
                PCs=PCs,accesses=accesses,API_reads=malloc['API_return_reads']+free['API_return_reads'],
                external_accesses=writes,external_projections=projections,extent=extent,pattern=pattern,
                native_initial=bytes(native_initial),allocation_padding_declared=True,
                AFTER_machine_state_used_as_seed=False,original_API_internals_equivalence=False,
                normal_SEH_handler_dispatch_proved=False)
