"""Supplement frozen workers with whole-corpus pre-entry exclusions and replay."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m2-fp-policy'
PROFILES=(('x87-c1','fistp32',384),('x87-store-c1','mul-special',480),('x87-store-c1','div-special',480))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok,reason):
    if not ok:raise AssertionError(reason)


def exercise():
    OUT.mkdir(parents=True,exist_ok=True);pins={};experiments=[];positives=[]
    def pin(path,expected=None):
        path=Path(path);key=str(path.resolve())
        digest=pins.get(key)
        if digest is None:digest=sha(path);pins[key]=digest
        require(expected is None or digest==expected,('frozen identity',str(path),digest,expected))
        return path
    for family,kind,count in PROFILES:
        base=ROOT/'reports'/family/kind;build_path=pin(base/'build.json')
        build=json.loads(build_path.read_text());report_path=pin(base/'comparison/report.json');report=json.loads(report_path.read_text())
        require(report['bounded_contract_passed'] is True and report['native_architectural_mismatches']==0,'prior profile not accepted')
        require(sha(build_path)==report['metadata_sha256'],'prior comparison/build binding')
        for relative,digest in build['source_files'].items():pin(ROOT/relative,digest)
        for path,digest in build['tool_files'].items():pin(path,digest)
        for relative,digest in build['artifacts'].items():pin(base/relative,digest)
        pin(build['repair_provenance_path'],build['repair_provenance_sha256'])
        for key in ('c1_baseline','initial_failure_provenance'):
            if key+'_path' in build:pin(build[key+'_path'],build[key+'_sha256'])
        fixture=pin(base/'fixture.bin',build['fixture_sha256']);corpus=pin(base/'comparison/corpus.bin',report['corpus_sha256'])
        raw=corpus.read_bytes();require(struct.unpack_from('<8s4I',raw)==(b'MW34REQ1',1,count,64,32) and len(raw)==24+count*64,'whole corpus header/length')
        index=count-1;record_offset=24+index*64
        out=OUT/kind;out.mkdir(exist_ok=True)
        workers=[('reference',report['reference_run'])]+[(r['optimization'],r) for r in report['native_runs']]
        require(len(workers)==3 and {x[0] for x in workers}=={'reference','O0','O2'},'all original/O0/O2 workers required')
        unsafe=[]
        if kind=='fistp32':
            for name,bits in (
                ('invalid_huge_positive',0x7fefffffffffffff),('invalid_huge_negative',0xffefffffffffffff),
                ('out_of_range_positive',0x41e0000000000000),('out_of_range_negative',0xc1e0000000200000),
                ('positive_infinity',0x7ff0000000000000),('negative_infinity',0xfff0000000000000),
                ('positive_QNaN',0x7ff8000000001234),('negative_QNaN',0xfff8000000004321),
                ('positive_SNaN',0x7ff0000000001234),('negative_SNaN',0xfff0000000004321),
                ('positive_subnormal',1),('negative_subnormal',0x8000000000000001)):
                unsafe.append((name,48,struct.pack('<Q',bits),'Expansion bits are outside reviewed exact input vectors'))
        else:
            for name,left,right in (
                ('two_QNaNs',0x7ff8000000001234,0xfff8000000004321),
                ('two_SNaNs',0x7ff0000000001234,0xfff0000000004321),
                ('mixed_QNaN_SNaN',0x7ff8000000001234,0xfff0000000004321),
                ('unlisted_left_QNaN',0x7ff800000000abcd,0x3ff0000000000000),
                ('unlisted_right_QNaN',0x3ff0000000000000,0x7ff800000000abcd),
                ('unlisted_left_SNaN',0x7ff000000000abcd,0x3ff0000000000000),
                ('unlisted_right_SNaN',0x3ff0000000000000,0x7ff000000000abcd),
                ('unlisted_sign_payload',0xfff8000000001234,0x3ff0000000000000)):
                unsafe.append((name,48,struct.pack('<QQ',left,right),'Expansion bits are outside reviewed exact input vectors'))
        for name,cw in (('unmasked_IE',0x37e),('unmasked_DE',0x37d),('unmasked_ZE',0x37b),
                        ('unmasked_OE',0x377),('unmasked_UE',0x36f),('unmasked_PE',0x35f),('reserved_PC',0x17f)):
            unsafe.append((name,40,struct.pack('<I',cw),'Control word is outside reviewed masked PC/RC modes'))
        mutations=[]
        for name,offset,data,diagnostic in unsafe:
            mutated=bytearray(raw);mutated[record_offset+offset:record_offset+offset+len(data)]=data
            require(mutated[:record_offset]==raw[:record_offset] and len(mutated)==len(raw),'one late record mutation')
            path=out/(name+'-corpus.bin');path.write_bytes(mutated)
            mutations.append((name,path,fixture,diagnostic,'one_last_record'))
        for name,prefix in (('guest_FNCLEX',bytes.fromhex('dbe2')),('unsupported_FNINIT',bytes.fromhex('dbe3')),('unsupported_FILD64',bytes.fromhex('df29'))):
            path=out/(name+'-fixture.bin');path.write_bytes(prefix+fixture.read_bytes())
            mutations.append((name,corpus,path,'','fixture_only'))
        for level,run in workers:
            worker=pin(run['command'][0],run['worker_sha256'])
            require(sha(worker)==build['reference_sha256' if level=='reference' else 'native_'+level+'_sha256'],'worker/build binding')
            previous=pin(run['output_path'],run['output_sha256']);output=out/(level+'-positive.bin')
            child=subprocess.run([str(worker),str(corpus),str(output),str(fixture)],capture_output=True,text=True,timeout=60)
            require(child.returncode==0 and sha(output)==sha(previous),('positive complete replay',kind,level,child.stderr))
            positives.append({'kind':kind,'optimization':level,'cases':count,'worker_sha256':sha(worker),
                              'input_sha256':sha(corpus),'fixture_sha256':sha(fixture),'output_sha256':sha(output),
                              'prior_output_sha256':sha(previous),'exact_full_record_replay':True,'stdout':child.stdout.strip()})
            for name,request,binary,diagnostic,mutation_type in mutations:
                output=out/(level+'-'+name+'-rejected-output.bin')
                require(not output.exists(),('negative output already exists',str(output)))
                child=subprocess.run([str(worker),str(request),str(output),str(binary)],capture_output=True,text=True,timeout=30)
                output_size=output.stat().st_size if output.exists() else 0
                expected=diagnostic or ('Code differs from authored expansion fixture identity' if level=='reference' else 'Authored code identity differs')
                require(child.returncode==1 and expected in child.stderr and output_size==0,
                        ('pre-entry exclusion failed',kind,level,name,child.returncode,child.stdout,child.stderr,output_size))
                experiments.append({'kind':kind,'optimization':level,'control':name,'changed_record':index if mutation_type=='one_last_record' else None,
                                    'mutation_type':mutation_type,'exit_code':child.returncode,'diagnostic':child.stderr.strip(),
                                    'worker_sha256':sha(worker),'input_sha256':sha(request),'fixture_sha256':sha(binary),
                                    'input_bytes':request.stat().st_size,'output_bytes':output_size,
                                    'input_path':str(request),'fixture_path':str(binary),'output_path':str(output)})
    for path,digest in pins.items():require(sha(Path(path))==digest,('frozen input changed during review',path))
    counts=Counter(x['kind'] for x in experiments)
    record={'schema_version':1,'status':'supplementary_unsafe_domains_rejected_before_entry','original_records_unchanged':True,
            'positive_runs':positives,'positive_records_replayed':sum(x['cases'] for x in positives),
            'negative_runs':experiments,'negative_run_count':len(experiments),'negative_counts_by_profile':dict(counts),
            'frozen_input_identities':pins,'scope':'Exclusions and exact replay only; no invalid-conversion/two-NaN/unmasked/clearing compatibility claim.',
            'live_state_final_acceptance':'pending'}
    output=OUT/'worker-exclusions.json';output.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'report_sha256':sha(output),'positive_runs':len(positives),'positive_records':record['positive_records_replayed'],
                      'negative_runs':len(experiments),'frozen_pins':len(pins),'negative_counts_by_profile':dict(counts)},indent=2))


if __name__=='__main__':exercise()
