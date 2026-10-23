"""Finite own native Runtime bootstrap FS head contract, separate from journal values."""
from pathlib import Path
import json,hashlib,struct,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};cases=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 proof=json.loads(pin(R/'reports/m4-138-validation-review/constructor-native36-source-r4/report.json','776630c569db2eeba5bd66dc8392b1e6aed8022262585d1a85987c0166614547').read_bytes());assert proof['passed']and proof['ordinary_reader_closed'];runtime=pin(R/'tools/m4-runtime/runtime.cpp').read_text();header=pin(R/'tools/m4-runtime/runtime.hpp').read_text();assert 'static constexpr std::uint32_t seh_end = 0xffffffff;'in header and 'image_.memory.store<std::uint32_t>(policy_.teb, seh_end);'in runtime and 'if (offset != 0)'in runtime
 build=json.loads(pin(R/'reports/m4-constructor-native/fixture-build-r10/build.json','0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18').read_bytes());assert build['passed']
 for p,h in build['files'].items():
  if p.endswith('runtime.hpp')and 'm4-runtime'in p or p.endswith('runtime.cpp.obj')and 'm4-runtime'in p:pin(p,h)
 for c in proof['cases']:
  case=R/'reports/m4-138-validation-review/constructor-native36-source-r4'/f"{c['branch']}-{c['sequence']}-{c['root']}";inp=json.loads(pin(case/'input.json').read_bytes());f=inp['FS_observed_field'];state=bytes.fromhex(inp['BEFORE_State_hex']);assert struct.unpack_from('<I',state,2168)[0]==f['address']and f['value']==0xffffffff and f['no_prior_FS_write'];assert bytes.fromhex(inp['BEFORE_memory'][str(f['address'])])==struct.pack('<I',0xffffffff);cases.append(dict(branch=c['branch'],sequence=c['sequence'],root=c['root'],own_State_FS_base=f['address'],physical_Runtime_bootstrap_head=0xffffffff,first_actual_read_equals_bootstrap=True,no_prior_constructor_FS_write=True,whole_TIB_claim=False))
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='36 current native own FS head input equals explicitly authored Runtime bootstrap sentinel; first read is verification, not arbitrary source input. Full Session carry and source/compiled-body provenance remain separate.',cases=cases,canonical_reader_opened=False,ordinary_capture_reader_opened=False,whole_TIB_claim=False,source_AFTER_seed=False,initializer_credit=0,whole_input_carry_policy_acceptance=False,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
