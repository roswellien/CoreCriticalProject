"""Same logical inputs, actual writers/readers; fresh pilot outputs only."""
import ctypes,hashlib,json,struct,subprocess,sys,time,traceback
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path[:0]=[str(H),str(R/'tools/m4-pipeline'),str(R/'tools/m4-crt-allocation-root')]
from capture_bundle import CaptureBundle,sha_file
from capture_shared_v3 import SharedDirectSet
from run_v2 import DirectSet
from stages import run_stage,verify_stage
from manifests import verify_manifest
from validate_pilot_v2 import native_build,pin,need
from read_probe import PMC
def peak(handle):
    api=ctypes.WinDLL('psapi',use_last_error=True);api.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong];p=PMC();p.cb=ctypes.sizeof(p)
    if not api.GetProcessMemoryInfo(int(handle),ctypes.byref(p),p.cb):return None
    return p.PeakWorkingSetSize
def worker(argv,directory,files):
    directory.mkdir();start=time.perf_counter_ns();p=subprocess.Popen(argv,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL,creationflags=0x08000000);observed=0;samples=0
    while p.poll() is None:
        value=peak(p._handle)
        if value is not None:observed=max(observed,value);samples+=1
        if (time.perf_counter_ns()-start)/1e9>180:p.kill();raise ValueError('Bounded native pilot timeout')
        time.sleep(0.001)
    final_counter=peak(p._handle)
    if final_counter is not None:observed=max(observed,final_counter);samples+=1
    stdout,stderr=p.communicate();elapsed=(time.perf_counter_ns()-start)/1e9
    (directory/'stdout.bin').write_bytes(stdout);(directory/'stderr.bin').write_bytes(stderr)
    need(p.returncode==0,'Actual native pilot exit '+stderr.decode(errors='replace'));value=json.loads(stdout)
    need(value['passed'],'Actual native pilot completion');record={'passed':True,'argv':argv,'exit_code':p.returncode,'elapsed_seconds':elapsed,'native_metrics':value,'peak_working_set_bytes':observed,'peak_counter_samples':samples,'peak_counter_final_query_succeeded':final_counter is not None,'game_executed':False}
    (directory/'stage.json').write_text(json.dumps(record,indent=2)+'\n')
    for path in directory.iterdir():pin(files,path)
    return record
def records(path,values):
    with path.open('xb') as stream:
        stream.write(b'MW34REC1'+struct.pack('<I',len(values)))
        for name,data in values:
            n=name.encode('ascii');stream.write(struct.pack('<IQ',len(n),len(data)));stream.write(n);stream.write(data)
def reader_probe(kind,manifest,stage,files):
    result=run_stage([sys.executable,str(H/'read_probe.py'),kind,str(manifest)],stage,timeout_seconds=180,inputs=[H/'read_probe.py',H/'capture_shared_v3.py',manifest])
    checked=verify_stage(stage,sha_file(stage/'stage.json'));need(result['passed'] and checked['recorded_stage_passed'],'Actual isolated reader stage')
    for path in stage.iterdir():pin(files,path)
    return json.loads((stage/'stdout.bin').read_bytes())
def compare(legacy,shared,expected):
    def pinned(path,expected=None):
        path=Path(path);need(expected is None or sha_file(path)==expected,'Actual canonical archive pin');return path
    old=DirectSet(legacy,pinned)
    try:
        with SharedDirectSet(shared,sha_file(shared)) as new:
            need(set(old.entries)==set(new.entries)==set(name for name,_ in expected),'Unchanged exact logical consumer inventory')
            for name,data in expected:need(old.data(name)==new.data(name)==data,'Complete logical bytes unchanged '+name)
            return {'exact_full_byte_records':len(expected),'logical_bytes':sum(len(data) for _,data in expected),'shared_unique_blobs':new.meta['unique_blobs'],'shared_unique_payload_bytes':new.meta['unique_payload_bytes']}
    finally:old.close()
def canonical_build(files):
    path=pin(files,R/'reports/m4-capture-direct/build-r4/build.json');value=json.loads(path.read_text(encoding='utf-8-sig'));need(value['passed'],'Frozen canonical baseline passed')
    for key in ('sources','artifacts','objects','tools','libraries','compiler_read_headers'):
        for name,digest in value[key].items():pin(files,name,digest)
    pin(files,R/'tools/m4-crt-allocation-root/run_v2.py');return value
def run_workload(out,label,values,build,oldbuild,files,levels=('O0','O2')):
    path=out/(label+'.records');records(path,values);pin(files,path);cases={}
    for level in levels:
        directory=out/(label+'-'+level);directory.mkdir();metrics={}
        for kind,executable in [('canonical',oldbuild['workers'][level]),('shared',build['workers'][level])]:
            target=directory/kind;argv=[str(executable),'replay',str(path),str(target)];metrics[kind]={'writer':worker(argv,directory/(kind+'-stage'),files)}
            manifest=target/'transport.json';metrics[kind]['reader']=reader_probe(kind,manifest,directory/(kind+'-reader'),files)
            for physical in target.iterdir():pin(files,physical)
            meta=json.loads(manifest.read_bytes());metrics[kind]['physical_bundle_bytes']=sum(p['bundle_bytes'] for p in meta['parts']);metrics[kind]['manifest_bytes']=manifest.stat().st_size;metrics[kind]['logical_payload_bytes']=meta['payload_bytes']
        identity=compare(directory/'canonical/transport.json',directory/'shared/transport.json',values)
        need(metrics['canonical']['reader']['checksum']==metrics['shared']['reader']['checksum'],'Unchanged actual steady-access consumer checksum')
        cases[level]={'identity':identity,'metrics':metrics,'physical_bundle_reduction_fraction':1-metrics['shared']['physical_bundle_bytes']/metrics['canonical']['physical_bundle_bytes'],'scope':'Single measured same-input trial per level; OS cache uncontrolled. Timings are this workload only, no production or general speedup claim.'}
    return cases
def main(directory):
    out=Path(directory).resolve();need(out.parent==R/'reports/m4-capture-shared' and not out.exists(),'Fresh benchmark receipt');out.mkdir();files={};report={'passed':False,'format_adopted':False,'game_executed':False}
    try:
        build=native_build(files);oldbuild=canonical_build(files);pin(files,H/'benchmark.py');pin(files,H/'benchmark_v2.py');pin(files,H/'prepare_benchmark_v2.py');pin(files,H/'read_probe.py');pin(files,R/'tools/m4-pipeline/stages.py')
        blobs=[bytes((j*17+i*13)&255 for j in range(4096)) for i in range(32)]
        values=[(f'phase/{i:06}/page.bin',b'' if i%127==0 else blobs[i%32]) for i in range(10000)]
        report['authored']=run_workload(out,'authored',values,build,oldbuild,files)
        # Read-only bounded subset from one physically authenticated accepted71
        # part. It is not a complete game archive or new semantic gate.
        original=pin(files,R/'reports/m4-joint-startup71-root/execution-r1/O0/transport.json');meta=json.loads(original.read_bytes());part=meta['parts'][0];source=pin(files,original.parent/part['bundle'],part['sha256']);start=time.perf_counter_ns()
        with CaptureBundle(source,part['sha256']) as owner:
            selected=[name for name in owner.names() if '/pages/' in name][:12000]
            if len(selected)<1000:selected=list(owner.names())[:12000]
            values=[(name,owner.read_bytes(name)) for name in selected]
        report['retained_source']={'manifest':str(original),'manifest_sha256':sha_file(original),'part':str(source),'part_sha256':part['sha256'],'source_part_logical_records':part['logical_files'],'source_part_payload_bytes':part['payload_bytes'],'selected_logical_records':len(values),'selection_rule':'first12000 sorted names containing /pages/; if fewer than1000, first12000 sorted names','strict_original_authenticate_and_select_seconds':(time.perf_counter_ns()-start)/1e9,'original_files_modified':False,'full_archive_game_acceptance_claimed':False}
        report['retained_subset']=run_workload(out,'retained',values,build,oldbuild,files,levels=('O2',))
        report.update(passed=True,transport_only=True,native_transport_executed=True,exact_full_byte_records=sum(c['identity']['exact_full_byte_records'] for group in ('authored','retained_subset') for c in report[group].values()),files=files,current_physical_closure=verify_manifest(files),scope='Authored same-input trials and read-only partial accepted71 conversion; production captures/readers unchanged. Peak RAM is Windows process PeakWorkingSetSize. No cold-cache or end-to-end game speedup claim.')
    except BaseException as exc:report.update(error=str(exc),traceback=traceback.format_exc(),files=files);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'exact_full_byte_records':report.get('exact_full_byte_records'),'format_adopted':False,'report':str(out/'report.json')}))
if __name__=='__main__':main(*sys.argv[1:])
