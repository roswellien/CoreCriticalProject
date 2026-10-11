"""Freeze bounded physical source-page admission and unchanged seven routes."""
from pathlib import Path
import hashlib,json,shutil,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh mapped-source fixture recipe');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact additive input '+str(p));pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-fps-native/fixture-preparation-r1/report.json','e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc');prior=json.loads(pp.read_bytes());need(prior['passed'],'Passed old recipe with failed runtime preserved')
 for p,h in prior['files'].items():pin(p,h)
 copies=[]
 for name_ in('inherited_main.cpp','widget_bindings.hpp','Runtime-physical-source-spans.json'):
  p=pin(pp.parent/name_);q=out/name_;shutil.copyfile(p,q);need(sha(q)==sha(p),'Unchanged actual seven routes and accepted library include');copies.append(dict(source=str(p),target=str(q),sha256=sha(p)));pin(q)
 source=pin(R/'tools/m4-fps-native/fixture_v2.cpp');shutil.copyfile(source,out/'fixture.cpp');pin(out/'fixture.cpp')
 crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');b=crt.read_bytes();nt=struct.unpack_from('<I',b,0x3c)[0];ns=struct.unpack_from('<H',b,nt+6)[0];optional=struct.unpack_from('<H',b,nt+20)[0];need(struct.unpack_from('<H',b,nt+24)[0]==0x10b,'Current provider PE32');base=struct.unpack_from('<I',b,nt+24+28)[0];need(base==0x78000000,'Exact owning CRT image base');sections=[]
 for i in range(ns):
  off=nt+24+optional+40*i;vs,va,rs,ro=struct.unpack_from('<IIII',b,off+8);flags=struct.unpack_from('<I',b,off+36)[0];sections.append(dict(name=b[off:off+8].rstrip(bytes(1)).decode(),address=base+va,virtual_size=vs,raw_size=rs,file_offset=ro,flags=flags))
 pages=[]
 for address in(0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000):
  owners=[v for v in sections if v['address']<=address and address+4096<=v['address']+v['raw_size']];need(len(owners)==1,'Whole provider source page has one own physical section');v=owners[0];offset=v['file_offset']+address-v['address'];payload=b[offset:offset+4096];need(len(payload)==4096,'Whole own physical page payload');permissions=(1 if v['flags']&0x40000000 else 0)|(2 if v['flags']&0x80000000 else 0)|(4 if v['flags']&0x20000000 else 0);need(permissions in(1,3,5),'Admitted exact PE source permissions');q=out/f'physical-provider-page-{address}.bin';q.write_bytes(payload);pin(q);pages.append(dict(address=address,file_offset=offset,permissions=permissions,section=v,bytes=4096,sha256=sha(q),path=str(q)))
 cp=pin(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');contracts=json.loads(cp.read_bytes());rows=contracts['instructions'];instruction_joins=[]
 for row in rows:
  if row['pc']<base:continue
  size=len(bytes.fromhex(row['bytes_hex']));owner=[v for v in pages if v['address']<=row['pc'] and row['pc']+size<=v['address']+4096];need(len(owner)==1,'Every provider source instruction fits a declared current page');v=owner[0];payload=Path(v['path']).read_bytes();need(payload[row['pc']-v['address']:row['pc']-v['address']+size]==bytes.fromhex(row['bytes_hex']),'Every provider physical source instruction matches current own page');instruction_joins.append(dict(PC=row['pc'],page=v['address'],bytes=size,bytes_hex=row['bytes_hex']))
 need(instruction_joins and any(v['page']==0x78023000 for v in instruction_joins),'Actual new vsprintf source page is explicitly admitted')
 h=['#pragma once','#include <array>','struct FpsProviderPage {unsigned address,file_offset,permissions;const char*sha256;};','inline constexpr const char*fps_crt_sha="'+sha(crt)+'";','inline constexpr std::array<FpsProviderPage,5>fps_provider_pages{{']
 for p in pages:h.append('{%d,%d,%d,"%s"},'%(p['address'],p['file_offset'],p['permissions'],p['sha256']))
 h.append('}};');q=out/'provider_pages.hpp';q.write_text('\n'.join(h)+'\n');pin(q)
 q=out/'provider-page-contracts.json';q.write_text(json.dumps(dict(pages=pages,physical_instruction_joins=instruction_joins,raw_dispatch_cells=[0x780103fa,0x7802e330,0x7802e336,0x7802e340,0x7802e343],carried_dynamic_cells=[0x780371a8,0x7803727b,0x7803728f,0x78037295],all_existing_provider_payloads_preserved=True,existing_permissions_not_changed=True,existing_permissions_not_observed=True,initial_unmapped_pages_are_absent=True),indent=2)+'\n');pin(q)
 for p in(__file__,R/'tools/m4-fps-native/derive_fixture_v2.py',R/'tools/m4-fps-native/fixture-source-relations-v2.json'):pin(p)
 report=dict(prior);report.update(passed=True,scope='Seven-route fixture with finite own physical CRT source-page admission after authentic registry bootstrap; existing whole provider payloads and rights preserved, no observation/AFTER seed',parent_preparation_sha256=sha(pp),prior_copy_relations=copies,physical_provider_pages=5,physical_provider_instructions=len(instruction_joins),provider_input_encoding='Guest Permissions read=1/write=2/execute=4 derived exact physical PE sections',existing_provider_state_and_permissions_preserved=True,whole_provider_pages_exported=True,provider_DllMain_modeled=False,native_executed=False,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])
