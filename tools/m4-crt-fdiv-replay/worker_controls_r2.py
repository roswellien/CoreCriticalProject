"""Actual denial controls for the new replay executable, not game execution."""
import argparse,hashlib,importlib.util,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-replay'
RUN=ROOT/'tools/m4-crt-fdiv-replay/run_replay.py'
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def save(p,v):
    with pathlib.Path(p).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def blob(p,b):
    with pathlib.Path(p).open('xb')as f:f.write(b)
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private worker-control folder')
    spec=importlib.util.spec_from_file_location('author_replay_runner',RUN);R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
    build,inputs,files=R.admit();out.mkdir();blob(out/'controls-source.py',pathlib.Path(__file__).read_bytes())
    original=inputs.read_bytes();changed=bytearray(original);changed[24+24]^=1;bad_input=out/'changed-before-inputs.bin';blob(bad_input,changed)
    truncated=out/'truncated-before-inputs.bin';blob(truncated,original[:-1])
    changed=bytearray(R.PACK.read_bytes());changed[100]^=1;bad_pack=out/'changed-pack.bin';blob(bad_pack,changed)
    changed=bytearray(R.PROVIDER.read_bytes());changed[100]^=1;bad_provider=out/'changed-provider.dll';blob(bad_provider,changed)
    records=[]
    try:
        for level,worker in build['workers'].items():
            for scenario in ('changed-before-input','truncated-before-input','missing-before-input','changed-pack','changed-provider','existing-output','wrong-argument-count'):
                prefix=level+'-'+scenario;output=out/(prefix+'.bin');command=[worker,str(R.GAME),str(R.PROVIDER),str(R.PACK),str(inputs),str(output)]
                expected=b'Exact before-only input identity/schema required';policy='absent'
                if scenario=='changed-before-input':command[4]=str(bad_input)
                elif scenario=='truncated-before-input':command[4]=str(truncated)
                elif scenario=='missing-before-input':command[4]=str(out/'missing.bin');expected=b'Input file unavailable'
                elif scenario=='changed-pack':command[3]=str(bad_pack);expected=b'Frozen Registry admission';policy='header-only'
                elif scenario=='changed-provider':command[2]=str(bad_provider);expected=b'Frozen Registry admission';policy='header-only'
                elif scenario=='existing-output':blob(output,b'EXTERNAL PREEXISTING REPLAY EVIDENCE\x00\xff');expected=b'Fresh replay output required';policy='sentinel'
                elif scenario=='wrong-argument-count':command.pop();expected=b'Native replay: actual-game actual-provider exact-pack before-inputs fresh-output'
                before=sha(output)if output.exists()else None
                need(R.admit()[2]==files,'Exact pre-control frozen associations')
                cp=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
                blob(out/(prefix+'.stdout'),cp.stdout);blob(out/(prefix+'.stderr'),cp.stderr)
                record={'level':level,'scenario':scenario,'command':command,'exit_code':cp.returncode,'expected_diagnostic':expected.decode(),'actual_stderr':cp.stderr.decode('utf-8','replace'),'output_policy':policy,'output_exists':output.exists(),'output_bytes':output.stat().st_size if output.exists()else 0,'output_sha256':sha(output)if output.exists()else None,'before_sha256':before}
                records.append(record);save(out/(prefix+'.json'),record)
                need(cp.returncode==1 and expected in cp.stderr and not cp.stdout,'Actual intended denial diagnostic/exit/no source replay')
                if policy=='absent':need(not output.exists(),'Required denial before output publication')
                elif policy=='sentinel':need(sha(output)==before,'Actual external evidence unchanged')
                else:need(output.read_bytes()==b'MW4FDRN1\x01\x00\x00\x00\x18\x00\x00\x00\xdc\xa4\x01\x00\x09\x00\x00\x00','Actual retained header-only prefix; no source row or COMPLETE')
        need(R.admit()[2]==files,'All frozen associations unchanged after actual controls')
        save(out/'report.json',{'passed':True,'scope':'Actual CLI/input/source/fresh-output replay denial controls only; no original execution/fullM4',
            'actual_controls':len(records),'observations':records,'original_executed':False,'native_source_replay_observed_in_controls':False,'whole_M4_complete':False})
    except Exception as e:
        save(out/'failure.json',{'passed':False,'reason':str(e),'observations':records,'raw_prefixes_and_diagnostics_retained':True});raise
    finally:
        files[str(RUN)]=sha(RUN);files[str(pathlib.Path(__file__).resolve())]=sha(__file__)
        for p in out.rglob('*'):
            if p.is_file():files[str(p)]=sha(p)
        save(out/'pins.json',{'files':files})
    print(json.dumps({'passed':True,'controls':len(records),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
