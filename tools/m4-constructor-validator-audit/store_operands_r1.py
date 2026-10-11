"""Independent physical constructor store operands; no worker/capture/native run."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
REGS = ('eax','ecx','edx','ebx','esp','ebp','esi','edi')
BYTE_REGS = ('al','cl','dl','bl','ah','ch','dh','bh')
KNOWN = {'mov','push','call','pop','cmp','test','add','jne','lea','xor','je','ret','jmp','sub','sar','sbb','inc','jae','sete','neg','dec','jbe','jge','jle','jl','setne','and','jns','jg','or'}

def need(v,m):
    if not v: raise ValueError(m)
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def reg_name(index): return REGS[index] if index is not None else None
def address(base=None,index=None,scale=1,displacement=0,segment=None):
    return dict(base=reg_name(base),index=reg_name(index),scale=scale,displacement=displacement&0xffffffff,segment=segment or ('ss' if base in (4,5) else 'ds'),offset_arithmetic='uint32 modulo 2^32',linear_arithmetic='uint32(segment_base + effective_offset)')

def decode(row):
    """Decode only physical x86 store forms; textual rows are cross-checks."""
    raw=bytes.fromhex(row['bytes']);at=0;segment=None
    if raw[0]==0x64:segment='fs';at+=1
    op=raw[at];at+=1
    def get(width,signed=False):
        nonlocal at
        need(at+width<=len(raw),'Whole immediate/displacement physical bytes')
        value=int.from_bytes(raw[at:at+width],'little',signed=signed);at+=width;return value
    def modrm():
        nonlocal at
        value=get(1);mod=value>>6;field=(value>>3)&7;rm=value&7
        if mod==3:return field,dict(register=rm)
        base=rm;index=None;scale=1;disp=0
        if rm==4:
            sib=get(1);scale=1<<(sib>>6);index=(sib>>3)&7;base=sib&7
            if index==4:index=None
            if mod==0 and base==5:base=None;disp=get(4)
        elif mod==0 and rm==5:base=None;disp=get(4)
        if mod==1:disp+=get(1,True)
        elif mod==2:disp+=get(4,True)
        return field,address(base,index,scale,disp,segment)
    def finish(kind,width,ea,value,**extra):
        need(at==len(raw)==row['size'],'Independent store decoder consumes exact whole opcode')
        return dict(pc=row['pc'],size=row['size'],bytes=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'],kind=kind,width=width,address=ea,value=value,**extra)
    stack=address(4,displacement=-4,segment='ss')
    if 0x50<=op<=0x57:
        need(segment is None,'No unsupported prefixed PUSH')
        return finish('PUSH',4,stack,dict(kind='register',register=REGS[op-0x50],shift=0))
    if op in (0x68,0x6a):
        need(segment is None,'No unsupported prefixed immediate PUSH')
        return finish('PUSH',4,stack,dict(kind='immediate',immediate=get(4) if op==0x68 else get(1,True)&0xffffffff))
    if op==0xe8:
        relative=get(4,True);need(segment is None,'No unsupported CALL prefix')
        return finish('CALL',4,stack,dict(kind='immediate',immediate=(row['pc']+row['size'])&0xffffffff),branch_target=dict(kind='direct',target=(row['pc']+row['size']+relative)&0xffffffff))
    if op==0xff:
        field,target=modrm()
        if field==2:
            need(segment is None,'No unsupported indirect CALL prefix')
            return finish('CALL',4,stack,dict(kind='immediate',immediate=(row['pc']+row['size'])&0xffffffff),branch_target=dict(kind='register' if 'register'in target else 'memory',operand=target))
        if field==4:
            need(at==len(raw)and row['mnemonic']=='jmp','Exact physical read-only indirect JMP')
            return dict(pc=row['pc'],size=row['size'],bytes=row['bytes'],mnemonic='jmp',operands=row['operands'],store=False,reason='FF /4 near JMP reads target and does not store a return address')
        raise ValueError('Unsupported FF group write at '+hex(row['pc']))
    if op in (0x88,0x89):
        field,ea=modrm();need('register'not in ea,'Physical MOV memory destination')
        width=1 if op==0x88 else 4;index=field if width==4 or field<4 else field-4;shift=8 if width==1 and field>=4 else 0
        return finish('MOV',width,ea,dict(kind='register',register=REGS[index],shift=shift))
    if op in (0xc6,0xc7):
        field,ea=modrm();need(field==0 and 'register'not in ea,'Physical MOV immediate memory group')
        width=1 if op==0xc6 else 4
        return finish('MOV',width,ea,dict(kind='immediate',immediate=get(width)))
    if op==0x83:
        field,ea=modrm();need(field==0 and 'register'not in ea,'Only ADD memory RMW physically admitted')
        addend=get(1,True)&0xffffffff
        return finish('ADD',4,ea,dict(kind='prior_read_add',immediate=addend),prior_read=dict(pc=row['pc'],same_instruction_epoch_required=True,address='same source-derived destination EA',width=4,writing=False,no_intervening_store_required=True,source_memory_read_required=True))
    raise ValueError('Unsupported store physical opcode '+hex(op)+' at '+hex(row['pc']))

def text_address(text):
    match=re.fullmatch(r'(byte|word|dword) ptr (?:(cs|ds|es|ss|fs|gs):)?\[(.*)\]',text)
    need(match is not None,'Exact retained source memory operand syntax '+text)
    width={'byte':1,'word':2,'dword':4}[match[1]];base=None;index=None;scale=1;disp=0
    for term in match[3].split(' + '):
        if term in REGS:
            need(base is None,'Single retained source base');base=REGS.index(term)
        elif '*'in term:
            name,mult=term.split('*');need(name in REGS and index is None,'Retained source affine index');index=REGS.index(name);scale=int(mult,0)
        else:disp+=int(term,0)
    return width,address(base,index,scale,disp,match[2])

def text_value(text,width):
    if text in REGS:return dict(kind='register',register=text,shift=0)
    if text in BYTE_REGS:
        i=BYTE_REGS.index(text);return dict(kind='register',register=REGS[i if i<4 else i-4],shift=0 if i<4 else 8)
    return dict(kind='immediate',immediate=int(text,0)&((1<<(width*8))-1))

def crosscheck(row,d):
    if not d.get('store',True):return
    mnemonic=row['mnemonic'];ops=row['operands']
    need(mnemonic.upper()==d['kind'],'Physical/text mnemonic agreement')
    if mnemonic=='push':need(text_value(ops,4)==d['value'],'Physical/text source PUSH value')
    elif mnemonic=='call':
        target=d['branch_target']
        if target['kind']=='direct':need(int(ops.split()[0],0)==target['target'],'Physical direct CALL target')
        elif target['kind']=='register':need(REGS[target['operand']['register']]==ops,'Physical register indirect CALL target')
        else:need(text_address(ops)[1]==target['operand'],'Physical indirect memory CALL operand')
    else:
        destination,source=ops.split(', ');width,ea=text_address(destination)
        need(width==d['width']and ea==d['address'],'Independent ModRM destination affine EA and segment match retained source')
        if mnemonic=='mov':need(text_value(source,width)==d['value'],'Independent physical source register/immediate match')
        else:need(d['value']==dict(kind='prior_read_add',immediate=int(source,0)&0xffffffff),'Independent physical ADD addend')

CPP_PREFIX='''#pragma once
#include <cstdint>
#include <array>
namespace mw34::m4_constructor_store_source {
enum class Register : unsigned {eax,ecx,edx,ebx,esp,ebp,esi,edi,none};
enum class Segment : unsigned {ds,ss,fs};
enum class ValueKind : unsigned {reg,immediate,prior_read_add};
struct Affine {Register base,index;unsigned scale,displacement;Segment segment;};
struct Store {unsigned pc,size,width;Affine address;ValueKind kind;Register reg;unsigned shift,immediate;std::array<unsigned char,16>opcode;};
struct PriorRead {unsigned pc,address,width;std::uint64_t value,instruction_epoch;bool writing;};
inline constexpr Store stores[]{
'''
CPP_SUFFIX='''};
inline const Store*descriptor(unsigned pc){for(const auto&d:stores)if(d.pc==pc)return&d;return nullptr;}
template<class State> unsigned source_register(const State&s,Register r){switch(r){
case Register::eax:return s.gpr.rax.dword;case Register::ecx:return s.gpr.rcx.dword;
case Register::edx:return s.gpr.rdx.dword;case Register::ebx:return s.gpr.rbx.dword;
case Register::esp:return s.gpr.rsp.dword;case Register::ebp:return s.gpr.rbp.dword;
case Register::esi:return s.gpr.rsi.dword;case Register::edi:return s.gpr.rdi.dword;
case Register::none:return 0;}return 0;}
template<class State> unsigned effective_address(const State&s,const Affine&a){
const unsigned offset=source_register(s,a.base)+source_register(s,a.index)*a.scale+a.displacement;
const unsigned segment=a.segment==Segment::fs?s.addr.fs_base.dword:a.segment==Segment::ss?s.addr.ss_base.dword:s.addr.ds_base.dword;
return segment+offset;}
// Call before committing the memory mirror. State must be the current literal
// instruction's incoming address/source-register state, including pre-PUSH ESP.
// For ADD, caller supplies its genuine earlier literal read with a supervisor
// epoch tied to this instruction and no intervening store. This helper does not
// load or trust native/captured AFTER bytes and makes no source State mutation.
template<class State,class Require> void guard(const State&s,unsigned pc,unsigned address,unsigned width,std::uint64_t value,std::uint64_t instruction_epoch,const PriorRead*prior,Require require){
const auto*d=descriptor(pc);require(d&&s.gpr.rip.dword==pc,"Current independently decoded source store PC");
require(width==d->width,"Exact independently decoded source store width");
const std::uint64_t mask=width==4?0xffffffffULL:width==2?0xffffULL:0xffULL;
require(value<=mask,"Exact scalar width without hidden upper source value");
const auto ea=effective_address(s,d->address);require(address==ea,"Current incoming State source-derived store effective address");
std::uint64_t wanted{};
if(d->kind==ValueKind::reg)wanted=(std::uint64_t(source_register(s,d->reg))>>d->shift)&mask;
else if(d->kind==ValueKind::immediate)wanted=d->immediate&mask;
else {require(prior&&instruction_epoch&&prior->instruction_epoch==instruction_epoch&&prior->pc==pc&&prior->address==ea&&prior->width==width&&!prior->writing&&prior->value<=mask,"Genuine same-instruction source RMW read before mirror");wanted=(prior->value+d->immediate)&mask;}
require(value==wanted,"Independent incoming-State register/immediate or prior-read RMW source store value");}
} // namespace mw34::m4_constructor_store_source
'''

def header(stores):
    def reg(v):return 'Register::'+(v or 'none')
    rows=[]
    for d in stores:
        a=d['address'];v=d['value'];kind='reg' if v['kind']=='register' else v['kind']
        rows.append('{%d,%d,%d,{%s,%s,%d,%d,Segment::%s},ValueKind::%s,%s,%d,%d,{%s}},'%(d['pc'],d['size'],d['width'],reg(a['base']),reg(a['index']),a['scale'],a['displacement'],a['segment'],kind,reg(v.get('register')),v.get('shift',0),v.get('immediate',0),','.join(str(x)for x in bytes.fromhex(d['bytes']))))
    return CPP_PREFIX+'\n'.join(rows)+'\n'+CPP_SUFFIX

def main(name):
    out=ROOT/'reports/m4-constructor-native'/name
    need(not out.exists(),'Fresh additive constructor store source contracts');out.mkdir(parents=True)
    pins={};counts=Counter();passed=False
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'No capture/archive/payload reader')
        actual=sha(p);need(h is None or actual==h,'Exact frozen physical source '+str(p));pins[str(p)]=actual;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def write(name,data):
        p=out/name;p.write_text(json.dumps(data,indent=2)+'\n');pin(p);return p
    try:
        preparation_path=ROOT/'reports/m4-constructor-source/preparation-r1/report.json'
        preparation=read(preparation_path,'0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf')
        need(preparation['passed'],'Exact constructor source preparation')
        rows_path=preparation_path.parent/'source-instructions.json';rows=read(rows_path,preparation['files'][str(rows_path.resolve())])
        need(len(rows)==len({v['pc']for v in rows})==1401 and set(v['mnemonic']for v in rows)<=KNOWN,'Entire finite unique supported source instruction vocabulary')
        pe_path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec=importlib.util.spec_from_file_location('store_operand_physical_PE',pe_path);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
        game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');image=pe.PEImage(game_path.read_bytes())
        stores=[];nonstores=[];classifications=[]
        for row in rows:
            start,_=image.rva_range(row['pc']-image.image_base,row['size']);need(image.data[start:start+row['size']].hex()==row['bytes'],'All current physical constructor instructions exact')
            counts['physical_instruction_rows']+=1
            destination=row['operands'].split(',',1)[0]
            candidate=row['mnemonic']in('push','call')or('['in destination and row['mnemonic']not in('cmp','test','lea'))
            if candidate:
                d=decode(row);crosscheck(row,d);counts['independent_raw_candidate_decodes']+=1
                if d.get('store',True):stores.append(d);counts[d['kind']+'_stores']+=1
                else:nonstores.append(d)
            classifications.append(dict(pc=row['pc'],candidate=candidate,kind='store'if candidate and d.get('store',True)else'read-only-memory-JMP'if candidate else'no memory store in retained physical source form'))
        need(len(stores)==418 and len(nonstores)==3 and counts['independent_raw_candidate_decodes']==421,'Complete 421 heuristic candidates partition into418 real stores and3 non-writing JMPs')
        need(counts['PUSH_stores']==165 and counts['CALL_stores']==74 and counts['MOV_stores']==176 and counts['ADD_stores']==3,'Exact independent store source classes')
        need([v['pc']for v in nonstores]==[0x5abd1a,0x5abd26,0x5ac580],'All inherited heuristic false positives specifically refused')
        need([v['pc']for v in stores if v['kind']=='ADD']==[0x4bfb57,0x4c04f9,0x4c0759],'Exact finite RMW source prior-read sites')
        contracts=dict(schema='mw34.constructor.store_operand_source.v1',source_preparation_sha256=sha(preparation_path),source_instructions_sha256=sha(rows_path),stores=stores,non_writing_heuristic_candidates=nonstores,all_source_PC_classification=classifications,State_semantics=dict(address_and_register_values='Actual incoming current literal source State before committing mirror; especially pre-PUSH/CALL ESP',default_segments='SS for EBP/ESP base, DS otherwise; exact FS override from physical prefix64',integer_wrap='32-bit effective offset, linear address and DWORD addition modulo2^32; byte stores truncate low8 or selected high8',PUSH='EA=SSbase+incomingESP-4; value is incoming register DWORD or physically sign-extended immediate',CALL='EA=SSbase+incomingESP-4; value is physicalPC+whole instruction length',MOV='Physical ModRM destination effective address and original register/immediate value',ADD='Genuine same-instruction earlier literal read at independently computed EA; add physical sign-extended immediate and mask toDWORD',RMW_read_authority='Caller must tie actual earlier read PC/EA/width/value to current instruction epoch and prove no intervening store; no raw BEFORE/AFTER/candidate expected memory supplied',source_State_mutation=False),runtime_integration=dict(guard='constructor_store_operands.hpp: mw34::m4_constructor_store_source::guard',stage='Before constructor_source_write memory/native mirror commit',physical_PC_bytes_width_and_whole_owner_guards='Keep existing independent owning opcode/PC/width/requested-extent/fullmirror guards as well',source_operand_check_required=True,source_read_operands_checked=False,CALL_target_or_branch_path_admission=False,lifted_callback_preState_order_independent_review_pending=True),frontier=dict(uncompiled_recursive_entry=0x56fea0,source_descriptor_does_not_admit_branch=True,arbitrary_path_equivalence=False,all_418_stores_statically_described_but_actual_reachability_not_claimed=True),native_executed=False,capture_reader_opened=False,source_AFTER_seed=False,initializer_credit=0)
        path=write('contracts.json',contracts);guard=out/'constructor_store_operands.hpp';guard.write_text(header(stores));pin(guard)
        # Source-only structural checks of generated table, no compiler/worker.
        need(guard.read_text().count('ValueKind::')==len(stores)+2,'Exact single descriptor row per physical source store and two guard branches')
        need(all(v['pc']not in {n['pc']for n in nonstores}for v in stores),'JMP candidates cannot acquire a store descriptor')
        pin(__file__)
        for p,h in list(pins.items()):pin(p,h)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Independent archive-free physical raw ModRM/stack/immediate constructor store operand contracts, textual cross-check and reusable incoming-State guard. Static preparation only; integration and actual source callback timing remain separate.',counts=dict(counts),source_preparation_sha256='0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf',contracts_path=str(path.resolve())if'path'in locals()else None,contracts_sha256=sha(path)if'path'in locals()else None,guard_path=str(guard.resolve())if'guard'in locals()else None,guard_sha256=sha(guard)if'guard'in locals()else None,unsupported_store_forms=0 if passed else None,explicit_nonstore_JMP_PC=[0x5abd1a,0x5abd26,0x5ac580],native_executed=False,compiler_executed=False,capture_reader_opened=False,payload_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,files=pins)
        target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(target),contracts_sha256=report['contracts_sha256'],guard_sha256=report['guard_sha256'],counts=dict(counts))))

if __name__=='__main__':main(sys.argv[1])
