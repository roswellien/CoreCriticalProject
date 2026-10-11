"""Use each actual entry Native BEFORE page for absent fixed memory regions.

The failed v1/v2 checkers remain unchanged. The current mode's complete entry
snapshot supplies its lower source stack; no refused AFTER or prior mode is an
input to the literal accepted-prefix derivation.
"""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
parent=ROOT/'tools/m4-mfc1168-native/verify_connected_controls.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='ac244486d396a637d059c3e421f84e88f0504aee92bb3105b022f31c3fd6d850'
text=parent.read_text().replace("1:'Flat32'","1:'source segment/entry identity'").replace("12:'Flat32'","12:'source segment/entry identity'")
old="      # Fill absent code/IAT inputs only from the fixed physical source image;"
new="""      entry_native=a.data(prefix+'entry/Native.bin');eq(len(entry_native),159716,'Whole actual own entry Native BEFORE snapshot')
      fixed_pages=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
      for i,address in enumerate(fixed_pages):memory.setdefault(address,entry_native[2276+4096*i:2276+4096*(i+1)])
      # Fill absent code/IAT inputs only from the fixed physical source image;"""
assert text.count(old)==1;text=text.replace(old,new)
old="      if mode==7:need(source_prefix and source_prefix[-1][1:]==(0x33005014,0,1,1),'Actual last attempted byte14 RO write');counts['recorded_rejected_source_write_payloads']+=1"
new=old+"\n      eq(memory[p['inputs']['guest_CS']],a.data(prefix+'refused/guestCS24.bin'),'Whole borrowed guest CS24 unchanged: no semantic write committed before these refusals');counts['whole_borrowed_guestCS24_prefixes']+=1"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('pin(__file__);pin(sys.executable)',"pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py');pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls.py');pin(sys.executable)")
# These transformations add equality-target copies after every semantic
# predicate has run, before the same strict canonical reader is closed.
old="counts=collections.Counter();cases=[];proofs={};identities=[]"
new=old+";raw_exports=[]"
assert text.count(old)==1;text=text.replace(old,new)
old="  MF=load(ROOT/'tools/m4-joint-startup131/mfc_source.py','mfc_causal_control_literal_adapter');"
new="  X=load(ROOT/'tools/m4-joint-startup131/paired_exports.py','mfc_control_raw_exports');"+old.strip()
assert text.count(old)==1;text=text.replace(old,new)
old="a=DS.DirectSet(row['capture'],pin);closed=False"
new=old+";export=X.Export(out/'raw-controls',level,a.path,pin)"
assert text.count(old)==1;text=text.replace(old,new)
old="   finally:a.close();a.entries.clear();a.bundles.clear();del a;closed=True"
new="""    for key in sorted(a.entries):export.write(key,a.data(key))
    raw_exports.append(export.finish())
   finally:export.close();a.close();a.entries.clear();a.bundles.clear();del a;closed=True"""
assert text.count(old)==1;text=text.replace(old,new)
old="dict(passed=passed,execution=str(execution),execution_sha256=digest,scope="
new="dict(passed=passed,raw_exports=raw_exports,raw_exports_all_logical_entries=True,raw_export_readers_closed=closed,execution=str(execution),execution_sha256=digest,scope="
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py');", "pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v4.py');pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py');")
# The observed zero-manager-cell control reaches the source TLS call with
# argument zero. It is refused by the existing exact index3 service guard,
# before any source API record; all poison/retry/lifetime predicates stay.
old="11:'causal connected source'"
new="11:'Typed guest TLS index3/borrowed CS24 argument'"
assert text.count(old)==1;text=text.replace(old,new)
old="source_prefix=[];API_count=0;owned_byteflows=[]"
assert text.count(old)==1;text=text.replace(old,old+";source_refusal_API_provenance=None")
old="       eq(source_prefix,m.accesses[:len(source_prefix)],'Literal mutated manager lazy-path accepted source prefix');eq(API_count,0,'No typed API admitted on unproved lazy path')"
new="""       eq(source_prefix,m.accesses[:len(source_prefix)],'Literal zero TLS-index cell accepted source prefix');eq(API_count,0,'No typed API admitted with source argument zero')
       need(m.cursor==p['inputs']['imports'][3]['projected']and m.call_stack and m.call_stack[-1][2]==0x5f401018,'Literal refused first TLS API target/return')
       frame=m.reg('esp');frame64=m.bytes(frame,64);eq(struct.unpack_from('<2I',frame64),(0x5f401018,0),'Literal committed TLS return and source zero argument')
       eq(struct.unpack_from('<I',memory[0x5f4cb000],8)[0],0,'Actual authored zero TLS-index BEFORE cell')
       need(source_prefix[-4][0:2]==(0x5f401010,0x5f4cb008)and source_prefix[-4][2:]==(0,4,0)and source_prefix[-3][0]==0x5f401010 and source_prefix[-3][2:]==(0,4,1),'Actual accepted source zero-index read and push')
       lower=a.data(stem+'retry-before/memory-536875008-4096.bin');eq(len(lower),4096,'Whole actual refused source lower-stack target')
       eq(frame64,lower[frame-0x20001000:frame-0x20001000+64],'Whole independently source-derived refused TLS call frame')
       source_refusal_API_provenance=dict(source_target=m.cursor,return_PC=0x5f401018,frame=frame,source_frame64_hex=frame64.hex(),source_argument=0,admitted_argument=3,actual_source_API_records=0,source_API_entered=False,source_read_and_push_indices=[len(source_prefix)-4,len(source_prefix)-3],scope='Literal source-derived committed zero argument and actual refused stack equality; exact typed index3 guard refuses before source API record')"""
assert text.count(old)==1;text=text.replace(old,new)
old="cases.append(dict(level=level,mode=mode,terminal=list(terminal),"
new="cases.append(dict(level=level,mode=mode,source_refusal_API_provenance=source_refusal_API_provenance,terminal=list(terminal),"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v4.py');", "pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v5.py');pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v4.py');")
exec(compile(text,str(parent),'exec'),globals())
