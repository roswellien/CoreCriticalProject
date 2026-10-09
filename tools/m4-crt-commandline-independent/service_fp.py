"""Additive independent hardware mid-service FP capture qualification."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
import raw_model as own

ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-native'
def need(v,w):
    if not v:raise ValueError(w)
def check(row):
    before=row[5612:6124];env=row[7716:7744]
    for offset,eo in ((6636,7772),(7148,7800)):
        capture=row[offset:offset+512]
        need(capture[:160]==before[:160] and capture[416:]==before[416:],'Native actual mid-service complete x87/raw80/capability/reserved storage equals independently captured host entry')
        need(row[eo:eo+28]==env,'Native actual mid-service complete legacy environment equals independent host entry')
    # SIMD160..415 is recorded actual host observer/API work, whose temporaries
    # are not a guest-State output. It may differ within the callback. The full
    # outer applicable256 SIMD bytes are independently proven restored instead.
    own.host_restore(before,row[6124:6636],env,row[7744:7772],True)

def main(out):
    need(not out.exists() and out.is_relative_to(BASE),'Fresh private independent supplement required')
    closure=BASE/'independent-final-review-r1/report.json';pins=BASE/'independent-final-review-r1/pins.json'
    need(own.sha(closure)=='28cc793ab1e27f6ef8dc31638ed2528a72495fd8ee3c3a524aa618dd820e2e8a' and own.sha(pins)=='e91dff9f9f8a60a592199db061dd6df0b348d8f9153705f1f64941c80ec117de','Exact already frozen independent closure')
    files=json.loads(pins.read_text())['files']
    for path,expected in files.items():need(own.sha(path)==expected,'Earlier independent evidence unchanged')
    cases=0;controls=[]
    for level in ('O0','O2'):
        for fixture in range(8):
            path=BASE/'capture-repaired-normal-r1'/f'{level}-{fixture}.bin';_,_,rows=own.parse(path,True)
            for row,regions,owned in rows:check(row);cases+=1
            row=rows[0][0]
            for start in (6636,7148):
                for off in (0,2,4,6,8,16,24,28,32,41,48,159,416,511):
                    changed=bytearray(row);changed[start+off]^=1
                    try:check(changed)
                    except ValueError as e:controls.append({'level':level,'fixture':fixture,'offset':start+off,'rejected':True,'reason':str(e)});continue
                    raise ValueError('Accepted actual hardware x87/capability mutation')
            for start in (7772,7800):
                for off in range(28):
                    changed=bytearray(row);changed[start+off]^=1
                    try:check(changed)
                    except ValueError as e:controls.append({'level':level,'fixture':fixture,'offset':start+off,'rejected':True,'reason':str(e)});continue
                    raise ValueError('Accepted separate ENV byte mutation')
            files[str(path)]=own.sha(path)
    need(cases==768 and len(controls)==1344,'Complete actual supplement extent')
    report={'passed':True,'scope':'Additive independent native hardware mid-service x87/environment capture and explicit volatile SIMD qualification',
            'native_records':cases,'observer_controls':controls,'mid_service_FX_bytes_checked_per_snapshot':256,'mid_service_ENV_bytes_checked_per_snapshot':28,
            'mid_service_SIMD_bytes_recorded_but_unspecified_per_snapshot':256,
            'qualification':'The two complete512 FX captures are actual observations. Their256 mid-service SIMD bytes may change during actual host API/observer work and are not software guest State output. All remaining256 FX bytes and complete28 ENV match the independently captured outer host entry; complete outer256 SIMD restoration is checked. Guest full State/FX/SIMD preservation and original actual service captures remain proven in frozen raw review.',
            'no_primary_model_imports':True,'closure_report_path':str(closure),'closure_report_sha256':own.sha(closure),'whole_M4_complete':False}
    out.mkdir();rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');files[str(rp)]=own.sha(rp)
    for path in (closure,pins,pathlib.Path(__file__).resolve()):files[str(path)]=own.sha(path)
    pp=out/'pins.json';pp.write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n')
    print('Independent actual service FP supplement passed',cases,len(controls),own.sha(rp),own.sha(pp))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve())
