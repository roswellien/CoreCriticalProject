"""Read-only independent foundation/source and direct-boundary review receipt."""
from pathlib import Path
import hashlib, json, struct
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-crt-entry-data/independent-source-r1'
PINS={}
def pin(p,h=None):
    p=Path(p).resolve()
    with p.open('rb') as f:v=hashlib.file_digest(f,'sha256').hexdigest()
    assert h is None or h==v,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v
    PINS[str(p)]=v;return p
assert not OUT.exists();OUT.mkdir()
build=ROOT/'reports/m4-crt-entry-data/build-r6'
execution=ROOT/'reports/m4-crt-entry-data/root-execution-r1'
model=ROOT/'reports/m4-crt-entry-data/root-model-r1'
r=json.loads(pin(model/'report.json').read_text());assert r['passed'] and r['records']==48 and len(r['actual_compiled_causal_cases'])==24
for p,h in json.loads(pin(model/'pins.json').read_text())['files'].items():pin(p,h)
b=json.loads(pin(build/'build.json').read_text());assert b['passed']
for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
    for p,h in b[group].items():pin(p,h)
e=json.loads(pin(execution/'execution.json').read_text());assert e['passed']
for command in e['commands']:
    assert command['exit_code']==0
    worker=pin(command['command'][0]).read_bytes();off=struct.unpack_from('<I',worker,60)[0];assert struct.unpack_from('<H',worker,off+4)[0]==0x8664
before_paths=sorted(execution.rglob('*-host-before.bin'));assert len(before_paths)==138
for p in before_paths:
    before=pin(p).read_bytes();after=pin(p.with_name(p.name.replace('-before.bin','-after.bin'))).read_bytes();assert len(before)==len(after)==544
    assert before[512:540]==after[512:540] and before[524:540]!=bytes(16)
    for lo,hi in [(0,5),(24,28)]+[(32+16*i,42+16*i) for i in range(8)]+[(160+16*i,176+16*i) for i in range(6,16)]:assert before[lo:hi]==after[lo:hi]
    scenario=int(p.parent.name.split('-')[-1])
    for i in range(6,16):assert before[160+16*i:176+16*i]==bytes((i*31+k*17+scenario+1)&255 for k in range(16))
source=ROOT/'reports/m4-crt-entry-data/preparation-r4/composition.cpp'
for p in (source,source.with_name('main_v2.inc'),ROOT/'tools/m4-crt-entry-data/capture.s',ROOT/'tools/m4-crt-entry-data-review/observe.py',Path(__file__)):pin(p)
report=dict(passed=True,scope='Independent foundation/source and direct caller boundary audit of accepted BEFORE-only FDIV writer to bounded CRT entry data consumer',build='reports/m4-crt-entry-data/build-r6',root_execution='reports/m4-crt-entry-data/root-execution-r1/execution.json',root_source_model='reports/m4-crt-entry-data/root-model-r1/report.json',positive_cases=48,causal_controls=24,full_State_bytes=3504,separate_FX_bytes=512,full_pages=11,full_source_identity_bytes=430,writer_events=4656,consumer_events=1632,root_observer_corruption_denials=56,independently_checked_direct_host_records=138,nonzero_before_legacy_metadata_records=138,seeded_ABI_nonvolatile_XMM='XMM6..15 exact patterned BEFORE plus all128bits preserved per register',
            findings=['Context borrows one ready FDIV Registry and the existing stable State/FX; no data/FP reseed',
                      'Flat DS/SS and owned Runtime FS base checked; only declared outer ESP/EIP transition accepted',
                      'Only actual PC5AC408 raw IAT5BB508 maps to owned source-written global78037C2C; dependent load5AC40D and actual third query BOOL remain bound',
                      'Three source-owned import CALL frames and literal one-byte translated RET leaf5AC5C0 complete; root stays incomplete at required next matherr import5AC428/5BB50C',
                      'AF0 is admitted and recorded only at source TEST5AC41F; no defined AF or arbitrary undefined-value equivalence claim',
                      'No generic data registry substitutes file-zero for initialized writer data; current source/IAT/global mutations fail causally before clean stop',
                      'External ASM snapshots direct caller state before harness cleanup; small noexcept Job callback contains all exceptions; completeENV28, numerical raw80/MXCSR and ABI XMM6..15 measured on positive/fault calls',
                      'Independent root model imports pinned separately independent producer/prefix models; exact source decoding and original BEFORE drive expectations, never native AFTER',
                      'Counter138 =48positives*2 +6early writer-only faults +18later writer-and-entry faults*2'],
            no_blocker_to_bounded_gate=True,scope_limit='This is source/BEFORE-defined native data composition to the matherr stop. Original entry execution, SEH dispatch, complete CRT/entry/startup and connection into selected27 table run remain unproved.',reviewer_executed_guest_or_original=False,ordinary_game_launched=False,whole_M4_complete=False)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
(OUT/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n')
print(json.dumps(dict(passed=True,report=str(OUT/'report.json'),host_records=138)))
