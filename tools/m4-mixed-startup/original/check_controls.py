"""Causal raw observer denials and actual original pre-entry identity guards."""
from pathlib import Path
import copy,json,struct,subprocess,sys
sys.dont_write_bytecode=True
from observe import inspect,fields as original_fields
from compare_native import (sha,configure,native_fields,native_checks,architectural_pair,
                           ORIGINAL_SIZE,NATIVE_SIZE,STATE0,STATE1,COUNTS,EVENTS,ROUTES)
ROOT=Path(__file__).resolve().parents[3]
def changed(b,offset,value=None):
    r=bytearray(b);r[offset]=r[offset]^1 if value is None else value;return bytes(r)
def main():
    original_build,native_build,original_path,out=map(lambda p:Path(p).resolve(),sys.argv[1:5])
    assert out.parent==ROOT/'reports/m4-mixed-startup' and out.name.startswith('original-') and not out.exists();out.mkdir()
    ob=json.loads(original_build.read_text(encoding='utf-8-sig'));nb=json.loads(native_build.read_text());assert ob['passed'] and nb['passed']
    extraction_path=Path(ob['extraction'])/'extraction.json';extraction=json.loads(extraction_path.read_text());configure(extraction)
    static_path=ROOT/'reports/m4-startup/next-initializer-410940-events/report.json';static_events=json.loads(static_path.read_text())['memory_events']
    raw=bytearray(original_path.read_bytes());assert inspect(raw,extraction)['passed']
    # Every mutation is restored before the next case. Failed streams are in
    # memory only; authoritative output/captures are never changed.
    original_cases=[]
    offsets=[('header_extent',12),('table_order',32+12),('entry_PC',32+36+36),('return_PC',32+76+36),('return_ESP',32+76+16),
      ('status_fault',32+28),('host_tag_restoration',32+32),('host_MXCSR',32+1652+24),('host_x87_storage',32+1652+32),
      ('host_XMM',32+1652+160),('host_legacy_ENV',32+2248+12),('CPU_carry',32+ORIGINAL_SIZE+36),
      ('flags_carry',32+ORIGINAL_SIZE+36+32),('hardware_FX_carry',32+ORIGINAL_SIZE+116+32),('legacy_ENV_carry',32+ORIGINAL_SIZE+2164+12),
      ('whole_page_carry',32+ORIGINAL_SIZE+2276+10*4096+0x7fc),('CW_domain',32+116),('TOP_domain',32+116+3),
      ('protected_constant',32+2276),('fresh_RW_page',32+2276+7*4096+0x10),('fresh_authored_stack',32+2276+10*4096+1),
      ('repeat_guest_result',32+24*26*ORIGINAL_SIZE+76)]
    for name,offset in offsets:
        old=raw[offset];raw[offset]^=1;rejected=False;reason=''
        try:inspect(raw,extraction)
        except ValueError as e:rejected=True;reason=str(e)
        finally:raw[offset]=old
        assert rejected,name
        original_cases.append({'case':name,'rejected':True,'reason':reason})
    native_results={}
    for level in ('O0','O2'):
        path=native_build.parent/('native-'+level+'.bin');nr=path.read_bytes()
        os=[original_fields(raw[32+i*ORIGINAL_SIZE:32+(i+1)*ORIGINAL_SIZE]) for i in range(26)]
        ns=[native_fields(nr[32+i*NATIVE_SIZE:32+(i+1)*NATIVE_SIZE]) for i in range(26)]
        def errors(i,n,previous=None):return architectural_pair(os[i],n,i)+native_checks(os[i],n,ns[i-1] if previous is None and i else previous,extraction,static_events)
        for i,n in enumerate(ns):assert not errors(i,n),str((i,errors(i,n)))
        cases=[]
        def reject(name,i,mutate,expected):
            n=copy.deepcopy(ns[i]);previous=copy.deepcopy(ns[i-1]) if i else None;mutate(n,previous);found=errors(i,n,previous)
            assert expected in found,(name,found)
            cases.append({'case':name,'rejected':True,'required_field':expected,'observed_fields':list(dict.fromkeys(found))})
        reject('opaque_State_after_protection',0,lambda n,p:n.update(state1=changed(n['state1'],7)),'full_State_actual_defined_writes_and_protection')
        reject('opaque_State_initial_seed',0,lambda n,p:n.update(state0=changed(n['state0'],7)),'full_State_entry_carry_or_seed')
        reject('opaque_State_cross_phase_carry',3,lambda n,p:n.update(state0=changed(n['state0'],7)),'full_State_entry_carry_or_seed')
        reject('upper_GPR_protection',2,lambda n,p:n.update(state1=changed(n['state1'],2220)),'full_State_actual_defined_writes_and_protection')
        reject('legacy_metadata_State_carry',3,lambda n,p:n.update(state0=changed(n['state0'],2776)),'full_State_entry_carry_or_seed')
        reject('legacy_metadata_State_exit',3,lambda n,p:n.update(state1=changed(n['state1'],2776)),'full_State_actual_defined_writes_and_protection')
        reject('FPU_sticky_State_protection_in_integer',3,lambda n,p:n.update(state1=changed(n['state1'],2745)),'full_State_actual_defined_writes_and_protection')
        reject('FP_dead_storage_not_globally_masked',2,lambda n,p:n.update(fx1=changed(n['fx1'],32)),'observed_dead_raw80_1_0')
        reject('FP_condition_bits_not_globally_masked',2,lambda n,p:n.update(fx1=changed(n['fx1'],3)),'observed_C0_C2_C3'+'1')
        # C1 is bit9, byte3 bit1; use an explicit mutation rather than bit0 C0.
        reject('FP_C1_observation',2,lambda n,p:n.update(fx1=n['fx1'][:3]+bytes([n['fx1'][3]^2])+n['fx1'][4:]),'observed_C1'+'1')
        reject('legacy_ENV_after',2,lambda n,p:n.update(env1=changed(n['env1'],12)),'legacy_ENV1')
        reject('native_CPU_carry',3,lambda n,p:p.update(after=tuple([p['after'][0]^1]+list(p['after'][1:]))),'native_CPU_carry')
        reject('native_whole_page_carry',3,lambda n,p:p.update(memory1=changed(p['memory1'],0x10)),'native_whole_page_carry')
        reject('native_FP_carry',3,lambda n,p:p.update(fx1=changed(p['fx1'],32)),'native_software_FP_carry')
        reject('native_ENV_carry',3,lambda n,p:p.update(env1=changed(p['env1'],12)),'native_legacy_ENV_carry')
        reject('table_order_absolute_slot',3,lambda n,p:n.update(tag=n['tag'][:3]+(n['tag'][3]+4,)+n['tag'][4:]),'tag')
        reject('RET_frame_PC',2,lambda n,p:n.update(after=n['after'][:9]+(0x10000100,)),'CPU_after')
        reject('RET_frame_ESP',2,lambda n,p:n.update(after=n['after'][:4]+(n['after'][4]+4,)+n['after'][5:]),'CPU_after')
        reject('bridge_counts',2,lambda n,p:n.update(counts=(n['counts'][0]+1,)+n['counts'][1:]),'typed_bridge_counts')
        reject('wrong_ordered_access',2,lambda n,p:n['events'].__setitem__(0,(n['events'][0][0]+4,)+n['events'][0][1:]),'exact_ordered_events')
        reject('wrong_checked_value',2,lambda n,p:n['events'].__setitem__(0,(n['events'][0][0],n['events'][0][1]^1)+n['events'][0][2:]),'exact_ordered_events')
        reject('unused_event_storage',2,lambda n,p:n['events'].__setitem__(191,(1,0,0,0)),'inactive_event_storage')
        reject('helper_RET12_route',1,lambda n,p:n['routes'].__setitem__(0,changed(n['routes'][0],8)),'exact_compiled_call_RET_routes')
        reject('helper_RET20_route',1,lambda n,p:n['routes'].__setitem__(1,changed(n['routes'][1],8)),'exact_compiled_call_RET_routes')
        reject('tail_route',3,lambda n,p:n['routes'].__setitem__(0,changed(n['routes'][0],0)),'exact_compiled_call_RET_routes')
        reject('inactive_route_storage',2,lambda n,p:n['routes'].__setitem__(1,changed(n['routes'][1],0)),'exact_compiled_call_RET_routes')
        reject('int_to_FILD_input',20,lambda n,p:n['events'].__setitem__(0,(0x60b44c,0,4,0)),'integer_to_FILD_dependency')
        reject('int_to_FILD_writer',20,lambda n,p:p.update(memory1=changed(p['memory1'],9*4096+0x44c)),'integer_to_FILD_dependency')
        reject('host_XMM15_restore',2,lambda n,p:n.update(host1=changed(n['host1'],160+15*16)),'native_host_restore')
        # Positive undefined-AF exclusion: this concrete State/call projection
        # may differ consistently at the XOR boundary without defined credit.
        n=copy.deepcopy(ns[3]);n['after']=n['after'][:8]+(n['after'][8]^16,)+n['after'][9:];n['state1']=changed(n['state1'],2069)
        n['routes'][0]=changed(n['routes'][0],88,value=n['routes'][0][88]^16)
        assert not errors(3,n),errors(3,n)
        native_results[level]={'positive_phase_checks':26,'negative_checks':len(cases),'positive_undefined_AF_exclusion':1,'cases':cases}
    worker,pack,image=map(Path,(ob['worker'],ob['pack'],ob['image']))
    for p in (worker,pack,image):assert sha(p)==ob['bindings'][str(p)]
    identity=[]
    for name,which,reason in [('changed_pack','pack','Pack identity rejected'),('changed_image','image','Image identity rejected')]:
        input_path=out/(name+'.bin');source=pack if which=='pack' else image;bytes_=bytearray(source.read_bytes());bytes_[-1]^=1;input_path.write_bytes(bytes_)
        output=out/(name+'-result.bin');command=[str(worker),str(input_path if which=='pack' else pack),str(input_path if which=='image' else image),str(output)]
        run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=190);(out/(name+'.stdout.log')).write_bytes(run.stdout);(out/(name+'.stderr.log')).write_bytes(run.stderr)
        assert run.returncode==1 and reason.encode() in run.stderr and not output.exists() and not list(out.glob(output.name+'.mixed-stage-*'))
        identity.append({'case':name,'command':command,'exit_code':1,'diagnostic':reason,'no_output_or_stage':True})
    result={'passed':True,'original_observer_negative_checks':len(original_cases),'original_cases':original_cases,'native_controls':native_results,'actual_identity_controls':identity,
            'scope':'Causal in-memory capture corruptions plus actual hash-identity guards before any original guest instruction; authoritative streams unchanged',
            'bindings':{str(p):sha(p) for p in (Path(__file__),Path(__file__).with_name('observe.py'),Path(__file__).with_name('compare_native.py'),original_build,native_build,original_path,extraction_path,static_path,worker,pack,image)}}
    for p in out.rglob('*'):
        if p.is_file():result['bindings'][str(p)]=sha(p)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'original_mutations':len(original_cases),'native_negative_each_level':len(cases),'native_positive_each_level':27,'actual_identity_denials':len(identity)}))
if __name__=='__main__':main()
