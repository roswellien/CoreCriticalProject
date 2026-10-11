"""Independent bounded current hypot source/C1/refusal review. Never opens archives."""
from pathlib import Path
from collections import Counter
import ast, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
A = R/'reports/m4-hypot-native'
T = R/'reports/m4-hypot-original/trace-validation-r2'
PINS, COUNTS = {}, Counter()
GATES = {
 'prelaunch': (R/'reports/m4-tree-review/hypot-c1-controls-prelaunch-r2/report.json','6a970a72f23aba6a96b59b2887d448d57d4a2569a4782d7dc9bc46b03bbe7cd5'),
 'preparation': (A/'fixture-preparation-r6/report.json','7219937e27edf2960129466f6416bfe109bee5b03f4e702c103fa296d80db03a'),
 'build': (A/'fixture-build-r6/build.json','9d36ad08985ecac2e28711cd2d9e3295b959eadd90524258ad166540c4f3f7dd'),
 'execution': (A/'fixture-execution-r3/report.json','7521a787982f762f1029fc4a62c026079a344fafb4400ef9db9dd21e42052908'),
 'comparison': (A/'fixture-comparison-r2/report.json','9017ac858319ea841b879b05bf0aa551140aa61d9bc7507b9f0efb48003e49b5'),
 'source': (A/'whole-state-r3/report.json','c341045f11517c80543df329175418e6441c4f564e1c5edfaa22028edf66eb8c'),
 'refusals': (A/'fixture-refusals-r1/report.json','a007a2c95f6fd86a10138b8f4938b509b1e8e1344b18c4ad277fd5352d547f18'),
 'trace': (T/'report.json','be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f'),
 'normal': (R/'reports/m4-hypot-original/prefix-validation-r2/report.json','80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313'),
}
def need(v, why):
 if not v: raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower() not in ('.mwb','.zip'),'No capture/archive reader')
 if str(p) in PINS:
  need(h is None or PINS[str(p)]==h,'Previously verified physical identity');return p
 actual=sha(p);need(h is None or h==actual,'Exact physical identity '+str(p));PINS[str(p)]=actual;return p
def blob(p):return pin(p).read_bytes()
def load(p,h=None):return json.loads(pin(p,h).read_bytes())
def eq(a,b,why):
 if a!=b:
  if isinstance(a,(bytes,bytearray)) and isinstance(b,(bytes,bytearray)):
   d=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
   raise ValueError(why+' lengths='+str((len(a),len(b)))+' differences='+str(d[:20]))
  raise ValueError(why+' '+str((a,b))[:500])
def u(b,at=0,n=1):return struct.unpack_from('<'+'I'*n,b,at)
def module(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def literal_assignment(p,key):
 rows=[x.value for x in ast.parse(pin(p).read_text()).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in x.targets)]
 need(len(rows)==1,'Exact source-authored additive literal '+key);return ast.literal_eval(rows[0])
def physical_pe(data,pc,width):
 pe=u(data,60)[0];need(data[pe:pe+4]==b'PE\0\0','Physical PE signature');opt=pe+24
 need(struct.unpack_from('<H',data,opt)[0]==0x10b,'Original PE32 source')
 base=u(data,opt+28)[0];n=struct.unpack_from('<H',data,pe+6)[0];at=opt+struct.unpack_from('<H',data,pe+20)[0]
 for i in range(n):
  row=at+i*40;vs,va,rs,ro=u(data,row+8,4);offset=pc-base-va
  if 0<=offset and offset+width<=rs:
   need(u(data,row+36)[0]&0x20000000,'Original instruction owns executable section');return data[ro+offset:ro+offset+width]
 raise ValueError('Complete original instruction has physical PE backing')
def project_return(data,base):
 result=bytearray(data);offset=0x20001800-base
 if 0<=offset and offset+4<=len(result):
  eq(u(result,offset)[0],0x410a80,'Only genuine external CALL return marker');struct.pack_into('<I',result,offset,0xfffffff0)
 return bytes(result)
def raw_cpu(context,pc=None):
 need(len(context)==716,'Complete stopped x86 CONTEXT')
 values=[u(context,o)[0] for o in (176,172,168,164,196,180,160,156,192,184)]
 values[8]&=~0x10100
 if pc is not None:values[9]=pc
 return values
BITS={'CF':0,'PF':2,'AF':4,'ZF':6,'SF':7,'DF':10,'OF':11}
ARITH=('CF','PF','AF','ZF','SF','OF')
CONDITIONS={'je':('ZF',),'jz':('ZF',),'jne':('ZF',),'jnz':('ZF',),'ja':('CF','ZF'),'jae':('CF',),'jb':('CF',),'jbe':('CF','ZF'),'jl':('SF','OF'),'jle':('ZF','SF','OF'),'jg':('ZF','SF','OF'),'jge':('SF','OF'),'js':('SF',),'jns':('SF',),'jo':('OF',),'jno':('OF',),'jp':('PF',),'jnp':('PF',),'sbb':('CF',),'adc':('CF',),'sete':('ZF',),'setge':('SF','OF')}
def domain_after(m,row,prior):
 # Independently audit exactly which original flag values may be undefined.
 out=dict(prior);op=row['mnemonic'];args=row['decoded_operands'];pc=row['pc']
 def define(names):
  for key in names:out.pop(key,None)
 def undef(key,why):out[key]=dict(PC=pc,mnemonic=op,reason=why)
 if op in ('add','adc','sub','sbb','neg','cmp'):define(ARITH)
 elif op in ('inc','dec'):define(tuple(k for k in ARITH if k!='CF'))
 elif op in ('and','or','xor','test'):
  define(('CF','PF','ZF','SF','OF'));undef('AF','logical source instruction has architecturally undefined AF')
 elif op in ('shl','shr','sar'):
  a=args[1] if len(args)>1 else {'kind':'immediate','value':1}
  need(a['kind'] in ('register','immediate'),'Current finite shift count has no extra unobserved memory read')
  n=(m.reg(a['register']) if a['kind']=='register' else a['value'])&31
  if n:
   define(('PF','ZF','SF'));undef('AF','nonzero source shift has architecturally undefined AF')
   if n==1:define(('OF',))
   else:undef('OF','multi-bit source shift has architecturally undefined OF')
   if n<args[0]['bits']:define(('CF',))
   else:undef('CF','source shift count reaches the operand width')
 elif op in ('std','cld'):define(('DF',))
 elif op=='sahf':define(('CF','PF','AF','ZF','SF'))
 return out
def machine_cpu(m,flags):
 for k,b in BITS.items():flags=(flags&~(1<<b))|(int(bool(m.flag(k)))<<b)
 return [m.reg(k) for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi')]+[flags,m.cursor]
def projected(cpu,domain):
 result=list(cpu);result[8]&=~sum(1<<BITS[k] for k in domain);return result
def initial_state(cpu,fx):
 # Explicit physical State layout reviewed by the current compiled gate.
 result=bytearray(3504)
 for offset,value in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),cpu[:8]+[cpu[9]]):struct.pack_into('<I',result,offset,value)
 struct.pack_into('<Q',result,2080,cpu[8])
 for offset,bit in zip((2065,2067,2069,2071,2073,2075,2077),(0,2,4,6,7,10,11)):result[offset]=(cpu[8]>>bit)&1
 result[2768:3280]=fx
 for offset,value in ((2090,0x2b),(2106,0x2b),(2110,0x23)):struct.pack_into('<H',result,offset,value)
 return bytes(result)
def main(name):
 need(re.fullmatch('hypot-current-review-r[1-9][0-9]*',name),'Additive review revision')
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh immutable output');out.mkdir()
 passed=False;witnesses=[];refusal_witnesses=[];gate_rows={};declared_archives={}
 try:
  gates={}
  for key,(path,h) in GATES.items():
   j=load(path,h);need(j['passed'],'Passed exact current '+key);gates[key]=j;gate_rows[key]=dict(path=str(path),sha256=h)
   for field in ('files','artifacts'):
    for p,digest in j.get(field,{}).items():
     if Path(p).suffix.lower() in ('.mwb','.zip'):
      need(p not in declared_archives or declared_archives[p]==digest,'Consistent retained archive identity');declared_archives[p]=digest
     else:pin(p,digest)
  eq(gates['execution']['build_sha256'],GATES['build'][1],'Execution uses current reviewed build6')
  eq(gates['build']['preparation_sha256'],GATES['preparation'][1],'Build uses current preparation6')
  eq(gates['comparison']['execution_sha256'],GATES['execution'][1],'Current comparison execution lineage')
  eq(gates['refusals']['build_sha256'],GATES['build'][1],'Actual refusals use current build6')
  eq(gates['refusals']['review_sha256'],GATES['prelaunch'][1],'Actual refusals use current compiled admission review')
  need(gates['execution']['all_processes_closed'] and gates['refusals']['all_processes_closed'],'All current workers closed')
  need(not gates['source']['independent_numeric_prediction'] and not gates['source']['source_AFTER_machine_seed'],'Explicit finite numerical-seam scope')
  need(not gates['trace']['canonical_debugger_FIP_FDP_claimed'] and not gates['trace']['debugger_metadata_replaced'],'Raw debugger metadata retained without canonical claim')
  eq(gates['trace']['normal_canonical_ENV_gate_sha256'],GATES['normal'][1],'Independent normal canonical metadata gate retained')
  base=pin(R/'tools/m4-hypot-native/source_model.py','179f954df6504f0d9297d671af63e89b4ae948bf0fd3cc4b50d4a982f84d8b51')
  model=R/'tools/m4-hypot-native/source_model_v3.py'
  eq(literal_assignment(model,'changes'),[
   ('self.cw = value\n','self.cw = (value & 0x1f3f) | 0x40\n'),
   ('self.last_fp = None',"self.last_serialized_sw = struct.unpack_from('<H', self.state, 2770)[0]\n            self.last_fp = None"),
   ("self.reg('ax', seam['value'])","self.reg('ax', seam['value'])\n                self.last_serialized_sw = seam['value']"),
   ('(before_sw & ~0x3800) | (observed_sw & 0x3800)','(self.last_serialized_sw & ~0x3800) | (observed_sw & 0x3800)')], 'Only four exact source-authority/lazy-FXSW model changes')
  verify_base=pin(R/'tools/m4-hypot-native/verify_whole_state.py')
  verify_wrap=pin(R/'tools/m4-hypot-native/verify_whole_state_v3.py')
  eq(literal_assignment(verify_wrap,'changes'),[
   ("ROOT/'tools/m4-hypot-native/source_model.py'","ROOT/'tools/m4-hypot-native/source_model_v3.py'"),
   ("AREA/'fixture-comparison-r1/report.json'","AREA/(sys.argv[2]+'/report.json')"),
   ("'3aa19148ad564700afcc84b459ad8aa8f9c6b7034063396db09ddf6f1a93d863'","sys.argv[3]"),
   ('        pin(__file__);pin(sys.executable)',"        pin(BASE);pin(ROOT/'tools/m4-hypot-native/source_model.py')\n        pin(__file__);pin(sys.executable)")], 'Exact immutable verifier selector/closure wrapper')
  verify_text=verify_base.read_text()
  need(verify_text.index('m.project_final_fp(sw,raw80)')<verify_text.index("eq(blob(target/'after/State.bin')"),'Expected source State completed before reading native AFTER State')
  need('program=program,callbacks={},descriptors=descriptors,numerical_seams=seams' in verify_text,'Explicit literal program and finite seams; no inherited default program/response seed')
  I=module(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','review_hypot_integer')
  S=module(model,'review_hypot_field_source');Numeric=S.machine_class(I)
  pin(R/'tools/m4-formatting-source/flag_domain.py');pin(R/'tools/m4-hypot-native/compare_fixture.py');pin(R/'tools/m4-hypot-native/run_refusals.py')
  descriptors=load(R/'reports/m4-hypot-original/trace-preparation-r8/trace-instruction-contracts.json')
  need(descriptors['descriptor_gaps']==0,'Complete zero-gap descriptor inventory')
  drows=descriptors['instructions'];need(len(drows)==3538 and len({r['pc'] for r in drows})==3538,'3538 distinct exact original definitions')
  images={'game':blob(R/'MW3/Mech3.exe'),'crt':blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')}
  for row in drows:
   eq(physical_pe(images[row['module']],row['pc'],row['width']),bytes.fromhex(row['bytes_hex']),'Whole independently resolved physical source bytes')
   eq(row['contract']['bytes_hex'],row['bytes_hex'],'Original instruction semantic contract physical bytes')
   need(row['descriptor_complete'],'Complete source operand descriptor');COUNTS['physical_source_rows']+=1
  program={r['pc']:r['contract'] for r in drows};desc={r['pc']:r for r in drows}
  traces=load(T/'actual-source-traces.json');observed=load(T/'actual-source-accesses.json')
  derivations=load(A/'whole-state-r3/source-derivations.json')
  need(len(traces)==len(derivations)==6 and len(observed)==3696,'Genuine/source six-case finite inventory')
  inputs=load(gates['preparation']['inputs'],gates['preparation']['inputs_sha256'])
  need(not inputs['source_AFTER_seed'] and not inputs['numerical_results_seeded'],'Whole trace BEFORE coupling only')
  states=blob(Path(gates['preparation']['inputs']).parent/'input-state.bin');need(len(states)==3480,'Complete six genuine CPU/FX/ENV inputs')
  native_by={(r['level'],r['sequence']):Path(r['output']) for r in gates['execution']['runs']}
  eq(set(native_by),{(level,seq) for level in ('O0','O2') for seq in range(6)},'Both actual builds and six inputs')
  for seq,t in enumerate(traces):
   need(t['sequence']==seq and t['event_count']==1007 and t['API_count']==2 and not t['unobserved_external_instruction_intervals'],'Complete actual source trace')
   raw_events=blob(T/f'raw-observations/case-{seq}-events.bin');raw_record=blob(T/f'raw-observations/case-{seq}-record.bin')
   need(len(raw_events)==1007*1840 and len(raw_record)==356992,'Complete source raw event/record extents')
   eq(raw_record[36:76],struct.pack('<10I',*t['own_BEFORE_CPU']),'Raw genuine root BEFORE CPU')
   eq(raw_record[116:628],bytes.fromhex(t['own_BEFORE_FX512_hex']),'Raw genuine root BEFORE FX')
   eq(raw_record[2164:2192],bytes.fromhex(t['own_BEFORE_ENV28_hex']),'Raw genuine root BEFORE ENV')
   eq(states[seq*580:(seq+1)*580],raw_record[36:76]+raw_record[116:628]+raw_record[2164:2192],'Native input is complete coherent genuine BEFORE')
   eq(raw_record[628:1140],bytes.fromhex(t['own_AFTER_FX512_hex']),'Raw actual source final numerical field owner')
   rows=[a for a in observed if a['sequence']==seq];need(len(rows)==616,'Actual complete source operands per input')
   per={i:[] for i in range(1007)}
   for a in rows:per[a['instruction_index']].append(a)
   seams=[];final_event=None
   for index,ins in enumerate(t['instructions']):
    eq(ins['index'],index,'Actual source ordinal');pc=ins['PC'];raw=raw_events[index*1840:(index+1)*1840];h=u(raw,0,8)
    eq(h[:6],(index,pc,ins['next_PC'],pc+1,desc[pc]['opcode'],len(desc[pc]['cells'])),'Whole actual source header')
    before,after=raw[32:748],raw[748:1464]
    eq(raw_cpu(before,pc),ins['BEFORE_CPU'],'Raw BEFORE CONTEXT/source CPU projection')
    eq(raw_cpu(after),ins['AFTER_CPU'],'Raw AFTER CONTEXT/source CPU projection')
    eq(u(raw,1832,2),tuple(ins['FS_heads']),'Raw retained source FS observations')
    eq(len(per[index]),len(desc[pc]['cells']),'Every raw source operand accounted')
    for ordinal,(a,d) in enumerate(zip(per[index],desc[pc]['cells'])):
     cell=raw[1464+ordinal*60:1524+ordinal*60];address=(d['displacement']+sum(v*c for v,c in zip(ins['BEFORE_CPU'][:8],d['coefficients']))+(t['TEB'] if d['segment'] else 0))&0xffffffff
     eq(u(cell,0,7),(address,d['width'],d['read'],d['write'],d['segment'],1,1),'Whole causal raw source operand geometry')
     eq((a['PC'],a['address'],a['width'],a['read'],a['write']), (pc,address,d['width'],d['read'],d['write']),'Actual exported operand identity')
     eq(cell[28:28+d['width']].hex(),a['before_hex'],'Whole original operand preimage')
     eq(cell[44:44+d['width']].hex(),a['after_hex'],'Whole original operand postimage');COUNTS['raw_source_operand_joins']+=1
    op=program[pc]['mnemonic']
    if op=='fnstsw':
     need(program[pc]['bytes_hex']=='dfe0','Only exact FNSTSW AX16 numerical seam')
     seams.append(dict(kind='SW_AX16',PC=pc,value=u(after,176)[0]&65535));COUNTS['FNSTSW_AX16_observations']+=1
    if op=='fstp':
     for a in per[index]:
      need(a['write'] and a['width'] in (4,8),'Only actual field-sized FSTP memory seam')
      seams.append(dict(kind='FSTP_SCALAR',PC=pc,address=a['address'],width=a['width'],bytes_hex=a['after_hex']));COUNTS['FSTP_scalar_observations']+=1
    if pc==0x4b5905:
     need(final_event is None,'Unique last literal FSTP');final_event=(ins,raw,before,after,per[index][0])
    COUNTS['raw_CONTEXT716_sides']+=2
   eq(seams,derivations[seq]['numerical_seams'],'Every model numerical seam directly joins raw genuine observations')
   need(len(seams)==75 and sum(s['kind']=='SW_AX16' for s in seams)==14,'Exact fourteen SW and sixty-one scalar observations')
   native=native_by[('O0',seq)];bcpu=list(u(blob(native/'before/CPU.bin'),0,10));fx=raw_record[116:628]
   eq(blob(native/'before/State.bin'),initial_state(bcpu,fx),'Independent whole native initial State layout')
   pack=blob(inputs['cases'][seq]['pack']);need(len(pack)==12+190*4104 and pack[:8]==b'MW4J124P' and u(pack,8)[0]==190,'Whole current coherent BEFORE pack')
   memory={};rights={}
   for i in range(190):
    address,permission=u(pack,12+i*4104,2);need(address not in memory and permission in (0,1,2),'Unique complete input pages and typed legacy permissions')
    memory[address]=project_return(pack[20+i*4104:20+i*4104+4096],address);rights[address]=permission
    eq(blob(native/f'before/pages/{address}.bin'),memory[address],'Whole native BEFORE page from genuine current pack')
   m=Numeric(initial_state(bcpu,fx),fx,struct.pack('<10I',*bcpu),memory,program=program,callbacks={},descriptors=desc,numerical_seams=seams)
   domain={};lifetimes=[]
   for ins in t['instructions']:
    pc=ins['PC'];row=program[pc];eq(m.cursor,pc,'Literal-derived source path without branch/path seed')
    eq(projected(machine_cpu(m,bcpu[8]),domain),projected(ins['BEFORE_CPU'],domain),'Whole derived BEFORE CPU and defined flags')
    used=CONDITIONS.get(row['mnemonic'],())
    need(not set(used)&set(domain),'No undefined flag controls an admitted branch/arithmetic result')
    COUNTS['defined_flag_consumption_relations']+=len(used)
    domain=domain_after(m,row,domain);old=len(m.accesses);m.step();m.word(2472,m.cursor)
    acpu=list(ins['AFTER_CPU'])
    if pc==0x4b593e:eq(acpu[9],0x410a80,'Exact original root RET');acpu[9]=0xfffffff0
    eq(projected(machine_cpu(m,bcpu[8]),domain),projected(acpu,domain),'Whole derived AFTER CPU and exactly bounded undefined flags')
    actual=per[ins['index']];generated=m.accesses[old:];need(len(actual)==len(generated),'All literal operand effects accounted')
    for p,a in zip(generated,actual):
     expected=int.from_bytes(bytes.fromhex(a['after_hex'] if a['write'] else a['before_hex']),'little')
     if pc==0x4b593e:expected=0xfffffff0
     eq(tuple(p),(pc,a['address'],expected,a['width'],a['write']),'Pure current literal operand value and causal address');COUNTS['literal_derived_operands']+=1
    lifetimes.append(dict(PC=pc,undefined_flags=dict(domain)));COUNTS['literal_derived_instruction_CPU_pairs']+=1
   eq(lifetimes,derivations[seq]['flag_lifetimes'],'Complete scoped source undefined-flag lifetimes')
   need(m.cursor==0xfffffff0 and not m.call_stack and m.seam_index==75,'Exact terminal root/empty source CALL stack and seam consumption')
   # Independently assemble the declared finite final FP representation. These
   # are explicit field observations, never a complete AFTER machine seed.
   final_fx=raw_record[628:1140];sw=struct.unpack_from('<H',final_fx,2)[0]
   eq(sw,derivations[seq]['final_SW'],'Exact final SW16 numerical field')
   eq(sw&0x3800,struct.unpack_from('<H',fx,2)[0]&0x3800,'Observed finite source balances initial/final TOP')
   result=bytearray(m.state)
   for bit,offset in ((0,2755),(1,2753),(2,2751),(3,2749),(4,2747),(5,2745),(6,2757),(8,2737),(9,2739),(10,2741),(14,2743)):result[offset]=(sw>>bit)&1
   struct.pack_into('<H',result,2768,m.cw)
   serialized=next(s['value'] for s in reversed(seams) if s['kind']=='SW_AX16')
   struct.pack_into('<H',result,2770,(serialized&~0x3800)|(sw&0x3800))
   raw80=[final_fx[32+i*16:42+i*16] for i in range(8)]
   eq([b.hex() for b in raw80],derivations[seq]['final_raw80_hex'],'Eight explicit final raw80 numerical fields')
   for i,b in enumerate(raw80):result[2486+i*16:2496+i*16]=b
   eq((m.last_fp['pc'],m.last_fp['bytes_hex'],m.last_fp_address),(0x4b5905,'d95e20',0x60b2e8),'Literal-derived last metadata-defining instruction/address')
   struct.pack_into('<H',result,2774,0x15e);struct.pack_into('<I',result,2776,0x4b5905);result[2780:2782]=result[2110:2112]
   struct.pack_into('<I',result,2784,0x60b2e8);result[2788:2790]=result[2106:2108]
   COUNTS['additional_final_SW16_observations']+=1;COUNTS['additional_final_raw80_10B_observations']+=8
   eq(blob(A/f'whole-state-r3/case-{seq}-derived-State.bin'),result,'Independent finite final State field assembly')
   ins,raw,before,after,store=final_event
   source_st0=before[236:246];source_cw=struct.unpack_from('<H',before,204)[0];source_post_sw=struct.unpack_from('<H',after,206)[0]
   eq(source_post_sw&0x200,sw&0x200,'Final source FSTP C1 survives remaining literal non-FP instructions')
   for level in ('O0','O2'):
    target=native_by[(level,seq)];eq(blob(target/'after/State.bin'),result,'Whole finite native/source State3504')
    eq(list(u(blob(target/'after/CPU.bin'),0,10)),machine_cpu(m,bcpu[8]),'Whole native/source final CPU40')
    for address,value in m.memory.items():eq(blob(target/f'after/pages/{address}.bin'),value,'Whole pure BEFORE plus source-derived memory effects');COUNTS['whole_source_derived_page4096_relations']+=1
    COUNTS['whole_source_derived_State3504_relations']+=1;COUNTS['whole_source_derived_CPU40_relations']+=1
    proof=blob(target/'final-FSTP-proof.bin');need(len(proof)==32,'Whole actual final FSTP proof')
    eq(u(proof,0,2),(0x4b5905,0x60b2e8),'Exact live final FSTP source PC/destination')
    actual_cw,actual_sw=struct.unpack_from('<2H',proof,8);eq(actual_cw,source_cw,'Actual hardware conversion under exact current source CW')
    eq(proof[12:22],source_st0,'Actual native live pre-pop raw80 equals genuine stopped source ST0')
    eq(proof[22:26],proof[26:30],'Lowered F32 equals separately executed actual hardware F32')
    eq(proof[26:30].hex(),store['after_hex'],'Hardware final F32 equals actual source publication')
    eq((actual_sw>>9)&1,(source_post_sw>>9)&1,'Actual hardware C1 equals genuine source FSTP C1')
    eq(result[2739],(actual_sw>>9)&1,'Native software C1 is the measured current conversion bit')
    eq(proof[30:32],bytes(2),'Complete zero-initialized proof padding retained')
    hw=blob(target/'host-hardware.bin');need(len(hw)==1632,'Complete actual outer caller boundary')
    eq(hw[:512],hw[1088:1600],'Actual outside Runtime invocation whole FX512 restoration')
    eq(hw[512:540],hw[1600:1628],'Actual outside Runtime invocation whole ENV28 restoration')
    COUNTS['actual_final_FSTP_C1_relations']+=1;COUNTS['positive_outer_caller_FX512_relations']+=1;COUNTS['positive_outer_caller_ENV28_relations']+=1
    witnesses.append(dict(level=level,sequence=seq,source_CW=source_cw,final_source_SW=sw,last_serialized_SW=serialized,
      hardware_final_store_SW=actual_sw,C1=(actual_sw>>9)&1,raw80_input=source_st0.hex(),F32=proof[26:30].hex(),
      whole_State_sha256=hashlib.sha256(result).hexdigest(),whole_final_store_proof_hex=proof.hex(),
      hardware_SW_other_bits_source_equality_claimed=False,final_FP_metadata_source_derived=True))
   COUNTS['genuine_input_sequences']+=1
  # Refusals remain actual compiled seam observations. Verify accepted source
  # prefixes and every complete poisoned retry byte, without guessing unseen
  # failed payload values or replacing exception metadata.
  reasons={1:'Exact causal source PC/address/width/direction',2:'Exact causal source PC/address/width/direction',3:'Unobserved numeric source PC at a native bridge denied',4:'Exact actual source dispatch PC',5:'Guest CW differs from isolated hardware CW',6:'Exact control State identity',7:'Exact admitted FP exception mask',8:'Exact current source return frame identity'}
  expected_cursor={1:5,2:0,3:5,4:5,5:44,6:44,7:7,8:53}
  need(len(gates['refusals']['runs'])==16,'Both actual eight-seam refusal sequences')
  for run in gates['refusals']['runs']:
   level,mode=run['level'],run['mode'];need(level in ('O0','O2') and mode in reasons and run['exit_code']==0 and run['process_closed'],'Actual finite refusal completion')
   p=Path(run['output']);eq(blob(p/'result/status.bin'),struct.pack('<5I',mode,1,1,0,1),'Actual denial, poison, no completion and revoked active context')
   refusal=blob(p/'result/refusal.txt').decode();eq(refusal,run['refusal'],'Sealed actual first refusal text')
   eq(refusal,'memory_access site=0x004b5910 target=0x004b5910: Admitted native callback failed: '+reasons[mode],'Exact intended first refusal cause')
   b={q.relative_to(p/'retry/before').as_posix():q for q in (p/'retry/before').rglob('*') if q.is_file()}
   a={q.relative_to(p/'retry/after').as_posix():q for q in (p/'retry/after').rglob('*') if q.is_file()}
   eq(set(b),set(a),'Exact whole retry block inventory');need(len(b)==199 and len([k for k in b if k.startswith('pages/')])==190,'Full private/public retry extent')
   for key in b:eq(blob(b[key]),blob(a[key]),'Same actual poisoned Runtime whole retry '+key);COUNTS['whole_same_Runtime_retry_blocks']+=1
   context=struct.unpack('<16Q',blob(b['context.bin']));eq(context[1],expected_cursor[mode],'Observed exact refusal prefix cursor')
   need(context[7]==1 and context[8]==0 and context[12]==context[13] and all(context[i] for i in (6,12,13,14,15)),'Same live context/State/Runtime/thread identities at retry')
   route=blob(b['routes.bin']);eq(route,struct.pack('<5I',0x4b5910,0x4b5910,0xfffffff0,0,0),'Single genuine incomplete registered Runtime route')
   prefix=blob(b['accesses.bin']);need(len(prefix)==context[1]*44,'Complete accepted actual operand prefix')
   positive=blob(native_by[(level,0)]/'accesses.bin');eq(prefix,positive[:len(prefix)],'Every admitted operand prefix equals genuine positive source payloads')
   before={int(q.stem):bytearray(blob(q)) for q in (p/'before/pages').glob('*.bin')};need(len(before)==190,'Complete own coherent BEFORE at refusal root')
   for i in range(context[1]):
    pc,address,width,writing=u(prefix,i*44,4);need(0<width<=28,'Full refusal-prefix width')
    if writing:before[address&~4095][address&4095:(address&4095)+width]=prefix[i*44+16:i*44+16+width]
   for address,value in before.items():eq(blob(b[f'pages/{address}.bin']),value,'Refusal memory follows own BEFORE and exact accepted writes only');COUNTS['whole_refusal_prefix_page4096_relations']+=1
   hw=blob(p/'host-hardware.bin');need(len(hw)==1632,'Complete actual refusal caller hardware')
   eq(hw[:512],hw[1088:1600],'Whole outside refusal/retry caller FX512');eq(hw[512:540],hw[1600:1628],'Whole outside refusal/retry caller ENV28')
   COUNTS['actual_precise_refusals']+=1;COUNTS['actual_same_Runtime_poisoned_retries']+=1;COUNTS['negative_outer_caller_FX512_relations']+=1;COUNTS['negative_outer_caller_ENV28_relations']+=1
   COUNTS['whole_accepted_refusal_prefix_operands']+=context[1]
   refusal_witnesses.append(dict(level=level,mode=mode,first_reason=refusal,cursor=context[1],source_PC=u(blob(b['State.bin']),2472)[0],
       full_retry_blocks=199,accepted_prefix_operands=context[1],failed_read_payload_observed=False if mode in (1,2) else None,
       full_fault_State_source_equivalence_claimed=False,whole_own_BEFORE_memory_causality=True))
  need(COUNTS['literal_derived_instruction_CPU_pairs']==6042 and COUNTS['literal_derived_operands']==3696,'Complete current genuine literal source extent')
  need(COUNTS['FNSTSW_AX16_observations']==84 and COUNTS['FSTP_scalar_observations']==366 and COUNTS['additional_final_SW16_observations']==6 and COUNTS['additional_final_raw80_10B_observations']==48,'Complete explicit numerical observation inventory')
  need(COUNTS['whole_same_Runtime_retry_blocks']==3184 and COUNTS['actual_precise_refusals']==16,'Complete meaningful current refusal extent')
  # Pin the exact IR ordering of the final memory callback before virtual-ST0
  # pop. Whole linked code and all relocation targets are independently bound
  # by the current prelaunch gate, not inferred from this text check.
  ir=pin(A/'lifts-r4/f_4b5860-host.ll').read_text();last=ir.index('i32 4937989')
  region=ir[last:];call=region.index('@mw34_hypot_write_memory_f32');pop=region.index('i32 2486',call)
  need(call<pop and 'store x86_fp80' in region[pop:],'Live raw80 final-store callback precedes literal virtual stack pop')
  pin(__file__);pin(sys.executable)
  for p,h in PINS.items():eq(sha(p),h,'Final stable physical identity')
  for label,data in (('finite-source-C1-relations.json',witnesses),('actual-refusal-relations.json',refusal_witnesses)):
   q=out/label;q.write_text(json.dumps(data,indent=2)+'\n');pin(q)
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent current bounded physical/raw source, finite State, live final FSTP C1 and actual refusal review',
   counts=dict(COUNTS),gates=gate_rows,files=PINS,archive_reader_opened=False,writer_launched=False,
   retained_archive_identities_reviewed_but_not_payload_rehashed=len(declared_archives),
   all_actual_workers_closed=True,whole_native_State_source_mapping=passed,
   numerical_scope=dict(FNSTSW_AX16=84,FSTP_scalar=366,final_SW16=6,final_raw80_10B=48,independent_numerical_prediction=False),
   debugger_metadata_replaced=False,canonical_debugger_metadata_claimed=False,final_metadata_literal_source_derived=True,
   whole_API_checkpoint_State_source_equivalence_claimed=False,full_fault_State_source_equivalence_claimed=False,
   cold_source_equivalence_claimed=False,general_unmasked_FP_exception_semantics_claimed=False,connected_prefix_acceptance=False,initializer_credit=0,
   requires=['Fresh genuine chronological carried-prefix integration','Fresh linked ownership/lifecycle/source/provider/paired acceptance'])
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(COUNTS),physical_inputs=len(PINS))))
if __name__=='__main__':main(sys.argv[1])
