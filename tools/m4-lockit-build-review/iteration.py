"""Review historical archive identity reuse for local compile/run iterations.

This never opens historical archive payloads and grants no acceptance credit.
"""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-build-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p):
  p=Path(p).resolve();pins[str(p)]=sha(p);return p
 base=ROOT/'tools/m4-joint-startup124';build=pin(base/'build_v2.py').read_text();run=pin(base/'run_v2.py').read_text();generator=pin(base/'derive_local_iterations_v2.py').read_text();pin(base/'build.py');pin(base/'run.py');pin(base/'build_v2.ps1')
 for source in [build,run,generator]:ast.parse(source)
 assert "inherited_archives={pp:h for pp,h in pins.items() if Path(pp).suffix=='.mwb'}"in build
 assert "if pp not in inherited_archives:assert sha(pp)==h,(pp,h)"in build
 assert "if pp not in inherited_archives:assert sha(pp)==h,('Source changed',pp)"in build
 assert "'inherited_capture_payload_hashes_reused':inherited_archives,'full_dependency_acceptance_rehash_required':True,'guest_executed':False"in build
 assert "if Path(p).suffix=='.mwb':"in run and 'Path(p).is_file()'in run
 assert 'inputs=[p for p in pins if p not in inherited_archives]'in run
 assert "if p not in inherited_archives:assert sha(p)==h,('Unchanged input',p)"in run
 assert "records=ds.DirectSet(capture/'transport.json',pin)"in run and "worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256'])"in run
 assert 'inherited_capture_payload_hashes_reused=inherited_archives,full_dependency_acceptance_rehash_required=True,initializer_credit=False' in run
 assert 'sources=dict(pins)'in build and "'sources':sources"in build and 'files=pins' in run
 # The native worker receives only its exact frozen PE inputs and fresh output.
 assert 'run_stage(list(map(str,(worker,game,provider,crt,mfc,capture)))'in run
 prep=ROOT/'reports/m4-joint-startup124/preparation-r3';p=json.loads(pin(prep/'report.json').read_bytes());manifest=json.loads(pin(prep/'pins.json').read_bytes())['files']
 historic={k:h for k,h in manifest.items()if Path(k).suffix=='.mwb'}
 assert historic and all(len(h)==64 and all(c in '0123456789abcdef'for c in h)and Path(k).is_file()for k,h in historic.items())
 assert all(Path(x).suffix=='.obj'for level in p['objects'].values()for x in level)
 direct=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py').read_text();assert "path = pin(self.path.parent / name, part['sha256'])"in direct and "reader = CaptureBundle(path, part['sha256'])"in direct and 'reader.read_bytes(logical)'in direct
 # Existing mandatory acceptance policy physically reads every normalized
 # dependency, including historical archives; the124 gate remains to be authored.
 accept=pin(ROOT/'tools/m4-joint-startup120/accept.py').read_text();verify=pin(ROOT/'tools/m4-pipeline/manifests.py').read_text()
 assert 'physical=verify_manifest(PINS)'in accept and "not physical['metadata_only_cache_used']"in accept
 assert "for path, expected in normalized_files.items():\n        with Path(path).open('rb') as stream:"in verify and "actual = hashlib.file_digest(stream, 'sha256').hexdigest()"in verify and 'actual != expected'in verify
 assert '.mwb'not in verify
 pin(__file__);r=dict(passed=True,scope='Local iteration archive hash reuse review only; inherited payload hashes are retained identities, current code/input/output hashing remains mandatory. No execution or acceptance credit.',historical_archive_identities=len(historic),historical_archive_bytes=sum(Path(x).stat().st_size for x in historic),historical_payloads_opened=False,changed_code_and_PE_inputs_physically_hashed=True,current_worker_outputs_fully_validated_by_DirectSet=True,historical_identities_retained_in_dependency_union=True,local_iteration_initializer_credit=False,full_final_dependency_rehash_required=True,final124_acceptance_script_reviewed=False,final124_acceptance_requirement='Carry build/run reused identity manifests into the exact conflict-normalized final union and invoke verify_manifest with no archive exemption before initializer credit.',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),historical_archives=r['historical_archive_identities'],historical_archive_bytes=r['historical_archive_bytes'])))
if __name__=='__main__':main(sys.argv[1])
