"""Source model with a finite typed version-response input, never an AFTER seed."""
import importlib.util
import struct
from consumer import F,M,STATE_REG
from before import stage,SPANS,COLD_PAGE

path=F.pin(F.ROOT/'tools/m4-crt-heap-mode-root/prefix.py',
    '95dd875e421a98c2a286e2cc528c279f97829a045ccb8afc53c0dce59e29d9f1')
spec=importlib.util.spec_from_file_location('heap_version_fixed_prefix',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
FRAGMENT,SOURCE_CALL,SOURCE_RETURN=prior.FRAGMENT,prior.SOURCE_CALL,prior.SOURCE_RETURN
ENTRY,API_CALL,API_SLOT,API_RETURN,RAW_API=prior.ENTRY,prior.API_CALL,prior.API_SLOT,prior.API_RETURN,prior.RAW_API
MODE_CALL,MODE_ENTRY,MODE_RETURN=prior.MODE_CALL,prior.MODE_ENTRY,prior.MODE_RETURN
PROBE_CALL,PROBE_RETURN,PROBE_RET=prior.PROBE_CALL,prior.PROBE_RETURN,prior.PROBE_RET
QUERY_CALL,QUERY_SLOT,QUERY_RETURN,RAW_QUERY=prior.QUERY_CALL,prior.QUERY_SLOT,prior.QUERY_RETURN,prior.RAW_QUERY
QUERY_POINTER,QUERY_FRAME,QUERY_BYTES=0x200017b8,0x20000618,148
ENV_CALL,ENV_SLOT,ENV_RETURN,COLD,SELECTOR_RET=0x78003a5c,0x7802e09c,0x78003a62,0x7800ccc5,0x78003a7f


def source_material(out):
    program,pages,commands=prior.source_material(out)
    provider_path=F.pin(F.ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider=M.N.PE.PEImage(provider_path.read_bytes())
    tool=F.pin(F.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',
        'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    for index,(start,size,_) in enumerate(SPANS):
        decoded,command=M.D.E.decode(tool,provider,provider_path,start,start+size,out,'heap-version-original-source-'+str(index))
        F.require(not set(program).intersection(decoded),'Disjoint original post-query source spans')
        program.update(decoded);commands.append(command)
    pages[COLD_PAGE]=M.D.mapped(provider,COLD_PAGE)
    F.require(program[QUERY_RETURN]==(2,'test',['eax','eax']) and
              program[ENV_CALL]==(6,'call',['dword ptr [0x7802e09c]']) and
              program[SELECTOR_RET]==(1,'ret',[]),'Original version test, environment CALL and selector RET')
    return program,pages,commands


def predict(entry,program,token,response):
    result=prior.predict(entry,program,token)
    phases=result['phases'];phases.pop('heap-create-after')
    state,memory,fx,cpu=result['state'],result['memory'],result['fx'],result['cpu']
    r={name:struct.unpack_from('<I',state,off)[0] for name,off in STATE_REG.items()}
    pc,flags=RAW_QUERY,struct.unpack_from('<I',M.D.cpu(state),32)[0]
    query_input=bytes(memory[0x20001000][0x7b8:0x7b8+QUERY_BYTES])
    F.require(set(response)=={'input','output','result'} and response['input']==query_input and
              isinstance(response['output'],bytes) and len(response['output'])==QUERY_BYTES and
              isinstance(response['result'],int) and 0<=response['result']<=0xffffffff,
              'Finite complete native or explicitly hypothetical API-response input')
    F.require(struct.unpack_from('<I',query_input)[0]==QUERY_BYTES and r['esp']==QUERY_FRAME,
              'Genuine source-initialized query structure and CALL frame')
    def commit():
        for name,off in STATE_REG.items(): struct.pack_into('<I',state,off,r[name])
        struct.pack_into('<I',state,2472,pc)
        for offset,bit in M.F.FLAGS: state[offset]=(flags>>bit)&1
    def snapshot(tag):
        commit();phases[tag]=stage(state,fx,cpu,memory)
    snapshot('heap-version-query-native-before');snapshot('heap-version-query-native-after')
    output_accesses=[]
    for index in range(37):
        address=QUERY_POINTER+index*4;value=struct.unpack_from('<I',response['output'],index*4)[0]
        struct.pack_into('<I',memory[address&~4095],address&4095,value)
        output_accesses.append((QUERY_CALL,address,value,4,1))
    snapshot('heap-version-query-output-after');snapshot('heap-version-query-return-before')
    returned=struct.unpack_from('<I',memory[QUERY_FRAME&~4095],QUERY_FRAME&4095)[0]
    F.require(returned==QUERY_RETURN,'Separate checked genuine version-query return word')
    query_return_access=(QUERY_CALL,QUERY_FRAME,returned,4,0)
    r['eax']=response['result'];r['esp']+=8;pc=returned
    snapshot('heap-version-query-returned')
    result['undefined'].append((QUERY_RETURN,0))
    def read(address):
        F.require(address==ENV_SLOT or 0x20000000<=address<=0x20001ffc,'Bounded source read')
        value=struct.unpack_from('<I',memory[address&~4095],address&4095)[0]
        result['accesses'].append((pc,address,value,4,0));return value
    def write(address,value):
        F.require(0x20000000<=address<=0x20001ffc,'Bounded source stack write')
        struct.pack_into('<I',memory[address&~4095],address&4095,value&0xffffffff)
        result['accesses'].append((pc,address,value&0xffffffff,4,1))
    def subtract(a,b):
        value=(a-b)&0xffffffff
        changed=((a<b)|(((value&255).bit_count()%2==0)<<2)|((((a^b^value)>>4)&1)<<4)|((value==0)<<6)|
            ((value>>31)<<7)|((((a^b)&(a^value))>>31)<<11))
        return (flags&~0x8d5)|changed
    success=False
    for _ in range(24):
        F.require(any(start<=pc<start+size for start,size,_ in SPANS) and pc in program,
                  'Only exact bounded post-query original instructions')
        commit();result['PCs'].append(pc);size,op,args=program[pc];nxt=pc+size
        if op=='test':
            F.require(pc==QUERY_RETURN and args==['eax','eax'],'Exact returned native BOOL TEST')
            value=r['eax'];flags=(flags&~0x8d5)|(((value&255).bit_count()%2==0)<<2)|((value==0)<<6)|((value>>31)<<7)
        elif op in ('je','jne','jae'):
            take=(bool(flags&64)==(op=='je')) if op!='jae' else not bool(flags&1)
            if take: nxt=int(args[0],0)
        elif op=='cmp':
            F.require(pc in (0x78003a35,0x78003a3e),'Exact source version-field comparisons')
            offset=0x88 if pc==0x78003a35 else 0x94
            F.require(args==['dword ptr [ebp - '+hex(offset)+']','0x2' if offset==0x88 else '0x5'],
                      'Recovered version-field operands')
            flags=subtract(read(r['ebp']-offset),2 if offset==0x88 else 5)
        elif op=='lea':
            F.require(pc==0x78003a4b and args==['eax','[ebp - 0x122c]'],'Original environment destination')
            r['eax']=(r['ebp']-0x122c)&0xffffffff
        elif op=='push':
            value=r[args[0]] if args[0] in r else int(args[0],0)&0xffffffff
            write(r['esp']-4,value);r['esp']-=4
        elif op=='pop':
            r[args[0]]=read(r['esp']);r['esp']+=4
        elif op=='jmp': nxt=int(args[0],0)
        elif op=='leave':
            F.require(pc==0x78003a7e,'Genuine selector LEAVE')
            r['esp']=r['ebp'];r['ebp']=read(r['esp']);r['esp']+=4
        elif op=='ret':
            F.require(pc==SELECTOR_RET and r['esp']==0x20001854,'Genuine outer selector return frame')
            target=read(r['esp']);F.require(target==MODE_RETURN,'Original caller return word')
            r['esp']+=4;pc=target;success=True
            snapshot('heap-version-selector-return-after');break
        elif op=='call':
            F.require(pc==ENV_CALL,'Only next genuine environment query CALL')
            target=read(ENV_SLOT);write(r['esp']-4,nxt);r['esp']-=4
            result['routes'].append((pc,target,nxt));pc=target
            snapshot('heap-version-environment-before');break
        else: raise ValueError('Unadmitted post-query opcode '+op)
        pc=nxt
    else: raise ValueError('Bounded selector continuation did not stop')
    snapshot('heap-create-after')
    result.update(state=state,memory=memory,phases=phases,query_input=query_input,query_output=response['output'],
        query_result=response['result'],query_output_accesses=output_accesses,query_return_access=query_return_access,
        selector_returned=success,environment_reached=not success,selector_result=r['eax'] if success else None,
        terminal_EIP=pc,terminal_ESP=r['esp'],fault_PC=SELECTOR_RET if success else ENV_CALL,
        fault_address=MODE_RETURN if success else ENV_SLOT,query_executed=False,query_response_applied=True,
        heap_mode_published=False,initializer_RET=False,heap_initialized=False)
    if success:
        F.require(len(result['PCs'])==51 and len(result['accesses'])==31 and len(result['routes'])==5 and
                  r['eax']==1 and r['esp']==0x20001858,'Complete source selector return without caller publication')
    else:
        F.require(len(result['PCs']) in (46,48,50) and len(result['accesses']) in (29,30,31) and
                  len(result['routes'])==6 and r['esp']==0x20000610,'Bounded alternate environment CALL')
    F.require(len(result['undefined'])==5 and len(output_accesses)==37,'Five exact AF sites and separate37-DWORD API transport')
    return result
