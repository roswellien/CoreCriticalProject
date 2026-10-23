"""Diagnose exact loaded-image/guest reservation collision and prepare linker-only fix."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
def main():
 out=R/'reports/m4-original141/imagebase-preparation-r1';out.mkdir();files={};images=[]
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;files[str(p)]=v;return p
 for rel in ['m4-original141/build-r1','m4-startup138-original/build-r5','m4-138-validation-review/constructor-input-capture-build-r2']:
  bpath=pin(R/'reports'/rel/'build.json');b=json.loads(bpath.read_bytes());im=PEImage(pin(b['worker'],b['worker_sha256']).read_bytes());assert im.machine==0x14c
  images.append(dict(build=str(bpath),preferred_base=im.image_base,image_size=im.size_of_image,image_end=im.image_base+im.size_of_image,sections=im.sections,guest_stack_intersects=im.image_base<0x20010000 and 0x20000000<im.image_base+im.size_of_image))
 assert [i['guest_stack_intersects']for i in images]==[True,False,False]
 current=R/'reports/m4-original141/source-preparation-r3';parent=json.loads(pin(current/'report.json').read_bytes())
 for p,h in parent['files'].items():pin(p,h)
 broker=pin(current/'original_broker.hpp').read_text();m=re.search(r'array<std::uint32_t,36> bases\{([^}]+)\}',broker);assert m
 bases=[int(x,16)for x in m[1].split(',')];assert len(set(bases))==len(bases)==36 and all(b%65536==0 for b in bases)
 assert 'reservation_size=65536' in broker and 'VirtualAllocEx(child.value,pointer,reservation_size,MEM_RESERVE,PAGE_NOACCESS)==pointer'in broker
 failure=R/'reports/m4-original141/root-capture-execution-r1';fr=json.loads(pin(failure/'report.json','bbbb53b0a943e6f3bef516c529a0ee22f4cc17a9b4e1bc430bd747275af2e338').read_bytes());assert not fr['passed']
 stderr=pin(failure/'run/stderr.bin').read_bytes();assert b'Pre-CRT guest reservation failed base=536870912 Win32=487'in stderr
 size=images[0]['image_size'];base=0x28000000;assert base%65536==0 and base+size<0x40000000
 assert all(not(base<a+65536 and a<base+size)for a in bases)
 normal=pin(current/'constructor_normal.hpp').read_text();assert 'ConstructorNormalSnapshot constructor_normal_records[256]{}'in normal and 'sizeof(ConstructorNormalSnapshot)==189108'in normal
 child=R/'reports/m4-original141/source-preparation-r4';assert not child.exists();child.mkdir();identical=[]
 for p in sorted(current.iterdir()):
  if not p.is_file()or p.name in('report.json','pins.json'):continue
  raw=pin(p).read_bytes()
  if p.name=='CMakeLists.txt':
   assert raw.count(b'/BASE:0x18000000')==1;changed=raw.replace(b'/BASE:0x18000000',b'/BASE:0x28000000');assert changed.replace(b'/BASE:0x28000000',b'/BASE:0x18000000')==raw
  else:changed=raw;identical.append(p.name)
  (child/p.name).write_bytes(changed);pin(child/p.name)
 oldpins=json.loads(pin(current/'pins.json').read_bytes());newpins={}
 for p,h in oldpins['files'].items():
  p=Path(p);target=child/p.name if p.parent==current else p;newpins[str(target)]=sha(target);pin(target,newpins[str(target)])
 # Admit exact new physical compiler inputs and retain complete historical parent proofs.
 for p in child.iterdir():newpins[str(p)]=sha(p)
 newpins[str(current/'report.json')]=sha(current/'report.json');newpins[str(Path(__file__).resolve())]=sha(__file__)
 (child/'pins.json').write_text(json.dumps(dict(files=newpins),indent=2)+'\n',encoding='utf-8');pin(child/'pins.json');pin(__file__)
 r={k:v for k,v in parent.items()if k!='files'}
 r.update(passed=True,prepared_only=True,physical_code_change=False,linker_preferred_base_changed=True,old_preferred_base=0x18000000,new_preferred_base=base,prior_image_size=size,prior_image_end=images[0]['image_end'],projected_new_image_end=base+size,exact_CMake_one_delta_inverse=True,whole_payload_byteidentical_except_CMake=identical,observation_capacities_unchanged=True,source_parent_report=str(current/'report.json'),source_parent_sha256=sha(current/'report.json'),build_admitted=False,build_executed=False,worker_admitted=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files)
 cp=child/'report.json';cp.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');pin(cp)
 diagnostic=dict(passed=True,diagnosis='Current preferred x86 observer image overlaps exactly the0x20000000 guest reservation; immutable PE .data virtual footprint covers that64KiB span. Successful138/37 images do not. No duplicate broker bases; keep allocation rejection unchanged.',actual_failure_before_CRT=True,failed_capture_preserved=True,images=images,broker_unique_bases=bases,constructor_normal_bytes=256*189108,fix='Linker preferred observer image base only18000000->28000000; retain all source/ASM/guest pages/176 code-page list/43+26+global5F2000 inputs and every capture/ownership cap.',source_preparation=str(cp),source_preparation_sha256=sha(cp),rebuild_required=True,projected_layout_only=True,actual_new_PE_layout_pending=True,new_whole_linked_relocation_review_pending=True,worker_launch_admitted=False,compiler_launched=False,reader_opened=False,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(diagnostic,indent=2)+'\n',encoding='utf-8');print(sha(p),sha(cp))
if __name__=='__main__':main()
