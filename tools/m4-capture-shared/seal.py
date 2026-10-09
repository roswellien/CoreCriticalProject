"""Freeze current pilot sources and physically recheck the exact evidence union."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'tools/m4-pipeline')]
from capture_bundle import sha_file
from manifests import verify_manifest,normalized
def main(directory):
 out=Path(directory).resolve()
 if out.parent!=R/'reports/m4-capture-shared' or out.exists():raise ValueError('Fresh shared pilot seal')
 out.mkdir();(out/'sources').mkdir();files={};reports={};seen={}
 def add(path,expected=None):
  path=Path(path).resolve();actual=sha_file(path)
  if expected is not None and actual!=expected:raise ValueError('Pinned pilot input changed '+str(path))
  key=normalized(str(path))
  if key in seen and seen[key]!=actual:raise ValueError('Conflicting pilot dependency')
  seen[key]=actual;files[str(path)]=actual;return path
 for label,relative in [('native_build','build-r1/build.json'),('functional_validation','validation-r3/report.json'),('writer_and_byte_benchmark','benchmark-r2/report.json'),('final_reader_benchmark','reader-measure-r1/report.json')]:
  path=add(R/'reports/m4-capture-shared'/relative);value=json.loads(path.read_text(encoding='utf-8-sig'))
  if not value['passed']:raise ValueError('Passed measured pilot gate required')
  reports[label]={'path':str(path),'sha256':files[str(path)]}
  if 'files' in value:
   for name,sha in value['files'].items():add(name,sha)
  else:
   for field in ('sources','artifacts','objects','tools','libraries','compiler_read_headers'):
    for name,sha in value[field].items():add(name,sha)
 for source in sorted(H.iterdir()):
  if source.is_file():add(source);copy=out/'sources'/source.name;copy.write_bytes(source.read_bytes());add(copy,files[str(source)])
 original_reader=add(R/'tools/m4-pipeline/capture_shared.py');copy=out/'sources/capture_shared_initial.py';copy.write_bytes(original_reader.read_bytes());add(copy,files[str(original_reader)])
 # Initial failed checker and benchmark remain honest historical artifacts.
 failures={}
 for label,relative in [('DF_checker_scope','validation-r1/report.json'),('canonical_context_manager','benchmark-r1/report.json')]:
  path=add(R/'reports/m4-capture-shared'/relative);value=json.loads(path.read_bytes());failures[label]={'path':str(path),'sha256':files[str(path)],'passed':value['passed'],'reason':value['error']}
 report={'passed':True,'format_adopted':False,'transport_only':True,'game_executed':False,'native_transport_executed':True,'reports':reports,'failure_history':failures,'hardware_pairs':120,'actual_writer_refusals':54,'malformed_and_unknown_format_refusals':63,'held_Windows_readonly_refusals':12,'exact_full_byte_records':32000,'final_reader':'tools/m4-capture-shared/capture_shared_v4.py','physical_scope':'Part-local blobs; contiguous unique extents; max200000 logical records/max256MiB blob/max64MiB index/max2GiB unique payload per part. Logical referenced payload may exceed2GiB. Full byte comparison follows lookup-key matches.','authentication':'External whole archive SHA and canonical index SHA, every unique blob actual SHA once into immutable bytes, exact inventory/count/ref/extents; held Windows no-write/delete handles for manifest and parts; no shared mutable view.','compatibility':{'proven':'Exact names, full data bytes, logical data access checksum, explicit old-format refusal, new words(I/Q) strict implementation','not_drop_in':['Canonical DirectSet.value is not exposed; pilot uses meta.','Canonical .bundles is not exposed; pilot uses readers.','Canonical private bundle._entries[name]=(offset,size) differs from pilot blob_id representation.','No entire production semantic gate was run through the new format.','No explicit dispatch/adoption or producer substitution.']},'hardware_scope':'Actual rich ENV28/CW/SW/FTW/raw80x8/MXCSR/nonvolatile XMM6..15, ABI-clear DF equality and caller LastError; DF1 and volatileXMM0..5 equality not claimed.','performance_scope':'Single measured same-input trials, OS cache uncontrolled. Retained71 subset converted read-only; original archives unchanged. Writer timing/reader startup/steady access/Windows PeakWorkingSetSize are recorded separately. No general end-to-end game speedup claim.','next_gate':'Root independent pilot review; future explicit consumer metadata adapters/versioning and unchanged complete semantic gates before production adoption.','files':files,'current_physical_closure':verify_manifest(files)}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'physical_dependencies':report['current_physical_closure']['unique_physical_dependencies'],'format_adopted':False}))
if __name__=='__main__':main(*sys.argv[1:])
