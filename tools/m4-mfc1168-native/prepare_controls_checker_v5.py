"""Bind the genuine zero-TLS-index refusal and literal call-frame provenance."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=R/'tools/m4-mfc1168-native/verify_connected_controls_v4.py'
assert sha(p)=='302faa03b05b2a284d8b0073bb77c011ac78f1dae9d3846090ecd8ac7f70bf82'
text=p.read_text();needle="exec(compile(text,str(parent),'exec'),globals())"
extra=r'''# The observed zero-manager-cell control reaches the source TLS call with
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
exec(compile(text,str(parent),'exec'),globals())'''
assert text.count(needle)==1;text=text.replace(needle,extra)
target=p.with_name('verify_connected_controls_v5.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-mfc1168-native/connected-controls-checker-preparation-r5';assert not out.exists();out.mkdir()
paths=[p,target,Path(__file__),R/'reports/m4-mfc1168-native/connected-controls-verification-r4/report.json',R/'reports/m4-mfc1168-native/connected-controls-mode11-diagnostic-r2/report.json',R/'reports/m4-mfc1168-native/connected-controls-mode11-diagnostic-r2/mode11-observations.json']
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,parent=str(p.resolve()),parent_sha256=sha(p),checker=str(target.resolve()),checker_sha256=sha(target),scope='One exact observed mode11 reason correction plus literal zero-index read/push and full64B actual refused stack join; original24 poison/retry/lifetime/source/capacity predicates unchanged',actual_workers_rerun=False,strict_refusal_retry_predicates_changed=False,raw_export_schema_changed=False,files={str(x.resolve()):sha(x)for x in paths}),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),checker_sha256=sha(target))))
