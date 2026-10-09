"""Read existing independent hardware evidence; no native worker or API run."""
import hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-heap-version-host-review'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 out=BASE/'diagnosis-r1';assert not out.exists();out.mkdir(parents=True)
 evidence=ROOT/'reports/m4-crt-heap-version-review/native-r1/actual-O0'
 pins={};samples=[]
 for n in (1,3,7,43,46,47):
  row=evidence/f'case-{n}';a=row/'writer-host-before.bin';b=row/'writer-host-after.bin'
  before,after=a.read_bytes(),b.read_bytes();assert len(before)==len(after)==544
  pins[str(a)]=sha(a);pins[str(b)]=sha(b)
  samples.append(dict(case=n,seed_top=3 if n%2 else 7,seed_depth=(0,1,3,7)[n%4],
   before_ENV28=before[512:540].hex(),after_ENV28=after[512:540].hex(),
   before_legacy_metadata=before[524:538].hex(),after_legacy_metadata=after[524:538].hex(),
   before_FXSAVE_pointer_opcode=before[6:24].hex(),after_FXSAVE_pointer_opcode=after[6:24].hex(),
   before_status=struct.unpack_from('<H',before,2)[0],before_exception_summary=bool(before[2]&0x80),
   differing_offsets=[i for i in range(544) if before[i]!=after[i]],
   before_metadata_matches_explicit_seed=before[524:538]==bytes.fromhex('4433221123001d01887766552b00'),
   inner_writer_snapshot_available=(row/'writer-record.bin').exists(),
   heap_version_entry_evidence_available=(row/'entry-host-before.bin').exists()))
 failed=samples[-1];assert failed['before_metadata_matches_explicit_seed']
 assert failed['differing_offsets']==[524,525,526,527,528,530,531,532,533,534,535,536]
 assert not failed['heap_version_entry_evidence_available']
 assert all(x['differing_offsets']==[] for x in samples[:-1])
 for path in ('tools/m4-crt-heap-version-review/controls.cpp','tools/m4-crt-heap-version/capture.s',
  'reports/m4-crt-heap-version/preparation-r2/composition.cpp','reports/m4-crt-heap-version/preparation-r2/main_v2.inc',
  'tools/m4-crt-fdiv/registry.cpp','tools/m4-crt-fdiv/registry.hpp',
  'reports/m4-crt-heap-version-review/compiled-r2/flat-build.json',
  'reports/m4-crt-heap-version-review/native-r1/run-O0/stage.json',
  'reports/m4-crt-heap-version-review/native-r1/run-O0/stdout.bin',
  'reports/m4-crt-heap-version-review/native-r1/run-O0/stderr.bin',__file__):
  p=ROOT/path if not pathlib.Path(path).is_absolute() else pathlib.Path(path);pins[str(p)]=sha(p)
 report=dict(passed=True,scope='Read-only evidence diagnosis; full hardware equality remains required',
  candidate_or_ancestor_changes=False,new_native_execution=False,new_host_API_execution=False,
  samples=samples,definite_findings=[
   'Case47 BEFORE contains the complete intended nonzero legacy environment metadata.',
   'Case47 AFTER zeros only the legacy instruction/data pointers, opcode and selectors; all other captured bytes match.',
   'Failure is in the frozen FDIV writer boundary before any heap-version entry evidence.',
   'Prior identical top3/depth7 cases retain all metadata.',
   'FXSAVE64 pointer/opcode fields are zero while FNSTENV fields are nonzero in the sampled masked-ES0 inputs.'],
  registry_host_observation=dict(name='AMD Ryzen 7 9700X 8-Core Processor',vendor='AuthenticAMD',
   domain='Read-only registry tool output, not CPUID or context-switch attestation'),
  primary_document=dict(url='https://www.amd.com/content/dam/amd/en/documents/processor-tech-docs/programmer-references/26569.pdf',
   title='AMD64 APM Volume5, FXSAVE',retrieval='Official indexed text; direct PDF endpoint returned404',
   relevant_contract='FXSAVE pointer/opcode saving is conditional on exception-summary ES.'),
  inference=dict(possible_cause='Hardware/OS context-save or restore window losing legacy metadata omitted by FXSAVE',
   established=False,context_switch_observed=False),
  next_diagnostic='On boundary failure preserve fd::Registry host_before/after and host_env_before/after via existing read-only getters, alongside outer captures, before restoring the caller.',
  recommendation='Keep all nonzero seeds and complete ENV28 equality. Do not force zero, skip metadata, or mask the failed comparison.',
  current_inputs=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pins[str(p)]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
 print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'))))
if __name__=='__main__':main()
