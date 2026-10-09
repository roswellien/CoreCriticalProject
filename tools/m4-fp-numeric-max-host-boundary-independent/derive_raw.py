"""Additive root observer derivation; frozen guest/source oracles stay unchanged."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tools/m4-fp-numeric-max-host-boundary-independent'
OLD=ROOT/'tools/m4-fp-numeric-max-integration-independent'
RECORD=ROOT/'reports/m4-fp-numeric-max-host-boundary/root-observer-derivation-r1'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def change(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b)
assert not RECORD.exists()
RECORD.mkdir(parents=True)
files={};changes=[]
helper='''def host_boundary(row,cw):
    before=row[45068:45580];after=row[45580:46092]
    env=row[46092:46120];env_after=row[46120:46148]
    need(before[:5]==struct.pack('<HHB',cw,0x3a20,0x81),'Input-derived caller CW/TOP7/PE/C1/two occupied physical tags')
    need(words(before,24)[0]==0x1f80,'Input-derived caller MXCSR')
    expected_env=struct.pack('<7I',0xffff0000|cw,0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b)
    need(env==expected_env,'Complete independently derived nonzero caller legacy ENV input')
    for i in range(8):
        expected=struct.pack('<QH',(1<<63)+(i<<56),0x4000|(0x8000 if i&1 else 0))
        need(before[32+16*i:42+16*i]==expected,'All independently seeded caller raw80 storage')
        need(after[32+16*i:42+16*i]==expected,'Direct after-return caller raw80 before cleanup')
    need(after[:5]==before[:5] and after[24:28]==before[24:28] and env_after==env,'Direct owned invocation preserves numerical host state and complete legacy ENV before cleanup')
    # Full512-byte images remain unmodified observations. Volatile SIMD and
    # reserved padding equality are not numerical restoration requirements.

'''
ancestors={
 'persistent_model.py':ROOT/'reports/m4-fp-numeric-max-integration/independent-persistent-final-r1/pins.json',
 'replay_model.py':ROOT/'reports/m4-fp-numeric-max-integration/independent-replay-final-r1/pins.json',
}
for name,prior_path in ancestors.items():
    p=OLD/name;prior=json.loads(prior_path.read_text())['files']
    assert prior[str(p)]==sha(p)
    literal=RECORD/(name+'.ancestor');literal.write_bytes(p.read_bytes())
    files[str(p)]=sha(p);files[str(literal)]=sha(literal);files[str(prior_path)]=sha(prior_path)
    s=p.read_text().replace("ROOT/'reports/m4-fp-numeric-max-integration'","ROOT/'reports/m4-fp-numeric-max-host-boundary'")
    if name=='persistent_model.py':
        s=change(s,'def observe(row,sequence,phase,case,sb,memory,old):',helper+'def observe(row,sequence,phase,case,sb,memory,old):')
        s=change(s,"    need(row[45068:45580]==row[45580:46092] and row[46092:46120]==row[46120:46148],'Entire captured host FX512/ENV28 restoration; reserved bytes are storage padding')","    host_boundary(row,cw)")
        s=change(s,"'Host reserved FXSAVE padding is initialized serialized storage, not extra hardware credit'","'Host BEFORE independently derives TOP7/depth2/PE+C1/CW/nonzeroENV; AFTER measured before cleanup through owned invoke. Numerical spans/fullENV only; volatileSIMD and reserved padding are unmodified observations'")
    else:
        s=change(s,"    need(n[45068:45580]==n[45580:46092] and n[46092:46120]==n[46120:46148],'Full native host FX512/ENV28 captured restore, reserved padding storage only')","    persistent.host_boundary(n,case[4])")
        s=change(s,"        persistent_path=ROOT/'tools/m4-fp-numeric-max-integration-independent/persistent_model.py'\n        prior=json.loads((ROOT/'reports/m4-fp-numeric-max-integration/independent-persistent-r1/pins.json').read_text())['files']\n        persistent=own(persistent_path,'root_native_persistent_model',prior[str(persistent_path)])",f"        persistent_path=ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/persistent_model.py'\n        persistent=own(persistent_path,'root_native_persistent_model','{sha(OUT/'persistent_model.py')}')")
        s=change(s,"'CC/deadraw80 representative/observations stay limited to declaredfixtures, source/toolhashes post-build associations notfullprocessattestation'","'CC/deadraw80 representative/observations stay limited to declaredfixtures, source/toolhashes post-build associations notfullprocessattestation','Direct numerical host/fullENV preservation through invoke observed before cleanup; volatileSIMD/reserved FX are raw observations without equality credit'")
    target=OUT/name;assert not target.exists();target.write_text(s)
    files[str(target)]=sha(target);changes.append(dict(file=name,guest_source_state_pages_events_routes_and_original_oracle_unchanged=True,changes=['Fresh derivative report namespace','Direct host input-derived numerical/fullENV check, no volatile/reserved equality','Replay imports exact new root-owned persistent observer'] if name.startswith('replay') else ['Fresh derivative report namespace','Direct host input-derived numerical/fullENV check, no volatile/reserved equality']))
files[str(Path(__file__))]=sha(Path(__file__))
report=RECORD/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Root-only mechanical additive raw observer derivative; no native/original execution',changes=changes,files=files,author_model_imported=False,whole_M4_complete=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=sha(report),files=len(files))))
