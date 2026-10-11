"""Small additive native interface and remaining admission obligations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-native'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=B/'fixture-handoff-r1';assert not p.exists();p.mkdir()
text='''The current fixture is compiled at O0 and O2, and its native writer is unlaunched pending independent prelaunch review. It grants no initializer credit.

`fixture-preparation-r2` freezes one registered Runtime translation, thirteen literal bodies, source State3504/CPU40/FX512, all142 normal source PCs,113 causal operand identities, and a1,212,472B input pack. Every byte of that pack is genuine original BEFORE; the registered Runtime overwrites only its outer saved return token withFFFFFFF0. The284 declared blocks are272 source provider pages,4 genuine game pages, completeTEB8192, stack65536, five actual borrowed backings, and one initialized guestCS24.

The source request consists of MFC1168 cached TLS/current-thread retrieval, cached global fallback, byte+14=0/DWORD+1040=421, and unchanged `_setmbcp(-3)`/GetACP1252. Native code owns a realTlsAlloc slot bound to a16B current-thread mirror and a separate realCRITICAL_SECTION40. The guest source index3 and borrowedCS24 do not become host resource storage. TlsGetValue returns the actual64-bit association; typed guest EAX names the original borrowed thread. Enter/Leave actual native depth/current-host-thread identity transports only the three semantic guestCS DWORDs; every opaque guest/native CS byte remains separate. GetACP is actually called and must return1252. Guest VOID EAX0 and retained ECX/EDX/flags are explicit typed ABI representatives, not original AFTER registers.

The raw native output schema is tenDWORDs: Access24B, ApiRecord352B,113accesses,4APIs,3504State,40CPU,512FX,284blocks,1translation,1call. Access is `(PC32,address32,value64,width32,write32)`. ApiRecord is16Q words, CPUbefore40, CPUafter40, sourceframe64, nativeCSbefore40, nativeCSafter40. Its16Q words are version,index,sourceIAT_PC,sourceTarget,argc,sourceFrame,sourceRET,guestResult,actualHostResult,actualHostThread,actualHostTLSindex,actualHostAssociation,guestThreadPointer,nativeDepth,LastErrorBefore,LastErrorAfter. The genuine codepage resolver tail uses the literal caller at78003DEE and rawIAT read at78003EAB.

`compare_fixture.py` is independently authored and unexecuted. It begins from the fresh native BEFORE State/CPU/FX/memory, runs all142 literal instructions, consumes only the four explicit typed API seams, and compares all3504 State bytes,40 CPU bytes,512 FX bytes, every declared whole memory block,113 ordered scalar operands, four actual API frames/CPU sides/nativeCS owners/depth, exact imported EH special return and FS install/restore, and actual owned TLS/CS cleanup. Native AFTER is solely a comparison target.

Remaining gates: exact current prelaunch/admission review before writer; actual O0/O2 smoke and source equality; physicalAMD64 native API/lifecycle export identity proof; varied BEFORE and causal negative controls; complete connected ownership/resource proof and persistent schedules. Five genuine sparse-probe borrowed extents at7C2xxx/7C3xxx overlap the admitted full PE BSS virtual domain400000..9F5000. The fixture intentionally installs only those declared source-role BEFORE extents at original addresses; full connected integration needs an independently reviewed borrowed alias policy or exact typed relocation/pointer-cell rewrite. No lazy callbacks, new object allocation, non1252 codepages or arbitrary nonzero caller-FP metadata are admitted.
'''
(p/'interface.md').write_text(text,encoding='utf-8')
paths=[R/'reports/m4-mfc1168-probe/validation-r6/report.json',R/'reports/m4-tree-review/mfc1168-original-r1/report.json',B/'lifts-r2/report.json',B/'fixture-preparation-r2/report.json',B/'fixture-build-r3/build.json',R/'tools/m4-mfc1168-native/compare_fixture.py',R/'tools/m4-mfc1168-native/run_fixture.py',Path(__file__),p/'interface.md']
report=dict(passed=True,scope='Concrete compiled finite native fixture handoff; writer unlaunched and initializer credit0',files={str(q.resolve()):sha(q)for q in paths},native_executed=False,initializer_credit=0)
(p/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(p/'report.json'))
