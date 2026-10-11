"""Freeze matched caller workers/comparison; no launch or payload reads."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
OSH='fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f';OBH='14e3040ee8aa42f014a07d042bf3bab06d3565006b9ce5a2dfb39cf952893b52'
NSH='d42a831e4d123021470ba99bc6589081f90dbf1f3e3bab5664c76356ab630bc6';NBH='5cfc72f299317152c64b2d196dc1e6318e69fb89387a98603ba32d56d509372a'
RECIPE='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281';HEADER='bdef49734a96c155a3e6a4e2e0a098bfcdc326746e16276dd219541882895182'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 for rel,h in [('original-preparation-r8/report.json',OSH),('original-build-r8/build.json',OBH),('fixture-preparation-r4/report.json',NSH),('fixture-build-r3/build.json',NBH),('common-caller-preparation-r1/report.json',RECIPE),('comparison-execution-preparation-r3/report.json','c1cb517a8333399a52954181083b636676b3ab12a120b09b9f7ef7bed83ef4ea')]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 original=pin(T/'run_original_v3.py','e6cafcbe42f728ba8e68913fd01f991061a3bb4335786fa7483c286b04e59e5d').read_text()
 for a,b in [('37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6',OSH),('cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7',OBH),('original-preparation-r6/report.json','original-preparation-r8/report.json'),('original-build-r6/build.json','original-build-r8/build.json')]:original=once(original,a,b)
 original=original.replace('original6','original8 matched caller')
 original=once(original,"  for d in(prep,build):", "  need(admission['common_caller_recipe_sha256']=='"+RECIPE+"'and prep['common_caller_recipe_sha256']=='"+RECIPE+"','Actual independent common caller recipe admission');\n  for d in(prep,build):")
 original=once(original,'original_worker_invocations=launched,','original_worker_invocations=launched,role="single_original8_common_transport",common_caller_recipe_sha256="'+RECIPE+'",')
 native=pin(T/'run_fixture_v2.py','5bd016198a61486e33849cd58d9006cfb46c446b5d97b32eafcf25eba6f07309').read_text()
 for a,b in [('ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee',NSH),('d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42',NBH),('fixture-preparation-r3/report.json','fixture-preparation-r4/report.json'),('fixture-build-r2/build.json','fixture-build-r3/build.json')]:native=once(native,a,b)
 native=once(native,'  for d in(build,prep):',"  need(admission['common_caller_recipe_sha256']=='"+RECIPE+"'and prep['common_caller_recipe_sha256']=='"+RECIPE+"','Actual independent complete common caller recipe admission');\n  for d in(build,prep):")
 native=once(native,"   manifest={str(p.relative_to(capture))", "   need(struct.unpack('<8I',pin(capture/'common-caller/application.bin').read_bytes())==(1,1,0x4af240,0x20001800,0xfffffff0,512,28,4096)and pin(capture/'common-caller/header-sha.txt').read_text()=='"+HEADER+"','Actual single independently authored matched native caller application');\n   manifest={str(p.relative_to(capture))")
 native=once(native,'actual_workers_launched=launched,','actual_workers_launched=launched,role="direct_ordinary_closed_native3_common",common_caller_recipe_sha256="'+RECIPE+'",')
 compare=pin(T/'compare_v4.py','85c294f281d96756f2dc5e2319fd32f748da68a3e3d566af5d8f408c129322ea').read_text()
 for a,b in [('37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6',OSH),('cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7',OBH),('ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee',NSH),('d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42',NBH)]:compare=once(compare,a,b)
 compare=compare.replace('single_original6_transport','single_original8_common_transport').replace('direct_ordinary_closed_native2','direct_ordinary_closed_native3_common').replace('original6/native2','original8/native3 common').replace('direct closed-native2','direct closed-native3 common').replace('closed ordinary native2','closed ordinary native3 common').replace('manifest-bound native2','manifest-bound native3 common')
 caller_helper='''def common_caller_validation(original,native,o,n):
 expected=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,0x4af240);need(o['before']==n['before']==expected,'Both actual complete root BEFORE CPUs equal the single independent common recipe')
 recipe={}
 for key,extent in [('CPU',40),('FX',512),('ENV',28),('stack',4096)]:
  a=original('common-caller/authored-'+key+'.bin');b=native('common-caller/authored-'+key+'.bin');need(len(a)==len(b)==extent and a==b,'Whole identical independently authored caller '+key);recipe[key]=a
 need(cpu(recipe['CPU'])==expected and original('common-caller/header-sha.txt')==native('common-caller/header-sha.txt')==b'@HEADER@','Same frozen caller header consumed by both actual fixtures')
 need(words(original('common-caller/application.bin'),8)==(1,1,0x4af240,0x20001800,0x410a80,512,28,4096)and words(native('common-caller/application.bin'),8)==(1,1,0x4af240,0x20001800,0xfffffff0,512,28,4096),'Each own real bootstrap is followed by exactly one authored caller application and its own terminal token')
 OF=o['record'][116:628];NF=native('phase-0/before/FX.bin');need(fx_arch(OF)==fx_arch(NF)==fx_arch(recipe['FX']),'Both actual BEFORE floating-point architectural fields equal the common authored recipe; raw hardware capability/reserved bytes retained')
 OE=o['record'][2164:2192];NE=native('phase-0/before/ENV-from-State.bin');need(OE==NE==recipe['ENV'],'Whole original guest ENV and explicit native persistent-State ENV fields equal the independently authored caller')
 page=PAGES.index(0x20001000);OS=o['record'][2276+page*4096:2276+(page+1)*4096];NS=native('phase-0/before/stack.bin');base=bytearray(recipe['stack']);offset=0x20001800-0x20001000;ob=base[:];nb=base[:];struct.pack_into('<I',ob,offset,0x410a80);struct.pack_into('<I',nb,offset,0xfffffff0);need(OS==ob and NS==nb,'Every whole caller stack byte equals its authored recipe with only the independently witnessed terminal word correspondence')
 need(len(original('common-caller/bootstrap-CPU.bin'))==40 and len(original('common-caller/bootstrap-FX.bin'))==512 and len(original('common-caller/bootstrap-ENV.bin'))==28 and len(original('common-caller/bootstrap-pages.bin'))==176128,'Whole original own real bootstrap BEFORE retained before projection')
 for f,size in [('CPU.bin',40),('FX.bin',512),('State.bin',3504),('stack.bin',4096),('ENV-from-State.bin',28)]:need(len(native('common-caller/bootstrap/'+f))==size,'Whole own native actual bootstrap BEFORE retained')
 return dict(complete_common_CPU_before=True,architectural_FX_before=True,whole_ENV_before=True,whole_stack_before=True,one_application_per_branch=True,terminal_tokens=dict(original=0x410a80,native=0xfffffff0),recipe_header_sha256='@HEADER@',native_ENV_role='Typed projection of actual persistent guest State under empty-tag guard; raw State/FX/API hardware retained',source_after_seed=False,per_source_reseed=False,whole_native_ENV_after=delta(o['record'][2192:2220],native('phase-0/after/ENV-from-State.bin')))

'''.replace('@HEADER@',HEADER)
 compare=once(compare,'def main(original_report,',caller_helper+'def main(original_report,')
 compare=once(compare,"  transport=pin(Path(oe['run']['capture'])", "  need(gate['common_caller_recipe_sha256']=='"+RECIPE+"'and oe['common_caller_recipe_sha256']==ne['common_caller_recipe_sha256']=='"+RECIPE+"'and oe['role']=='single_original8_common_transport'and ne['role']=='direct_ordinary_closed_native3_common','Explicit matched caller execution/reader roles and complete independent recipe');pin(R/'reports/m4-version-source/common-caller-preparation-r1/report.json','"+RECIPE+"');\n  transport=pin(Path(oe['run']['capture'])")
 compare=once(compare,"n=native_validation(native);need(o['API_count']", "n=native_validation(native);common=common_caller_validation(original,native,o,n);need(o['API_count']")
 compare=once(compare,'entry=dict(level=level,original_isolated_provider=', 'entry=dict(level=level,complete_common_caller=common,original_isolated_provider=')
 compare=once(compare,"pin(R/'tools/m4-version-source/derive_compare_v4.py');pin(__file__)","pin(R/'tools/m4-version-source/derive_compare_v4.py');pin(R/'tools/m4-version-source/compare_v4.py','85c294f281d96756f2dc5e2319fd32f748da68a3e3d566af5d8f408c129322ea');pin(R/'tools/m4-version-source/prepare_common_controllers_v1.py');pin(__file__)")
 compare=compare.replace('common_authored_caller_pair_required_for_endpoint_equivalence=True','common_authored_caller_pair_required_for_endpoint_equivalence=False,matched_common_caller_checked=validation_passed')
 outputs=[]
 for name,s,role in [('run_original_common_v1.py',original,'single_original8_common_transport'),('run_fixture_common_v1.py',native,'direct_ordinary_closed_native3_common'),('compare_common_v1.py',compare,'sole_original8_reader_plus_native3_ordinary')]:
  p=T/name;assert not p.exists();p.write_text(s);compile(s,str(p),'exec');pin(p);outputs.append(dict(path=str(p),sha256=sha(p),role=role))
 pin(__file__);out.mkdir(parents=True);d=dict(passed=True,scope='Matched original8/native3 one-root common caller controllers and sole original strict reader comparator; preparation only',tools=outputs,common_caller_recipe_sha256=RECIPE,original_preparation_sha256=OSH,original_build_sha256=OBH,native_preparation_sha256=NSH,native_build_sha256=NBH,common_caller_header_sha256=HEADER,worker_admission_requires_common_recipe=True,reader_admission_requires_common_recipe=True,original_workers=1,native_workers=2,sequential_writer_slots=True,original_reader_count=1,native_archive_readers=0,reader_roles=['single_original8_common_transport','direct_ordinary_closed_native3_common'],full_architecture_hardware_coincidence_claimed=False,raw_endpoints_modified=False,blanket_masks=False,source_original_equivalence=False,initializer_credit=0,original_executed=False,native_executed=False,archive_reader_opened=False,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),tools=outputs,executed=False)))
if __name__=='__main__':main(sys.argv[1])
