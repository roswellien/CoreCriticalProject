"""Independent source-only constructor cleanup namespace/guard review."""
from pathlib import Path
import ast, hashlib, json, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def main(name):
    out = ROOT / 'reports/m4-constructor-validator-audit' / name
    need(not out.exists(), 'Fresh additive source-only receipt')
    out.mkdir(parents=True)
    files, passed = {}, False
    def pin(path, digest=None):
        path = Path(path).resolve()
        need(path.suffix.lower() not in ('.mwb','.bin','.exe') and path.name not in ('transport.json','index.json','payload.dat'), 'Only source and small descriptors; no capture/index/payload/binary reader')
        actual = sha(path)
        need(digest is None or digest == actual, 'Exact current source input ' + str(path))
        need(str(path) not in files or files[str(path)] == actual, 'Stable successful source read')
        files[str(path)] = actual
        return path
    def read(path, digest=None):
        return json.loads(pin(path,digest).read_bytes())
    try:
        prep_path = ROOT / 'reports/m4-constructor-original/chronological-preparation-r10/report.json'
        prep = read(prep_path,'22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe')
        need(prep['passed'],'Current exact prep10 source producer')
        reference_path = prep_path.parent / 'reference.cpp'
        reference = pin(reference_path,prep['files'][str(reference_path.resolve())]).read_text()
        normal_path = prep_path.parent / 'constructor_normal.hpp'
        normal = pin(normal_path,prep['files'][str(normal_path.resolve())]).read_text()
        prerequisite_path = prep_path.parent / 'prerequisite_observer.hpp'
        prerequisite = pin(prerequisite_path,prep['files'][str(prerequisite_path.resolve())]).read_text()
        old_path = ROOT / 'tools/m4-constructor-original/validate_v6.py'
        new_path = ROOT / 'tools/m4-constructor-original/validate_v7.py'
        old, new = pin(old_path).read_text(), pin(new_path).read_text()
        lineage = pin(ROOT / 'tools/m4-constructor-original/derive_validator_v7.py').read_text()
        need(sha(new_path)=='cc536b43d0300c724c93f8a74dbd016ec2c597762a1784e0874ac3f9b6b2a9a2','Exact current validator7 identity')
        execution_path = ROOT / 'reports/m4-constructor-original/chronological-execution-r3/report.json'
        execution = read(execution_path,'cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4')
        failure_path = ROOT / 'reports/m4-constructor-original/chronological-validation-r2/report.json'
        failure = read(failure_path)
        failure_text = pin(failure_path.parent/'failure.txt').read_text()
        need(execution['passed'] and not failure['passed'] and failure['reader_closed'] and failure['execution_sha256'] == sha(execution_path),'Existing writer succeeded and failed validator closed; this audit does not replay')
        need('Every live measured new constructor owner freed exactly once by research cleanup' in failure_text and failure['counts']['whole_phase_records'] == 37 and failure['counts'].get('whole_actual_new_owner_cleanup_returns',0) == 0,'Exact failed sequence0 cleanup selection context')
        need('for(auto&v:constructor_occurrences)if(v.alive&&v.phase<entries.size()&&constructor_is_root(entries[v.phase])){const auto stem="cleanup/"+std::to_string(sequence)+"/constructor-owner-"+std::to_string(v.serial);out.append(stem+"/meta.bin",&v,sizeof(v));out.append(stem+"/before.bin",reinterpret_cast<void*>(v.pointer),v.capacity);mfc825(reinterpret_cast<void*>(v.pointer));const unsigned returned=1;out.append(stem+"/returned.bin",&returned,4);v.alive=0;}' in reference,'Exact direct producer prefix and metadata/whole backing/return marker/lifetime order')
        need('constructor_dump' not in reference.split('const auto stem="cleanup/"+std::to_string(sequence)+"/constructor-owner-"',1)[1].split('\n',1)[0],'Cleanup uses direct Writer.append, not prerequisite-prefixed helper')
        need('constructor_is_root(unsigned entry){return entry==0x4103f0||entry==0x410440||entry==0x459b40;}' in normal,'Exact three-root cleanup scope')
        need('unsigned version,serial,phase,api_index,kind,heap,requested,pointer,capacity,alive,predecessor_serial,initial_bytes;' in prerequisite,'Whole occurrence metadata contains all12 measured DWORD fields')
        old_prefix="cleanup_prefix=f'constructor-prerequisites/cleanup/{sequence}/constructor-owner-'"
        new_prefix="cleanup_prefix=f'cleanup/{sequence}/constructor-owner-'"
        need(old.count(old_prefix)==1 and new.count(new_prefix)==1 and old_prefix not in new,'One exact additive direct cleanup-key correction')
        diagnostic_path=ROOT/'reports/m4-constructor-original/cleanup-diagnostic-r1/report.json'
        diagnostic=read(diagnostic_path,'6d97e5abf473548eb6f138a4e60f00f5d173888c371de269e3174e0d3835c3fa')
        need(diagnostic['passed'] and diagnostic['reader_closed'] and diagnostic['producer_prefix']=='cleanup/<sequence>/constructor-owner-' and diagnostic['files'][str(reference_path.resolve())]==sha(reference_path) and diagnostic['files'][str(execution_path.resolve())]==sha(execution_path),'Immutable successful closed cleanup diagnostic binds this exact source/execution; archive declarations not opened by this audit')
        expected=old.replace(old_prefix,new_prefix,1)
        anchor="        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)"
        evidence="        cleanup_evidence=read(BASE/'cleanup-diagnostic-r1/report.json','6d97e5abf473548eb6f138a4e60f00f5d173888c371de269e3174e0d3835c3fa');need(cleanup_evidence['passed']and cleanup_evidence['producer_prefix']=='cleanup/<sequence>/constructor-owner-','Exact current producer cleanup-key evidence')\n        for path,digest in cleanup_evidence['files'].items():pin(path,digest)\n"
        need(expected.count(anchor)==1,'Unique new diagnostic admission anchor')
        expected=expected.replace(anchor,evidence+anchor,1)
        old_lineage="pin(Path(__file__).with_name('derive_validator_v6.py'));pin(sys.executable);passed=True"
        new_lineage="pin(Path(__file__).with_name('derive_validator_v6.py'));pin(Path(__file__).with_name('validate_v6.py'));pin(Path(__file__).with_name('derive_validator_v7.py'));pin(sys.executable);passed=True"
        need(expected.count(old_lineage)==1,'Unique additive validator lineage pin anchor')
        expected=expected.replace(old_lineage,new_lineage,1)
        need(new==expected,'Exact entire v7 source equals v6 plus only cleanup key, immutable evidence admission and additive lineage pins')
        ast.parse(new)
        guard="v[1]not in observed_cleaned and v[1]in source_new_serials and v[1]in live_byserial and v==live_byserial[v[1]]and v[2]<len(order)and order[v[2]]['entry']in NEW and v[9]"
        need(guard in new and "len(backing)==v[8]and reader.data(key.replace('/meta.bin','/returned.bin'))==struct.pack('<I',1)" in new and "observed_cleaned=={serial for serial in source_new_serials if live_byserial[serial][9]}" in new,'Preserved uniqueness, full metadata/current live/new-root identity, complete capacity, returned1 and exhaustive exact set guards')
        controller=read(ROOT/'reports/m4-constructor-original/controller-preparation-r6/report.json','b35b9ce0a6df17c723a8e86c91a307979c4bb6a18053e35340906da0d9017c54')
        need(controller['passed'],'Current strict controller preparation')
        outcome=read(ROOT/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95')
        need(outcome['passed'] and outcome['reader_closed'] and outcome['counts']['whole_phase_records']==222 and outcome['counts']['whole_actual_new_owner_cleanup_returns']==36 and outcome['files'][str(new_path.resolve())]==sha(new_path) and outcome['execution_sha256']==sha(execution_path),'Current passing strict validation outcome binds exact v7 and same writer; receipt only, no replay')
        pin(__file__)
        pin(sys.executable) if Path(sys.executable).suffix.lower() != '.exe' else None
        for path,digest in list(files.items()):
            pin(path,digest)
        passed = True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report=dict(passed=passed,scope='Independent source-only review of constructor cleanup-key repair v6→v7 against exact successful writer3 prep10. Only direct cleanup namespace, immutable diagnostic admission and lineage pins change; every previous ownership/completeness computation and guard conserved. No validation replay or capture/index/payload access.',old_validator=str(ROOT/'tools/m4-constructor-original/validate_v6.py'),new_validator=str(ROOT/'tools/m4-constructor-original/validate_v7.py'),producer_preparation_sha256='22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe',successful_writer_execution_sha256='cac188db72cb1f5010d04706b52e95afaa4247fab577d6239e726a55bf6751b4',producer_cleanup_prefix='cleanup/<sequence>/constructor-owner-<serial>',obsolete_validator_cleanup_prefix='constructor-prerequisites/cleanup/<sequence>/constructor-owner-',corrected_validator_cleanup_prefix='cleanup/<sequence>/constructor-owner-',guards_preserved=dict(unique_serial=True,whole_final_occurrence_metadata=True,actual_live_new_constructor_owner=True,whole_measured_capacity=True,actual_returned_marker_1=True,exhaustive_final_live_new_owner_set=True)if passed else {},entire_source_has_only_three_explicit_changes=passed,strict_validation_outcome_sha256='00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95',outcome_receipt_only=True,capture_reader_opened=False,index_reader_opened=False,worker_executed=False,validation_executed=False,initializer_credit=0,files=files)
        path=out/'report.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(path))))

if __name__=='__main__':
    main(sys.argv[1])
