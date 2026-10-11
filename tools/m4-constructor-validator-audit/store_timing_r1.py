"""Bounded immutable constructor host-IR store callback timing receipt."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]

def need(v,m):
    if not v:raise ValueError(m)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def blocks(text):
    body=text[text.index('define ptr @mw34_onexit_game_f_'):];body=body[:body.index('\n}\n')]
    split=re.split(r'(?m)^(\d+):[^\n]*\n',body)
    return {split[i]:split[i+1]for i in range(1,len(split),2)}

INTEGRATION='''// Source-only suggested private SessionImpl addition. Keep existing ownership,
// opcode, full-mirror and source authority guards. These fields are supervisor
// provenance, never source State or memory. The helper Require must throw on false.
using ConstructorPriorRead=mw34::m4_constructor_store_source::PriorRead;
std::uint64_t constructor_operand_epoch_{};
ConstructorPriorRead constructor_operand_read_{};
unsigned constructor_operand_read_root_{};
bool constructor_operand_read_live_{};
void constructor_operand_read(State&source,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value){
 constructor_authority(source,root);
 require(pc==source.gpr.rip.dword&&bytes&&bytes<=4,"Actual literal constructor scalar read provenance");
 require(constructor_operand_epoch_<300000,"Finite source access epoch");
 ++constructor_operand_epoch_;
 constructor_operand_read_={pc,address,bytes,value,constructor_operand_epoch_,false};
 constructor_operand_read_root_=root;constructor_operand_read_live_=true;
}
void constructor_operand_store_guard(State&source,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value){
 constructor_authority(source,root);
 require(constructor_operand_epoch_<300000,"Finite source access epoch");
 const auto*prior=constructor_operand_read_live_&&constructor_operand_read_root_==root?&constructor_operand_read_:nullptr;
 mw34::m4_constructor_store_source::guard(source,pc,address,bytes,value,constructor_operand_epoch_,prior,[](bool v,const char*m){require(v,m);});
 constructor_operand_read_live_=false;++constructor_operand_epoch_;
}
// Integration sites:
// 1. constructor_owner_read: after the actual scalar/source PC checks and BEFORE
//    the `if(!allocation_for(...)) return`, call constructor_operand_read(...).
//    Record ALL genuine literal reads (owned/game/stack/TIB), no new public input.
// 2. constructor_source_write: call constructor_operand_store_guard(...) BEFORE
//    committing r.memory().write and binding->expected_store, then preserve full
//    State/FX transparency and complete current native/guest extent checks.
// 3. Scope entry/exit/poison clears constructor_operand_read_live_. Every literal
//    source write consumes/invalidates prior evidence, even non-owned writes.
// Borrowed MFC/onexit calls already require a genuine preceding literal CALL
// store; that store invalidates prior evidence before routing the service.
// This is a source-only suggested integration shape, not compiled/executed code.
'''

def main(name):
    out=ROOT/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh additive store timing receipt');out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'No capture/archive/raw reader')
        actual=sha(p);need(h is None or actual==h,'Exact pinned source/IR '+str(p));pins[str(p)]=actual;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    preparation=read(ROOT/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf')
    rows_path=ROOT/'reports/m4-constructor-source/preparation-r1/source-instructions.json';rows=read(rows_path,preparation['files'][str(rows_path.resolve())]);by_pc={r['pc']:r for r in rows}
    operands=read(ROOT/'reports/m4-constructor-native/store-operands-r1/report.json','56acaf9dffcf68355d6a68bcd28ef841e084208e9f10724a8a14d3d06ed63d33');need(operands['passed'],'Successful complete independent store descriptors')
    pin(operands['contracts_path'],operands['contracts_sha256']);pin(operands['guard_path'],operands['guard_sha256'])
    lift_report=read(ROOT/'reports/m4-remaining-service-source/lifts-r2/report.json','b408ef417766435e082a436a2af6fbbcd3827fd1e30e6503d7d16fc7b1fb3c8e')
    def ir(entry):
        path=ROOT/f'reports/m4-remaining-service-source/lifts-r2/f_{entry:x}-host.ll';pin(path,lift_report['source_bodies'][f'f_{entry:x}']['host_sha256']);return path,blocks(path.read_text())
    first_path,first=ir(0x4103f0);list_path,lists=ir(0x4bf910)
    selected=[]
    def claim(path,label,pc,kind,block,facts):
        need(by_pc[pc]['mnemonic']==kind.lower(),'Exact physical source instruction kind')
        selected.append(dict(kind=kind,pc=pc,source_instruction=by_pc[pc],source_IR=str(path.resolve()),source_IR_sha256=sha(path),label=label,block_text=block,callback_facts=facts))
    push=first['27']
    need(push.index('%37 = call noundef ptr @mw34_onexit_game_write32')<push.index('store i32 %33, ptr %31'),'Actual PUSH memory callback before ESP publication')
    need('%32 = load i32, ptr %31' in push and '%33 = add i32 %32, -4'in push and '%31 = getelementptr inbounds nuw i8, ptr %state, i32 2312'in push and '%34 = getelementptr inbounds nuw i8, ptr %state, i32 2120'in push and 'i32 noundef 4260896)'in push,'Physical PUSH source immediate and source ESP/SS-base arithmetic')
    claim(first_path,'27',0x410410,'PUSH',push,dict(callback='write32 %37',ESP_at_callback='Incoming ESP; decrement published only after callback',value=0x410420,address='incoming SSbase+ESP-4',source_GPR_mutation_before_callback=False))
    call=first['38']
    need(call.index('%51 = call noundef ptr @mw34_onexit_game_write32')<call.index('store i32 %47, ptr %45')<call.index('store i32 %42, ptr %52'),'Actual CALL memory callback before ESP and targetPC publication')
    need('%46 = load i32, ptr %45'in call and '%47 = add i32 %46, -4'in call and '%43 = load i32, ptr %NEXT_PC'in call and '%40 = add i32 %39, 5'in call,'Current CALL PC+5 saved return and incoming ESP source')
    claim(first_path,'38',0x410415,'CALL',call,dict(callback='write32 %51',ESP_at_callback='Incoming ESP',PC_at_callback='Physical source CALL PC',value='PC+5 from NEXT_PC',address='incoming SSbase+ESP-4',target_PC_publication='After memory callback',source_GPR_mutation_before_callback=False))
    mov=lists['42']
    need('%45 = load i32, ptr %FSBASE'in mov and '%47 = load i32, ptr %ESP'in mov and '%49 = call noundef ptr @mw34_onexit_game_write32'in mov and not re.search(r'^  store i(?:8|32) .*ptr %(?:ESP|FSBASE|EAX|ECX|EDX|EBX|ESI|EDI|EBP),',mov,re.M),'Actual FS MOV preserves source address/value State before callback')
    claim(list_path,'42',0x4bf91e,'MOV',mov,dict(callback='write32 %49',value='Incoming ESP',address='Incoming FSbase+0',source_GPR_or_segment_mutation_before_callback=False))
    rmw=[(label,b)for label,b in lists.items()if '@mw34_onexit_game_read32'in b and '@mw34_onexit_game_write32'in b and re.search(r'= add i32 %\d+, 4\n',b)]
    need(len(rmw)==1 and rmw[0][0]=='2718','Unique actual memory ADD source IR in current bounded helper')
    label,add=rmw[0]
    need(add.index('%2730 = call noundef i32 @mw34_onexit_game_read32')<add.index('%2731 = add i32 %2730, 4')<add.index('%2732 = call noundef ptr @mw34_onexit_game_write32')<add.index('store i8 %2735, ptr %2736'),'Actual RMW source read then add then write before flags publication')
    need('%2721 = load i32, ptr %ESI'in add and '%2722 = load i32, ptr %DSBASE'in add and '%2723 = add i32 %2721, 8'in add and '%2727 = add i32 %2725, 8'in add and not re.search(r'^  store i32 .*ptr %(?:ESP|FSBASE|DSBASE|EAX|ECX|EDX|EBX|ESI|EDI|EBP),',add,re.M),'RMW operand State remains unchanged at read and write callbacks')
    claim(list_path,label,0x4bfb57,'ADD',add,dict(read_callback='read32 %2730',write_callback='write32 %2732',prior_read_source='Actual read32 return %2730; never host expected or captured AFTER memory',value='uint32(prior_read+4)',address='Incoming DSbase+ESI+8 at both callbacks',flags_publication='After write callback',source_GPR_or_segment_mutation_before_callback=False))
    contract=dict(schema='mw34.constructor.store_callback_timing.v1',checked_forms=selected,scope='Exact four bounded frozen host-IR forms; source arithmetic and callback-state relation only, compiled callback artifact correspondence requires its own build/review',descriptor_receipt_sha256=sha(ROOT/'reports/m4-constructor-native/store-operands-r1/report.json'),guard_valid_at_checked_callback_forms=True,source_PC_publication='Physical PC is published from NEXT_PC before each checked instruction; CALL target is published after its write callback',prior_read_integration='All actual constructor literal read scalars retained independently before owner early-return; private same-root monotonically numbered last-access provenance, invalidated by every store and scope transition',full_State_observer_mutation=False,optimized_machine_callback_order_claim=False,complete_all_store_IR_timing_claim=False,cold_recursive_frontier=0x56fea0,frontier_unadmitted=True,native_executed=False,source_AFTER_seed=False,initializer_credit=0)
    path=out/'timing-contracts.json';path.write_text(json.dumps(contract,indent=2)+'\n');pin(path)
    integration=out/'integration.inc';integration.write_text(INTEGRATION);pin(integration)
    pin(__file__)
    for p,h in list(pins.items()):pin(p,h)
    report=dict(passed=True,scope='Bounded source-only PUSH/CALL/MOV/ADD current host-IR callback timing and exact private prior-read integration suggestion. No parent Component/service mutation, compiler, worker or capture.',checked_form_count=4,operand_receipt_sha256='56acaf9dffcf68355d6a68bcd28ef841e084208e9f10724a8a14d3d06ed63d33',timing_contracts=str(path.resolve()),timing_contracts_sha256=sha(path),integration_suggestion=str(integration.resolve()),integration_suggestion_sha256=sha(integration),native_executed=False,compiler_executed=False,capture_reader_opened=False,payload_reader_opened=False,initializer_credit=0,files=pins)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(p),timing_contracts_sha256=sha(path),integration_sha256=sha(integration))))

if __name__=='__main__':main(sys.argv[1])
