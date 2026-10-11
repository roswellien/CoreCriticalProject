"""Admit the additive five-page FPS fixture without changing carried state."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-tree-review/review_widget_extensions.py'
assert hashlib.sha256(prior.read_bytes()).hexdigest()=='48b57127bcd33d29a431010322380b36c2847523ca87b8f14c1f456cb0405944'
text=prior.read_text()
for a,b in {
'e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc':'bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0',
'fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7':'636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a',
"'fixture-preparation-r1'":"'fixture-preparation-r2'",
"'fixture-build-r1'":"'fixture-build-r2'",
"'?borrow_widget_onexit@'":"'?'+'borrow_widget_onexit@','?map_current_formatter_sources@'",
}.items():
 assert a in text,a;text=text.replace(a,b)
extra=r'''
  if kind=='fps':
   relation=read(R/'tools/m4-fps-native/fixture-source-relations-v2.json',closure=False)
   before=pin(relation['parent'],relation['parent_sha256']).read_text()
   assert len(relation['changes'])==4
   for change in relation['changes']:
    assert change['count']==1 and before.count(change['before'])==1
    before=before.replace(change['before'],change['after'],1)
   assert before==cpp==pin(relation['target'],relation['target_sha256']).read_text()
   assert cpp.index('registry.bootstrap();map_current_formatter_sources(r,crt,writer);')<cpp.index('AcceptedServices services(r,registry);')
   for token in ('if(e.reason()!=MemoryFaultReason::unmapped)throw;absent=true;','if(absent){r.memory().map','r.memory().protect({p.address},static_cast<Permissions>(p.permissions))','need(before==after,','if(absent)need(std::equal(current.begin(),current.end(),physical.begin())','provider-source-page-','initial-own-input",false'):
    assert token in cpp,token
   meta=read(prepdir/'provider-page-contracts.json',closure=False);pages=meta['pages']
   assert len(pages)==5 and [x['address']for x in pages]==[0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000]
   nt=struct.unpack_from('<I',crt.data,0x3c)[0];n=struct.unpack_from('<H',crt.data,nt+6)[0];os=struct.unpack_from('<H',crt.data,nt+20)[0]
   expected=[]
   for page in pages:
    matches=[]
    for i in range(n):
     at=nt+24+os+i*40;vs,va,rs,ro=struct.unpack_from('<IIII',crt.data,at+8);flags=struct.unpack_from('<I',crt.data,at+36)[0]
     address=crt.image_base+va
     if address<=page['address'] and page['address']+4096<=address+rs:
      rights=(1 if flags&0x40000000 else 0)|(2 if flags&0x80000000 else 0)|(4 if flags&0x20000000 else 0)
      matches.append((ro+page['address']-address,rights))
    assert matches==[(page['file_offset'],page['permissions'])]
    raw,offset=physical(crt,page['address'],4096)
    assert offset==page['file_offset'] and hashlib.sha256(raw).hexdigest()==page['sha256'] and pin(page['path'],page['sha256']).read_bytes()==raw
    expected.append((page['address'],offset,page['permissions'],page['sha256']))
    counts['whole_new_owned_provider_PE_pages']+=1
   h=pin(prepdir/'provider_pages.hpp').read_text()
   actual=[(int(a),int(o),int(p),s)for a,o,p,s in re.findall(r'\{(\d+),(\d+),(\d+),"([0-9a-f]{64})"\}',h)]
   assert actual==expected and str((prepdir/'provider_pages.hpp').resolve())in files
   contractrows=read(compdir/'contracts.json',closure=False)['instructions']
   for row in contractrows:
    if row['pc']<crt.image_base:continue
    raw=bytes.fromhex(row['bytes_hex']);owners=[x for x in pages if x['address']<=row['pc'] and row['pc']+len(raw)<=x['address']+4096]
    assert len(owners)==1
    assert physical(crt,row['pc'],len(raw))[0]==raw
    counts['formatter_physical_rows_inside_admitted_pages']+=1
   ctl=read(R/'reports/m4-fps-native/controller-preparation-r3/report.json','244bcd1bd375b13d883f1239f317838f8f4c7aad5efeb684d6c389b36c71dad7')
   assert ctl['build_sha256']==BH[kind]and ctl['preparation_sha256']==PH[kind] and ctl['actual_worker_launches']==0
   controller=pin(ctl['controller'],ctl['controller_sha256']).read_text()
   for token in ("for level in('O0','O2')","timeout_seconds=180","all_workers_terminal=True","format-dispatches.bin","provider-mapping","if row[4]:need(after==physical","else:need(pin(Path(str(stem)+'-before.bin')).read_bytes()==after"):
    assert token in controller,token
   pin(R/'tools/m4-tree-review/review_widget_extensions.py')
'''
needle="  bindings=pin(prepdir/'widget_bindings.hpp').read_text()"
assert text.count(needle)==1;text=text.replace(needle,extra+needle)
exec(compile(text,str(prior),'exec'),globals())

