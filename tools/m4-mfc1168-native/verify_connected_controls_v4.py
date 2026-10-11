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
exec(compile(text,str(parent),'exec'),globals())
