"""Additive static caller-frame and defined FNCLEX domain clarification.

Consumes only the frozen independent source dossier; runs no machine code.
"""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv'
OUT=BASE/'independent-static-continuation-r1';PINS={}
def need(x,why):
    if not x:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();got=sha(p);need(h is None or h==got,'Frozen identity '+str(p));PINS[str(p)]=got;return p
def read(p,h=None):return json.loads(pin(p,h).read_text())
def main():
    need(not OUT.exists(),'Fresh additive continuation dossier');OUT.mkdir(parents=True)
    (OUT/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(OUT/'review-source.py');pin(Path(__file__));pin(sys.executable)
    try:
        r=read(BASE/'independent-static-scope-r1/report.json','c2be15964692046e118a8be890ac0bee140988aa356e401024d5141718aa138c')
        p=read(BASE/'independent-static-scope-r1/pins.json','465e5a40bee7a1aae08c5d04477e00501f984a01387dc43c16e0d3ca9fa431dd')
        for path,h in p['files'].items():pin(path,h)
        m=read(r['model_path'],r['model_sha256']);rows={x['address']:x for g in m['graphs'] for x in g['instructions']}
        # Follow the actual argument/frame prefix from writer entry W to the
        # reached local whose high half survives the 16-bit FNSTCW store.
        sp=0;ebp=None;trace=[];local=None;copy=None
        for pc in (0x78004263,0x780042cf,0x780042d4,0x780042d9,0x780042e1,0x780042e5,0x780042ea,0x780042eb,0x780042ef,0x780042f7,0x780042f8,0x780042fa,0x780042fb,0x780042fc,0x780042fd,0x78004300):
            x=rows[pc];op=x['mnemonic'];before=sp
            if op in ('call','push'):sp-=4
            if pc==0x780042f8:
                need(x['operands']=='ebp, esp','Exact frame base');ebp=sp
            if pc==0x780042fa:need(x['operands']=='ecx','Actual post-query volatile source');local=sp
            if pc==0x780042fd:
                need(x['mnemonic']=='fnstcw' and x['operands']=='word ptr [ebp - 0x4]' and ebp-4==local,'Actual 16-bit store leaves high ECX half')
            if pc==0x78004300:need(x['operands']=='dword ptr [ebp - 0x4]','Actual whole DWORD copy');copy=sp
            trace.append(dict(pc=pc,operation=op,operands=x['operands'],SP_before_W_offset=before,SP_after_W_offset=sp,EBP_W_offset=ebp))
        need(local==-36 and copy==-44,'Two exact residual DWORD source slots')
        stores=[x for x in rows.values() if x['mnemonic']=='mov' and x['operands'].startswith('dword ptr [ebp')]
        need(len(stores)==1 and stores[0]['address']==0x78004320 and stores[0]['operands']=='dword ptr [ebp + 0xc], eax' and ebp+12==-20,'Only later control local MOV is distinct from residual slots')
        for pc,wanted in ((0x780042de,'ecx'),(0x780042df,'ecx')):need(rows[pc]['mnemonic']=='pop' and rows[pc]['operands']==wanted,'Final wrapper restores known argument DWORDs into ECX')
        need(rows[0x780043d7]['mnemonic']=='mov' and rows[0x780043d7]['operands']=='edx, 0x300','Final EDX value defined by raw-CW helper')
        need(rows[0x78004402]['mnemonic']=='test' and rows[0x78004402]['operands']=='ebx, 0x40000','Final integer arithmetic flags defined except logical AF')
        # Architectural relation deliberately permits every C0/C1/C2/C3 value.
        # Repeated software checks are domain-model checks, not hardware trials.
        clear=0x80ff;cc=0x4700;top=0x3800
        def relation(before,after):return not after&clear and (before&top)==(after&top)
        reps=0
        for sw in range(65536):
            preserved=sw&~clear;zero_cc=preserved&~cc
            need(relation(sw,preserved) and relation(sw,zero_cc),'Defined FNCLEX domain admits distinct condition representatives')
            reps+=2
        reject=0
        for bit in (0,1,2,3,4,5,6,7,15,11,12,13):
            before=0x3800;after=(before&~clear)^(1<<bit)
            need(not relation(before,after),'Defined clear/TOP corruption rejected');reject+=1
        report=dict(passed=True,scope='Additive read-only reached service volatility/frame and FNCLEX defined-status model; no execution proof',consumed_static_report_sha256=sha(BASE/'independent-static-scope-r1/report.json'),trace=trace,post_query_ECX_consumed_by_partial_local_store=True,writer_entry_SP_symbol='W',residual_unportable_halfword_intervals=[[-34,-32],[-42,-40]],residual_source_DWORD_offsets=[-36,-44],unknown_source='High16 of ECX after dynamically resolved API query, or after missing named-API lookup on fallback path. API ABI leaves ECX unspecified. Following FNSTCW writes only the low16 then copies the whole DWORD.',residual_condition='Relevant when control87 executes successfully after the queried/fallback probe. Later helpers push below these slots; the only ordinary local MOV writes W-20. No portable equality of these two high halfwords follows.',known_final_GPRs=dict(ECX=0x30000,EDX=0x300,EAX='Decode(CW_before) with abstract precision mask0x30000 replaced by0x10000'),integer_flag_domain=dict(defined_mask=0x8c5,final_CF=0,final_OF=0,final_SF=0,final_PF=1,final_ZF='1 if modified abstract CW lacks0x40000, otherwise0',AF='undefined by final TEST; native representative must be explicit'),FNCLEX=dict(defined_SW_clear_mask=clear,condition_mask_undefined=cc,TOP_mask_preserved=top,representative_domain_checks=reps,cause_specific_defined_field_rejections=reject,CW_TAG_raw80_legacy_MXCSR='Unchanged by FNCLEX only; prior fallback/control/services have separate effects and dead raw80 storage remains observation-only',hardware_execution=False),needed_native_measurements=['Record actual original query/lookup volatile observations and API target/module/export association.','Independently define the native service guest-register representative; preserve native full State/page captures.','Do not force original/native equality for residual post-service ECX high halves. If original reference broker returns a specific authored ECX, identify that fixture rather than widening portable API credit.','Separate architecture-defined FNCLEX clears/TOP retention from observed raw C0/C1/C2/C3 and dead raw80 retention.','Prove actual guest CALL/RET/stdcall cleanup; no API success invented.'],original_or_native_execution=False,full_process_attach=False,full_CRT=False,full_startup=False,whole_M4_complete=False)
        q=OUT/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q)
        for path,h in PINS.items():need(sha(path)==h,'Final unchanged physical association '+path)
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(PINS),report_sha256=sha(q),pins_sha256=sha(OUT/'pins.json'))))
    except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
