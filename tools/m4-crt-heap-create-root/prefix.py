"""Independent source continuation after a declared real HeapCreate outcome."""
import importlib.util
import struct
import types
from consumer import F, M, STATE_REG
from before import stage, PAGE

path = F.pin(F.ROOT/'tools/m4-crt-heap-init-root/prefix.py',
    'd5d6f4357adb7033667ecc014168ba49fbc2041fd41e9216012eae7a9087d9a1')
spec = importlib.util.spec_from_file_location('heap_create_frozen_prefix', path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
FRAGMENT, SOURCE_CALL, SOURCE_RETURN = prior.FRAGMENT, prior.SOURCE_CALL, prior.SOURCE_RETURN
ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API = prior.ENTRY, prior.API_CALL, prior.API_SLOT, prior.API_RETURN, prior.RAW_API
MODE_CALL, MODE_ENTRY, MODE_RETURN = 0x780039e3, 0x78003a0c, 0x780039e8
CONTINUATION = (API_RETURN, 0x780039d8, 0x780039dd, MODE_CALL)
first_prefix = types.FunctionType(prior.predict.__code__,dict(prior.predict.__globals__, stage=stage),
                                 argdefs=prior.predict.__defaults__)


def source_material(out):
    program, raw, commands = prior.source_material(out)
    provider = M.N.PE.PEImage(F.pin(F.ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
    F.require(program[API_RETURN] == (2,'test',['eax','eax']) and
        program[0x780039d8] == (5,'mov',['dword ptr [0x78035000]','eax']) and
        program[0x780039dd] == (6,'je',['0x7800cddc']) and
        program[MODE_CALL] == (5,'call',['0x78003a0c']), 'Exact original post-API source continuation')
    return program, {0x78003000:raw, PAGE:M.D.mapped(provider,PAGE)}, commands


def predict(entry, program, token):
    F.require(isinstance(token,int) and not isinstance(token,bool) and 0 < token <= 0xffffffff,
              'Declared nonzero opaque guest token from verified actual API ownership witness')
    result = first_prefix(entry,program)
    state, memory, fx, cpu = result['state'], result['memory'], result['fx'], result['cpu']
    phases = result['phases']
    phases.pop('heap-after')
    phases = {name.replace('heap-','heap-create-',1):files for name,files in phases.items()}
    r = {name:struct.unpack_from('<I',state,off)[0] for name,off in STATE_REG.items()}
    pc = struct.unpack_from('<I',state,2472)[0]
    F.require(pc == RAW_API and r['esp'] == 0x20001848 and r['eax'] == 0,
              'Authentic generated HeapCreate CALL State')
    F.require(struct.unpack_from('<I',state,2184)[0] == 0,
              'Original flat source DS base')
    frame = r['esp']
    returned = struct.unpack_from('<I',memory[frame&~4095],frame&4095)[0]
    F.require(returned == API_RETURN, 'Checked API stdcall return word')
    phases['heap-create-api-return-before'] = stage(state,fx,cpu,memory)
    result['API_return_access'] = (API_CALL,frame,returned,4,0)
    # This is a declared guest API ABI model, not execution of the old x86
    # Windows API implementation. All carried guest bytes except EAX/ESP/EIP
    # remain preserved. The following source TEST defines its own flags.
    r['eax'],r['esp'],pc = token, frame+16, returned
    flags = struct.unpack_from('<I',M.D.cpu(state),32)[0]

    def commit():
        for name,off in STATE_REG.items():
            struct.pack_into('<I',state,off,r[name])
        struct.pack_into('<I',state,2472,pc)
        for offset,bit in M.F.FLAGS:
            state[offset]=(flags>>bit)&1

    def snapshot(name):
        commit()
        phases[name]=stage(state,fx,cpu,memory)

    def write(address,value):
        F.require(address == PAGE or 0x20001000 <= address <= 0x20001ffc,
                  'Exact source heap-global or owned CALL-stack store')
        struct.pack_into('<I',memory[address&~4095],address&4095,value)
        result['accesses'].append((pc,address,value,4,1))

    snapshot('heap-create-api-returned')
    for wanted in CONTINUATION:
        F.require(pc == wanted,'Exact post-API source PC order')
        commit()
        result['PCs'].append(pc)
        size,op,operands = program[pc]
        nxt = pc+size
        if op == 'test':
            F.require(operands == ['eax','eax'],'Exact source returned-handle TEST')
            flags = (flags&~0x8d5)|(((token&255).bit_count()%2 == 0)<<2)|((token>>31)<<7)
            result['undefined'].append((pc,0))
        elif op == 'mov':
            F.require(operands == ['dword ptr [0x78035000]','eax'],'Source-only handle publication')
            write(PAGE,r['eax'])
            snapshot('heap-create-published')
        elif op == 'je':
            F.require(not(flags&0x40),'Actual nonzero guest handle success branch')
        elif op == 'call':
            target = int(operands[0],0)
            write(r['esp']-4,nxt)
            r['esp']-=4
            result['routes'].append((pc,target,nxt))
            pc = target
            F.require(pc == MODE_ENTRY and r['esp'] == 0x20001854,'Genuine heap-mode selector CALL frame')
            snapshot('heap-create-mode-before')
            snapshot('heap-create-after')
            result.update(state=state,memory=memory,phases=phases,mode_frame=r['esp'],
                token=token,fault_PC=MODE_CALL,fault_address=MODE_ENTRY,API_executed=True,
                guest_heap_handle_published=True,heap_initialized=False)
            F.require(len(result['PCs']) == 13 and len(result['accesses']) == 10 and
                      len(result['routes']) == 3 and len(result['undefined']) == 2,
                      'Complete bounded real-API source continuation')
            return result
        else:
            raise ValueError('Unadmitted post-API source opcode '+op)
        pc=nxt
    raise ValueError('Source continuation failed to reach mode-selector boundary')
