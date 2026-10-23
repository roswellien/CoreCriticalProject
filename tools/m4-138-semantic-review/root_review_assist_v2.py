"""ROOT-executable ordinary closure/control assist; no semantic main or archive reader."""
from pathlib import Path
from collections import Counter
import ast,copy,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[2]
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(name):
 out=R/'reports/m4-138-semantic-review'/name;need(not out.exists(),'Fresh ordinary assist');out.mkdir(parents=True);pins={};deferred={};controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Ordinary assist only');v=sha(p);need(h is None or v==h,'Physical ordinary input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def closure(p,h=None):
  d=read(p,h)
  for q,v in d.get('files',{}).items():
   q=Path(q)
   if q.suffix.lower()in('.mwb','.mwi','.zip')or q.name in('transport.json','payload.bin','index.json'):deferred[str(q.resolve())]=v
   else:pin(q,v)
  return d
 preparation=closure(R/'reports/m4-138-semantic-review/preparation-r3/report.json','d167fe5da91a37ab141b0b9b1816901c4f279c817260b06684ffdeb32f25e792')
 paired_path=R/'reports/m4-startup138-paired/paired-r5/report.json';source_path=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json'
 paired=closure(paired_path,'5d5a4e5082512617f972e383868004d3c1fbbc79fe1679d365431ab119d8a42e');source=closure(source_path,'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052')
 def output(n):
  p=paired_path.parent/n;return read(p,paired['files'][str(p.resolve())])
 oldprep=closure(R/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 loaded=closure(R/'reports/m4-tree-review/loaded-input138-r1/report.json','379e86517363d5abf25830b3805bb41ff5fe8b104a9e2349131e045c4a5cacec')
 rw=pin(oldprep['loaded_input_page'],oldprep['loaded_input_page_sha256']).read_bytes();iat=pin(oldprep['loaded_IAT_page'],oldprep['loaded_IAT_page_sha256']).read_bytes()
 need(len(rw)==len(iat)==4096 and rw==pin(loaded['whole_native_input_page'],loaded['whole_native_input_page_sha256']).read_bytes(),'Entire retained/native declaration RW equality')
 provider=output('Lockit-provider-page-relations.json');need(len(provider)==9936,'All3providers12x138x2');need(all(r['native_sha256']==sha(oldprep['loaded_IAT_page'])for r in provider if r['page']==0x78146000),'Every actual paired native IAT hash equals complete retained own IAT')
 build=closure(R/'reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47');joint=closure(build['preparation'],build['preparation_sha256']);service=closure(joint['borrowed_service_preparation'],joint['borrowed_service_preparation_sha256']);lib=pin(joint['native_library'],service['files'][str(Path(joint['native_library']).resolve())]);need(service['native_library']==str(lib)and build['files'][str(lib)]==sha(lib),'Actual native build compiles currentFPS service library');need(all(str(lib)in v['compiler_dependencies']for v in build['workers'].values()),'Bothlevels actual compiler dependency includes exact current service library')
 compiled=closure(R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json','eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c')
 cp=R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/compiled-observers.json';cr=read(cp,compiled['files'][str(cp.resolve())]);co=next(r for r in cr if r['symbol']=='lockit_observer_x86 whole source');sp=R/'reports/m4-startup138-original/inherited-source-r5-old4/provider-observer-spans.json';spans=read(sp);need(len(spans)==4,'Exact4currentprovider hooks')
 for p in spans:
  raw=bytes.fromhex(p['original_hex']);need(len(raw)==p['width']and raw[0]==0xe9 and(p['PC']+5+struct.unpack_from('<i',raw,1)[0])&0xffffffff==p['compiled_target'],'Whole observed patch target current compiled provider observer');need(co['address']<=p['compiled_target']<co['address']+co['bytes'],'Target inside actual current linked wholeASM');need(p['compiled_target']-co['address']in(0,193,380,575),'Exact current observer interior entrypoint offsets')
 # Source models and paired artifacts, without loose raw payload access.
 oldgate=closure(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4')
 def art(g,base,n):
  p=base/n;return read(p,g['files'][str(p.resolve())])
 originals=art(oldgate,R/'reports/m4-startup138-original/inherited-source-r5','original-Tree-source-derivations.json');natives=art(source,source_path.parent,'Tree-source-derivations.json');of=art(oldgate,R/'reports/m4-startup138-original/inherited-source-r5','original-Formatting-source-derivations.json');nf=art(source,source_path.parent,'Formatting-source-derivations.json')
 need(len(originals)==6 and all(r['phase']==83 for r in originals)and len(natives)==12 and len(of)==24 and len(nf)==48,'Exact current original/native tree/formatter finite sets')
 need(len(output('Lockit-private-owners.json'))==len(output('Lockit-paired-API-observations.json'))==len(output('Lockit-paired-normal-FS.json'))==96,'Exact actual owner/API/FS finite sets')
 # Reuse the exact retained assertions as text, not a semantic main invocation.
 reviewer=pin(preparation['semantic_reviewer'],preparation['semantic_reviewer_sha256']).read_text()
 start=reviewer.index("        owners=output('Lockit-private-owners.json')");end=reviewer.index('        # Reconstruct all three entire provider pages')
 block='\n'.join(line[8:]if line.startswith('        ')else line for line in reviewer[start:end].splitlines())
 base={n:output(n)for n in('Lockit-private-owners.json','Lockit-paired-API-observations.json','Lockit-paired-normal-FS.json')}
 def owner_api_fs(data):
  ns=dict(output=lambda n:data[n],need=need,read=read,source_report=source_path,source=source,ROOT=R,struct=struct,hashlib=hashlib,Counter=Counter,counts=Counter());exec(compile(block,'retained-owner-API-FS-assertions','exec'),ns);return ns['counts']
 owner_api_fs(base)
 def refused(label,call):
  try:call()
  except(ValueError,AssertionError,KeyError):controls.append(dict(domain=label,refused=True))
  else:raise AssertionError('Mutation survived '+label)
 for label,artifact,change in [('owner-initial','Lockit-private-owners.json',lambda r:r.__setitem__('original_initial_hex',bytes([bytes.fromhex(r['original_initial_hex'])[0]^1]).hex()+r['original_initial_hex'][2:])),('owner-store','Lockit-private-owners.json',lambda r:r['source_writes'][0].__setitem__('source_value',r['source_writes'][0]['source_value']^1)),('owner-native-expected','Lockit-private-owners.json',lambda r:r.__setitem__('native_expected_sha256','0'*64)),('API-frame','Lockit-paired-API-observations.json',lambda r:r['actual_original_APIentry_CPU'].__setitem__(4,r['actual_original_APIentry_CPU'][4]^4)),('API-return-PC','Lockit-paired-API-observations.json',lambda r:r['actual_original_sourceAPIreturn_CPU'].__setitem__(9,r['actual_original_sourceAPIreturn_CPU'][9]^1)),('API-CS24','Lockit-paired-API-observations.json',lambda r:r.__setitem__('actual_original_CS24_returned_hex',bytes([bytes.fromhex(r['actual_original_CS24_returned_hex'])[0]^1]).hex()+r['actual_original_CS24_returned_hex'][2:])),('FS-predecessor','Lockit-paired-normal-FS.json',lambda r:r.__setitem__('original_saved_predecessor',r['original_saved_predecessor']^1)),('FS-handler','Lockit-paired-normal-FS.json',lambda r:r.__setitem__('original_record_hex',r['original_record_hex'][:8]+'ffffffff'+r['original_record_hex'][16:]))]:
  wrong=copy.deepcopy(base);change(wrong[artifact][0]);refused(label,lambda:owner_api_fs(wrong))
 # Independently reconstruct complete physical provider pages using unchanged reviewer assertions.
 pstart=reviewer.index("        parser=pin(ROOT/'tools/analysis/pe.py'");pend=reviewer.index('        expected_counts=',pstart)
 pblock='\n'.join(line[8:]if line.startswith('        ')else line for line in reviewer[pstart:pend].splitlines())
 config=read(paired['configuration_path'],paired['configuration_sha256']);original_old4=read(config['original_old4_source']['path'],config['original_old4_source']['sha256']);paired_code=pin(R/'reports/m4-startup138-paired/comparer-preparation-r15/paired138.py').read_text()
 def provider_assertions(rows):
  ns=dict(pin=pin,read=read,need=need,ROOT=R,output=lambda n:rows if n=='Lockit-provider-page-relations.json'else output(n),configuration=config,original=original_old4,prep=oldprep,report=paired,paired_code=paired_code,cases={(l,i)for l in('O0','O2')for i in range(6)},counts=Counter(),struct=struct,sha_bytes=lambda b:hashlib.sha256(b).hexdigest(),sha=sha,importlib=importlib)
  exec(compile(pblock,'retained-physical-provider-assertions','exec'),ns);return ns['counts']
 provider_assertions(provider)
 for label,mutate in [('provider-wholehash',lambda r:r[0].__setitem__('original_sha256','0'*64)),('provider-declared-offset',lambda r:r[0]['exact_declared_difference_offsets'].append(4095)),('provider-endpoint-omission',lambda r:r.pop())]:
  wrong=copy.deepcopy(provider);mutate(wrong);refused(label,lambda:provider_assertions(wrong))
 # Actual comparison helper controls use current sealed source journals and derived mappings.
 def load(p,n):
  p=pin(p);spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 H=load(R/'tools/m4-tree-review/review_pair_helper_v2.py','assist_derived_mapping');TT=load(R/'tools/m4-startup138-paired/tree_relations_v2.py','assist_current_tree');contract=read(R/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json')
 old=originals[0]['source'];new=natives[0]['source'];TT.compare(old,new,H.DerivedMappingAdapter(new),'',contract)
 wrong=copy.deepcopy(old);wrong['source_accesses'][0][2]^=1;refused('actual-tree-source-operand',lambda:TT.compare(wrong,new,H.DerivedMappingAdapter(new),'',contract))
 # Formatter controls already have504 current72provider+Game/cdecl checks; invoke exact retained bounded source-only preflight into fresh child scope.
 FF=load(R/'tools/m4-startup138-paired/preflight_format_module_v2.py','assist_current_formatter_controls');FF.main(name+'-formatter-controls');fcp=R/'reports/m4-startup138-paired'/(name+'-formatter-controls')/'report.json';fc=closure(fcp);need(len(fc['adverses'])==504,'Every exact current Game/provider formatter adverse retained')
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Ordinary input closure, exact bootstrap/currentbuild/provider target facts and bounded owner/API/FS/tree/formatter mutation assist; no admission or semantic main',whole_RW_bytes=4096,whole_IAT_bytes=4096,current_compiled_provider_spans=4,owner_API_FS_sets=96,tree_sets=[6,12],formatter_sets=[24,48],controls=controls,formatter_controls=504,deferred_raw_or_capture_identities_not_opened=deferred,main_executed=False,raw_export_reader_opened=False,capture_archive_reader_opened=False,independent_review=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':run(sys.argv[1])
