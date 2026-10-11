"""Focused actual formatter controls; canonical readers are coordinated."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check_controls_v3 import hardware

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def need(v, s):
    if not v: raise ValueError(s)

def main(execution, digest, name):
    out = R/'reports/m4-tree-review'/name
    need(not out.exists(), 'Fresh focused formatter controls validation'); out.mkdir(parents=True)
    pins = {}; counts = Counter(); causes = []; passed = False
    def pin(p, h=None):
        p = Path(p).resolve(); a = pins.get(str(p)) or sha(p)
        need(h is None or a == h, 'Exact current physical input ' + str(p)); pins[str(p)] = a; return p
    def read(p, h=None): return json.loads(pin(p, h).read_bytes())
    def rows(a, p, fmt):
        b = a.data(p); need(len(b)%struct.calcsize(fmt)==0, 'Whole actual typed row '+p)
        return list(struct.iter_unpack(fmt, b))
    try:
        e = read(execution, digest); need(e['passed'], 'Both actual writer workers passed')
        b = read(e['build_path'], e['build_sha256']); p = read(b['preparation'], b['preparation_sha256'])
        need(b['passed'] and p['control_scenarios']==14 and p['control_attempts']==28 and p['actual_Runtime_selected_call'], 'Actual registered three-root fixture')
        need(e['native_preparation_sha256']==b['native_preparation_sha256']==p['native_preparation_sha256']=='bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa', 'Frozen native15 with real generic malloc kind1')
        n=read(p['native_preparation'],p['native_preparation_sha256']); need(n['passed'], 'Frozen native15 preparation')
        for q,h in b['sources'].items(): pin(q,h)
        for q,h in n['files'].items():
            if Path(q).parent==Path(p['native_preparation']).parent: pin(q,h)
        pin(__file__); pin(R/'tools/m4-tree-review/check_controls_v3.py')
        direct=pin(R/'tools/m4-crt-allocation-root/run_v2.py'); spec=importlib.util.spec_from_file_location('format_controls_reader', direct); D=importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
        for f in ('capture_bundle.py','paths.py','stages.py','manifests.py'): pin(R/'tools/m4-pipeline'/f)
        for level in ('O0','O2'):
            w=e['workers'][level]; need(w['exit_code']==0,'Actual worker status'); pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
            a=D.DirectSet(pin(w['transport'],w['transport_sha256']),pin)
            try:
                need(a.words('header.bin',9)==(1,14,28,9968,0x4df610,3504,40,512,70),'Whole immutable full caller/machine/current-page ABI')
                need(a.data('COMPLETE.txt').startswith(b'Bounded actual Runtime formatter controls passed'),'Actual completion record')
                for case in range(14):
                    first=None
                    for retry in (0,1):
                        root=f'case-{case}/'+('retry/' if retry else 'first/'); sample=a.data(root+'sample.bin'); need(len(sample)==9968,'Full actual sample')
                        tags=struct.unpack_from('<32Q',sample); before=struct.unpack_from('<32Q',sample,256); after=struct.unpack_from('<32Q',sample,512)
                        need(tags[:3]==(1,case,retry) and tags[5]==tags[9]==1 and tags[6]==0x4d573354 and not((tags[7]^tags[8])&0x400),'Actual case/cleanup/caller LastError/DF')
                        need(not any(after[i] for i in (10,11,15)), 'No live native allocation/CS/heap after cleanup')
                        hardware(sample[8880:9424],sample[9424:9968],True); hardware(a.data(root+'actual-cleanup-hardware-before.bin'),a.data(root+'actual-cleanup-hardware-after.bin'))
                        counts['rich_caller_architectural_hardware_pairs']+=1; counts['cleanup_architectural_hardware_pairs']+=1
                        for label,z in (('State',3504),('CPU',40),('FX',512),('guest-ENV',28)):
                            need(len(a.data(root+'actual-causal-'+label+'.bin'))==z,'Whole causal machine '+label)
                        live=root+'actual-live/'; clean=root+'actual-cleaned/'
                        if retry:
                            need(not tags[3] and not tags[4] and before==after,'Same cleaned Session refuses without progress')
                            need(sample[768:4272]==sample[4272:7776] and sample[7776:8288]==sample[8288:8800] and sample[8800:8840]==sample[8840:8880], 'Whole State3504/FX512/CPU40 unchanged retry')
                            need(first[4272:7776]==sample[768:4272] and first[8288:8800]==sample[7776:8288] and first[8840:8880]==sample[8800:8840], 'Exact first-cleaned machine carries into retry without seed')
                            old=f'case-{case}/first/actual-cleaned/'
                            suffixes=('locale-source-accesses.bin','locale-api-transports.bin','locale-call-frames.bin','locale-summary.bin','locale-allocations.bin','locale-critical-sections.bin','registry-exception-message.bin','formatting-status.bin','formatting-calls.bin','formatting-owned.bin','formatting-publications.bin','formatting-dispatches.bin','current-page-addresses.bin')
                            for suffix in suffixes:
                                need(a.data(old+suffix)==a.data(live+suffix)==a.data(clean+suffix),'Whole actual retry history '+suffix); counts['whole_retry_history_joins']+=2
                            pages=a.words(old+'current-page-addresses.bin',70)
                            need(tuple(pages)==tuple(p['current_pages']), 'Physical declared current-page identity')
                            for page in pages:
                                suffix='current-page-'+str(page)+'.bin'; need(len(a.data(old+suffix))==4096 and a.data(old+suffix)==a.data(live+suffix)==a.data(clean+suffix),'Whole current-page retry conservation'); counts['whole_retry_page_joins']+=2
                            counts['same_session_refusals']+=1; continue
                        first=sample; allocs=rows(a,live+'locale-allocations.bin','<16Q'); accesses=rows(a,live+'locale-source-accesses.bin','<2IQ2I')
                        # Whole current formatter backing is derived from its own
                        # actual allocation initial bytes and committed source stores.
                        formatter=set(r[4] for r in rows(a,live+'formatting-publications.bin','<12Q'))
                        formatter.update(r[8] for r in rows(a,live+'formatting-owned.bin','<12Q'))
                        for o in allocs:
                            if o[1] not in formatter or not o[9]: continue
                            need(o[6]==1 and o[2] in (8,10,12) and o[3]==16 and o[4]==4096 and o[8] and o[5], 'Real live generic malloc kind1/request/rounded16/current generation')
                            stem=live+f'locale-allocation-{o[5]}'; initial=a.data(stem+'-initial.bin'); need(len(initial)==16,'Whole genuine native initial16')
                            want=bytearray(initial+bytes(4096-16))
                            for pc,address,value,width,writing in accesses:
                                if writing and o[1]<=address<o[1]+4096:
                                    need(pc in (0x7801042a,0x78022bd5) and address+width<=o[1]+o[2], 'Only genuine literal stores within source request')
                                    want[address-o[1]:address-o[1]+width]=value.to_bytes(width,'little'); counts['source_owner_stores']+=1
                            need(bytes(want)==a.data(stem+'-expected.bin')==a.data(stem+'-owned-page.bin'), 'Whole actual guest owner page reconstructed solely from native initial/source stores')
                            need(bytes(want[:16])==a.data(live+f'native-full-{o[5]}.bin') and want[o[2]:16]==initial[o[2]:16], 'Whole genuine native backing/current page/tail relation'); counts['whole_owner_backing_byteflows']+=1
                        if case==0:
                            need(tags[3]==1 and tags[4]==3 and not any(tags[k] for k in (10,11,12,13)), 'Actual registered positive three-root closure')
                            need(a.words(live+'formatting-status.bin',10)==(1,0,3,0,0,0,0,0,0,0) if False else a.words(live+'formatting-status.bin',10)[1:3]==(0,3), 'Three completed finite formatter roots')
                            need(len(rows(a,live+'formatting-calls.bin','<16Q'))==9 and len(rows(a,live+'formatting-owned.bin','<12Q'))==33 and len(rows(a,live+'formatting-publications.bin','<12Q'))==3 and len(rows(a,live+'formatting-dispatches.bin','<8Q'))==12,'Complete actual call/owner/publication/dispatch positive extents')
                            counts['registered_positive_roots']+=3; continue
                        need(not tags[3] and not tags[4] and tags[12]==tags[13]==tags[14]==tags[15]==1, 'One actual intervention refused before root completion')
                        trig=root+'trigger/'; identity=a.words(trig+'identity.bin',4); need(identity[2:]==(1,1), 'One actual trigger/intervention')
                        v=a.words(trig+'intervention.bin',16,'Q'); fault=a.words(live+'locale-fault.bin',4); reason=a.data(live+'locale-fault-reason.bin').decode()
                        need(fault[0]==1 and reason and a.data(live+'registry-exception-message.bin').decode()==reason,'Precise first native predicate retained')
                        if case<=4:
                            need(identity[:2]==(90,0x7801042a) and v[0]==1 and v[5] and v[6] and v[7:10]==(case,0x7801042a,1), 'True MOV [EDX],AL source operand counterfactual')
                            target=next((o for o in rows(a,trig+'locale-allocations.bin','<16Q') if o[1]<=v[2]<o[1]+o[4]),None)
                            current=next(o for o in rows(a,trig+'locale-allocations.bin','<16Q') if o[1]==v[5]); need(current[6]==1 and current[2]==8 and current[3]==16 and current[5]==v[6], 'Actual first source malloc current generation')
                            if target:
                                need(a.data(trig+f'locale-allocation-{target[5]}-owned-page.bin')==a.data(live+f'locale-allocation-{target[5]}-owned-page.bin'),'Entire counterfactual target unchanged before denied commit')
                            if case==1: need(target and target[1]!=current[1], 'Foreign actual live generic allocation')
                            if case==2: need(target and target[1]==current[1] and v[2]-current[1]==8, 'Requested tail lies inside genuine physical capacity16')
                            if case==3: need(target is None, 'Actual unmapped successor is no admitted owner')
                            if case==4: need(target and target[1]==current[1] and v[2]==current[1]+1 and v[3]==((v[4]&255)^0x80), 'Ordered valid cell receives wrong literal AL value')
                            need(reason.startswith('Formatter ') and 'observer changed' not in reason and fault[1]==0x7801042a and fault[2]==v[2], 'Genuine source owner admission is first reason'); counts['public_source_operand_denials']+=1
                        elif case<=8:
                            old=a.data(trig+'private-before.bin'); new=a.data(trig+'private-after.bin')
                            need(v[0]==2 and v[1]<len(old)==len(new)==v[2] and sum((x^y).bit_count() for x,y in zip(old,new))==1,'Exactly one actual private witness bit changed')
                            need(reason=='Formatter observer changed private invocation or source owner witnesses','Private witness conservation first predicate'); counts['private_witness_denials']+=1
                        elif case==9:
                            need(identity[:2]==(89,0x7800fcef) and v[0]==7 and v[2]==2 and v[3]==0x78010402 and reason=='Formatter exact narrow table branch and current source index', 'Actual source dispatch index/table reentry denial'); counts['public_dispatch_denials']+=1
                        else:
                            need(v[0] in (4,5,6), 'Actual IAT/permission/FX/suffix intervention')
                            if case==10: need(v[0]==4 and v[1]==0x5bb658 and v[3]==(v[2]^4), 'Actual source IAT DWORD bit')
                            if case==11: need(v[0]==6 and v[2]==current[1] if False else v[0]==6 and v[1]==(v[2]&~4095), 'Actual owner page read-only intervention')
                            if case==12: need(v[:3]==(5,0,512), 'Whole actual RuntimeFX byte intervention')
                            if case==13: need(v[0]==4 and v[3]==(v[2]^1), 'Actual retained source cdecl suffix bit')
                            counts['source_IAT_permission_FX_frame_denials']+=1
                        causes.append(dict(level=level,scenario=case,hook_point=identity[0],State_PC=identity[1],fault_PC=fault[1],fault_address=fault[2],reason=reason,intervention=list(v),public_source_service=case<=4 or case==9))
                        counts['causal_denials']+=1; print(json.dumps(causes[-1]),flush=True)
                counts['levels']+=1
            finally: a.close()
        need(counts['causal_denials']==26 and counts['same_session_refusals']==28 and counts['registered_positive_roots']==6,'Complete both levels and all current cases/retries')
        for q,h in pins.items(): need(sha(q)==h,'Final unchanged physical input '+q)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        (out/'actual-causes.json').write_text(json.dumps(causes,indent=2)+'\n')
        report=dict(passed=passed,scope='Focused actual registered formatter3 controls: public source admission, private observer integrity, exact whole backing and same-session State/CPU/FX/history conservation',execution_sha256=digest,build_sha256=e['build_sha256'] if 'e' in locals() else None,native_preparation_sha256=e['native_preparation_sha256'] if 'e' in locals() else None,counts=dict(counts),reader_closed=True,full_caller_FX512_equality_claim=False,whole_guest_State_retry=True,whole_guest_CPU_retry=True,whole_guest_FX_retry=True,initializer_credit=0,files=pins)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__': main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
