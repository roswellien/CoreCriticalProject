"""Independent bounded numeric observations/byteflow review, no target writer."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,struct,sys,traceback
R=Path(__file__).resolve().parents[2];A=R/'reports/m4-hypot-native'
PINS={};COUNTS=Counter()
E='320e147d0f0836e71f9c5341386400c691eff24c55fd4d9d719a80092491b099'
C='3aa19148ad564700afcc84b459ad8aa8f9c6b7034063396db09ddf6f1a93d863'
SRET=0x410a80;NRET=0xfffffff0;FRAME=0x20001800;STACK=0x20001000
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.iso'),'No archive or ISO reader')
    a=sha(p);need(h is None or h==a,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable input');PINS[str(p)]=a;return p
def blob(p):return pin(p).read_bytes()
def load(p,h=None):return json.loads(pin(p,h).read_bytes())
def words(b,at=0,n=10):return struct.unpack_from('<'+'I'*n,b,at)
def projected(b,base):
    at=FRAME-base
    if not 0<=at<=len(b)-4:return b
    need(words(b,at,1)[0]==SRET,'Only exact captured source caller return')
    b=bytearray(b);struct.pack_into('<I',b,at,NRET);return bytes(b)
def initial(cpu,fx):
    state=bytearray(3504)
    regs=((2216,0),(2248,1),(2264,2),(2232,3),(2312,4),(2328,5),(2280,6),(2296,7),(2472,9))
    for at,index in regs:struct.pack_into('<I',state,at,cpu[index])
    struct.pack_into('<Q',state,2080,cpu[8])
    for at,bit in ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)):state[at]=(cpu[8]>>bit)&1
    for at,selector in ((2090,0x2b),(2106,0x2b),(2110,0x23)):struct.pack_into('<H',state,at,selector)
    state[2768:3280]=fx
    return bytes(state)

def main(name):
    out=R/'reports/m4-tree-review'/name
    need(re.fullmatch('hypot-actual-comparison-r[1-9][0-9]*',name)and not out.exists(),'Fresh independent output')
    out.mkdir();passed=False;cases=[]
    try:
        report=load(A/'fixture-comparison-r1/report.json',C)
        execution=load(report['execution'],E)
        prelaunch=load(execution['review'],execution['review_sha256'])
        build=load(execution['build'],execution['build_sha256'])
        prep=load(build['preparation'],build['preparation_sha256'])
        inputs=load(prep['inputs'],prep['inputs_sha256'])
        trace_path=R/'reports/m4-hypot-original/trace-validation-r2/report.json'
        trace=load(trace_path,'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')
        trace_review=load(R/'reports/m4-tree-review/hypot-trace-actual-r1/report.json','92c18c03c0b24c9f4c8aeccea8c4efbdcfea8c864e744415c09b70605a3e2421')
        for receipt in(report,execution,prelaunch,build,prep,inputs,trace,trace_review):
            need(receipt['passed'],'Passed exact measured input gate')
            for key in('files','artifacts'):
                for path,digest in receipt.get(key,{}).items():
                    if Path(path).suffix.lower()not in('.mwb','.zip'):pin(path,digest)
        need(execution['all_processes_closed']and trace['reader_closed']and not execution['source_after_seed']and not execution['numerical_expected_seed'],'Actual closed BEFORE-only writer/trace')
        need(execution['review_sha256']=='abcac29a4df6e80ee18453f717bfaa2cfd3f86f8efd06abdbc6fba5322661a96'and build['preparation_sha256']=='d237d05453b2ba32a6b70678f057340a32b78ad2e839c7c3bff4815bf5e69993','Exact current coupled build')
        need(report['caller_projection']==dict(address=FRAME,source_RETURN=SRET,native_RETURN=NRET,bytes=4,source_root_RET_PC=0x4b593e),'Only exact root caller adapter')
        for key in('source_AFTER_seed','numerical_expected_seed','independent_numeric_prediction','source_native_whole_State_equivalence','cold_source_domain_admitted'):
            need(report[key]is False,'Explicit uncredited scope '+key)
        need(report['initializer_credit']==0,'No initializer acceptance')
        source=load(trace_path.parent/'actual-source-traces.json');operands=load(trace_path.parent/'actual-source-accesses.json')
        need(len(source)==6 and len(operands)==3696,'Whole genuine source observation inventory')
        seeds=blob(Path(prep['inputs']).parent/'input-state.bin');need(len(seeds)==3480,'Six complete CPU/FX/ENV BEFORE inputs')
        need({(x['level'],x['sequence'])for x in execution['runs']}=={(level,i)for level in('O0','O2')for i in range(6)}and len(execution['runs'])==12,'Exact12 actual independent processes')
        cross={}
        for run in execution['runs']:
            need(run['complete']and run['exit_code']==0 and run['process_closed'],'Actual complete process')
            seq=run['sequence'];level=run['level'];folder=Path(run['output']);t=source[seq]
            rows=[x for x in operands if x['sequence']==seq]
            need(t['sequence']==seq and t['event_count']==1007 and len(rows)==616 and len(t['APIs'])==2,'Exact finite measured source schedule')
            need(words(blob(folder/'schema.bin'),0,10)==(44,15360,616,2,3504,40,190,2,80,80),'Physical native record ABI')
            need(blob(folder/'COMPLETE.txt')==b'complete','Actual completion marker')
            seed=seeds[seq*580:(seq+1)*580];cpu=blob(folder/'before/CPU.bin');need(cpu==seed[:40]==struct.pack('<10I',*t['own_BEFORE_CPU']),'Complete authentic entry CPU')
            need(seed[40:552].hex()==t['own_BEFORE_FX512_hex']and seed[552:].hex()==t['own_BEFORE_ENV28_hex'],'Complete authentic FX/ENV inputs')
            state_before=blob(folder/'before/State.bin');state_after=blob(folder/'after/State.bin')
            need(state_before==initial(words(cpu),seed[40:552])and len(state_after)==3504,'Independent complete initial State layout reconstruction')
            expected_after=list(t['own_AFTER_CPU']);need(expected_after[-1]==SRET,'True original source RET')
            expected_after[-1]=NRET;need(blob(folder/'after/CPU.bin')==struct.pack('<10I',*expected_after),'Complete source CPU return with precise Runtime caller')
            COUNTS['whole_initial_State3504_relations']+=1;COUNTS['whole_root_CPU40_relations']+=2
            cross[level,seq]=(state_before,state_after)
            packed=blob(inputs['cases'][seq]['pack']);need(packed[:8]==b'MW4J124P'and len(packed)==12+190*4104 and words(packed,8,1)[0]==190,'Complete current coupled pack')
            memory={};before={}
            for i in range(190):
                address,right=words(packed,12+i*4104,2);need(address not in memory and address%4096==0 and right in(0,1,2),'One exact finite typed page')
                expected=projected(packed[20+i*4104:12+(i+1)*4104],address)
                observed=blob(folder/f'before/pages/{address}.bin');need(len(observed)==4096 and observed==expected,'Whole current BEFORE page and only caller projection')
                memory[address]=bytearray(observed);before[address]=observed;COUNTS['whole_BEFORE_page4096_relations']+=1
            ledger=blob(folder/'accesses.bin');need(len(ledger)==616*44,'Complete actual native access ledger')
            returns=0;publications=[]
            for i,row in enumerate(rows):
                pc,address,width,writing=words(ledger,44*i,4)
                need((pc,address,width,writing)==(row['PC'],row['address'],row['width'],row['write']),'Exact occurrence/PC/address/width/direction')
                need(0<width<=28 and bool(row['read'])!=bool(row['write']),'Measured unique source direction')
                value=bytes.fromhex(row['after_hex']if writing else row['before_hex'])
                if i==615:
                    need((pc,address,width,writing)==(0x4b593e,FRAME,4,0)and value==struct.pack('<I',SRET),'Exact final source RET operand')
                    value=struct.pack('<I',NRET);returns+=1
                need(ledger[i*44+16:i*44+16+width]==value and ledger[i*44+16+width:(i+1)*44]==bytes(28-width),'Whole actual observed payload and no unused buffer ambiguity')
                page=address&~4095;offset=address&4095
                need(page in memory and offset+width<=4096,'Whole finite source operand backing')
                if writing:
                    memory[page][offset:offset+width]=value
                    if width==4 and 0x60b2c8<=address<=0x60b2e8:publications.append((address,value))
                else:need(bytes(memory[page][offset:offset+width])==value,'Own complete BEFORE plus dominating genuine source-write history')
                COUNTS['whole_observed_operand_payload_relations']+=1
            need(returns==1 and [x[0]for x in publications]==list(range(0x60b2c8,0x60b2ec,4)),'Exact caller adapter and nine actual game publications')
            COUNTS['precise_caller_RET4_projections']+=1;COUNTS['actual_game_F32_publications']+=9
            for address,data in memory.items():need(blob(folder/f'after/pages/{address}.bin')==data,'Whole AFTER from own BEFORE plus complete observed source-write sequence');COUNTS['whole_AFTER_page4096_byteflow_relations']+=1
            api=blob(folder/'APIs.bin');need(len(api)==30720,'Two complete actual native cdecl intervals')
            raw80s=[]
            for index,original in enumerate(t['APIs']):
                off=index*15360
                need(original['index']==index and original['import_name']=='_hypot'and original['owning_IAT']==0x5bb5b0 and original['target']==0x7802a122 and original['argc']==4 and original['returned']==1,'Genuine exact named cdecl interval')
                need(words(api,off,3)==(index,original['ENTRY_CPU'][4],original['return_PC']),'Actual current call occurrence/frame/return')
                frame=original['ENTRY_CPU'][4]
                for label,cpu_offset,stack_offset,frame_offset in(('entry',7024,7168,7104),('returned',7064,11264,7136)):
                    orig_cpu=original['ENTRY_CPU'if label=='entry'else'AFTER_CPU']
                    need(api[off+cpu_offset:off+cpu_offset+40]==struct.pack('<10I',*orig_cpu),'Whole40 actual API source CPU')
                    stack=api[off+stack_offset:off+stack_offset+4096]
                    need(stack==projected(bytes.fromhex(original[label+'_whole_stack_hex']),STACK),'Whole4096 API stack equality with only exact root return')
                    at=orig_cpu[4]-STACK;expected=projected(bytes.fromhex(original[label+'_frame64_hex']),orig_cpu[4])
                    need(len(expected)==64 and stack[at:at+64]==expected,'Whole64 current source API frame')
                    need(api[off+frame_offset:off+frame_offset+32]==stack[frame-STACK:frame-STACK+32],'Whole32 native fixed-CALL-frame capture join')
                    COUNTS['whole_API_CPU40_relations']+=1;COUNTS['whole_API_stack4096_relations']+=1;COUNTS['whole_API_frame64_relations']+=1;COUNTS['native_API_frame32_stack_joins']+=1
                need(api[off+7108:off+7124].hex()==original['actual_F64_arguments_hex'],'Exact two actual F64 arguments')
                raw80=api[off+3520+2486:off+3520+2496]
                need(raw80.hex()==original['actual_return_raw80_hex'],'All ten actual numerical return bytes, no prediction')
                raw80s.append(raw80.hex());COUNTS['actual_raw80_return_relations']+=1;COUNTS['actual_literal_cdecl_intervals']+=1
            for kind,size in(('FX',512),('ENV',28)):
                old=blob(folder/f'host-before-{kind}.bin');now=blob(folder/f'host-after-{kind}.bin')
                need(len(old)==size and old==now,'Actual whole outside-caller hardware restoration')
                COUNTS[f'whole_caller_{kind}{size}_restorations']+=1
            cases.append(dict(level=level,sequence=seq,whole_final_State_sha256=hashlib.sha256(state_after).hexdigest(),actual_return_raw80_hex=raw80s,actual_F32_publication_hex=[v.hex()for _,v in publications],whole_pages=190))
        for seq in range(6):need(cross['O0',seq]==cross['O2',seq],'Both actual whole before/after State images agree');COUNTS['whole_State3504_cross_level_pairs']+=2
        need(dict(COUNTS)==report['counts'],'All actual independently reconstructed count extents')
        code=pin(R/'tools/m4-hypot-native/compare_fixture.py').read_text()
        need('Expected numeric bytes enter only this post-execution verifier'in code and 'memory_write(address,observed)'in code and "source_native_whole_State_equivalence=False"in code,'Exact finite post-execution measured comparison scope')
        need('Independent source-derived whole State/x87/control mapping'in report['requires']and'Meaningful actual native refusal and same-context retry evidence'in report['requires'],'Unclosed acceptance prerequisites preserved')
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        pin(__file__);pin(sys.executable)
        p=out/'independent-actual-observations.json';p.write_text(json.dumps(cases,indent=2)+'\n');pin(p)
        result=dict(passed=passed,execution_sha256=E,comparison_sha256=C,counts=dict(COUNTS),files=PINS,
            archive_reader_opened=False,worker_launched=False,all_bounded_readers_closed=True,initializer_credit=0,
            independent_numeric_prediction=False,source_native_whole_State_equivalence=False,cold_source_equivalence=False,
            original_AFTER_seed=False,scope='Independent physical recheck of actual finite numerical outputs, complete CPU/API stack/caller hardware and own-BEFORE source-write byteflows. Source raw numerical results are comparison observations only. Whole source-derived State/x87 mapping, causal denials/retry and carried-prefix ownership/initializer integration remain unclosed.')
        p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),files=len(PINS),counts=dict(COUNTS))))
if __name__=='__main__':main(sys.argv[1])
