"""Causal raw observer and actual executable publication/admission controls."""
import argparse,copy,hashlib,importlib.util,json,mmap,subprocess,struct,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(p):return {str(x.resolve()):sha(x) for x in p.rglob('*') if x.is_file()}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True);parser.add_argument('--original',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    assert not a.output.exists() and a.output.resolve().is_relative_to(ROOT/'reports/m4-fp-sqrt');a.output.mkdir()
    b=json.loads(a.build.read_text(encoding='utf-8-sig'));spec=importlib.util.spec_from_file_location('own_observer',ROOT/'tools/m4-fp-sqrt/analyze_sqrt.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with a.original.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as om:
        o=module.fields(om[24:24+75988],False)
    npath=a.build.parent/'directed-O0.bin'
    with npath.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nm:n=module.fields(nm[32:32+83168],True)
    assert not module.pair(o,n)
    observers=[]
    for field,offset in [('cpu1',0),('mem1',0),('mem1',7*4096+0x150),('state1',0),('state1',2739),('state1',2776),('fx1',0),('fx1',2),('fx1',4),('fx1',32),('fx1',160),('env1',12),('host1',0),('host1',32),('host1',160),('henv1',12)]:
        r=copy.deepcopy(n);x=bytearray(r[field]);x[offset]^=1;r[field]=bytes(x);issues=module.pair(o,r);assert issues
        observers.append({'field':field,'offset':offset,'diagnostics':issues,'rejected':True})
    for field in ('counts','events'):
        r=copy.deepcopy(n)
        if field=='counts':r[field]=(7,4,3,5,5,1,0,0)
        else:r[field][0]=(0x5c8a88,n['events'][0][1]^1,8,0)
        issues=module.pair(o,r);assert issues;observers.append({'field':field,'diagnostics':issues,'rejected':True})
    workers={'original':Path(b['original_worker']),**{l:Path(b['builds'][l])/'mw34_m4_fp_sqrt_native.exe' for l in ('O0','O2')}}
    actual=[]
    for name,worker in workers.items():
        root=a.output/name;command=[str(worker),'--check-publication',str(root.resolve())];run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30)
        log=a.output/(name+'-publication.log');log.write_bytes(run.stdout+run.stderr)
        assert run.returncode==0 and b'2 actual publisher admission controls passed' in run.stdout
        files=inventory(root);assert len(files)==2 and all(Path(p).read_bytes()==bytes.fromhex('4d57333400ff8042') for p in files)
        actual.append({'worker':str(worker.resolve()),'worker_sha256':sha(worker),'kind':'actual existing output and actual existing stage','checks':2,'command':command,'exit_code':run.returncode,'fixtures':files,'log':str(log.resolve()),'log_sha256':sha(log)})
    pack=ROOT/'reports/m4-fp-startup/research-r1/pages.bin';image=ROOT/'MW3/Mech3.exe'
    for kind,source,position in [('pack',pack,20),('image',image,0)]:
        x=bytearray(source.read_bytes());x[position]^=1;p=a.output/('changed-'+kind+'.bin');p.write_bytes(x)
        for name,worker in workers.items():
            dest=a.output/(name+'-'+kind+'-denied.bin');command=[str(worker),str(p if kind=='pack' else pack),str(p if kind=='image' else image),str(dest.resolve())]
            run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30);log=a.output/(name+'-'+kind+'.log');log.write_bytes(run.stdout+run.stderr)
            diagnostic=(run.stdout+run.stderr).lower()
            assert run.returncode!=0 and not dest.exists() and kind.encode() in diagnostic and b'required' in diagnostic
            actual.append({'worker':str(worker.resolve()),'kind':'changed '+kind,'command':command,'exit_code':run.returncode,'no_result':True,'log':str(log.resolve()),'log_sha256':sha(log)})
    report={'passed':True,'observer_mutations':observers,'observer_count':len(observers),'actual_controls':actual,'actual_publication_checks':6,'actual_wrong_identity_checks':6,'scope':'Real authored CREATE_NEW publisher controls and real image/pack denial; sequential ordinary private directories'}
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'observer':len(observers),'publication':6,'identity_denials':6}))
if __name__=='__main__':main()
