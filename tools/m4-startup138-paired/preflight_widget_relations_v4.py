"""Archive-free exact finite widget pair helper and adversarial field/lifetime controls."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};passed=False;relations=[];controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 def load(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  m=load('finite_pair_widget',R/'tools/m4-startup138-paired/widget_relations_v7.py');o=json.loads(pin(R/'reports/m4-startup138-original/widget-complete-source-r1/source-derivations.json').read_bytes());nativegate=json.loads(pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052').read_bytes());assert nativegate['passed']and nativegate['reader_closed'];np=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/Widget-source-derivations.json';n=json.loads(pin(np,nativegate['files'][str(np.resolve())]).read_bytes());assert len(o)==42 and len(n)==84
  allrelations=[];joined=[];fonts=json.loads(pin(R/'reports/m4-startup138-original/widget-complete-source-r1/source-font-generations.json').read_bytes());cp=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/Widget-manual-native-cleanup.json';cleanups=json.loads(pin(cp,nativegate['files'][str(cp.resolve())]).read_bytes());assert len(cleanups)==12
  for level in('O0','O2'):
   for seq in range(6):
    current=[m.compare_root(next(a for a in o if a['sequence']==seq and a['root']==root),next(b for b in n if b['level']==level and b['sequence']==seq and b['root']==root))for root in m.WIDGETS];allrelations.extend(current);joined.extend(m.compare_font_cleanup(fonts,current,next(c for c in cleanups if c['level']==level and c['sequence']==seq)))
  relations=allrelations[:7];cleanup=cleanups[0]
  def refusal(label,call):
   try:call()
   except ValueError:controls.append(dict(name=label,refused=True))
   else:raise AssertionError(label+' must refuse')
  a=copy.deepcopy(o[0]);a['registration_callback']^=4;refusal('wrong-literal-callback',lambda:m.compare_root(a,n[0]))
  b=copy.deepcopy(n[0]);b['GDI_source']['API_response_derivations'][0]['source_arguments'][0]^=1;refusal('wrong-GDI-arg',lambda:m.compare_root(o[0],b))
  b=copy.deepcopy(n[0]);i=next(i for i,x in enumerate(b['source_accesses'])if x[0]==0x78004a67);b['source_accesses'][i][1]+=4;refusal('wrong-source-registry-next',lambda:m.compare_root(o[0],b))
  badfonts=copy.deepcopy(fonts);badfonts[0]['instance']+=4;refusal('wrong-font-instance',lambda:m.compare_font_cleanup(badfonts,relations,cleanup))
  badcleanup=copy.deepcopy(cleanup);badcleanup['font_generations'][0]=1;refusal('stock-generation-cleaned-as-owned',lambda:m.compare_font_cleanup(fonts,relations,badcleanup))
  policy=m.HandleFieldPolicy();policy.activate(relations[4],134);page=next(iter(policy.fields))&~4095;original=bytearray(4096);native=bytearray(4096)
  for address,row in policy.fields.items():
   if address&~4095==page:offset=address&4095;original[offset:offset+4]=row['original'].to_bytes(4,'little');native[offset:offset+4]=row['native'].to_bytes(4,'little')
  offsets=policy.page(134,'after',page,original,native);assert offsets and policy.page(134,'before',page,original,native)==set();controls.append(dict(name='exact-literal-field-and-activation-boundary',passed=True,declared_bytes=len(offsets)))
  native[min(offsets)]^=1;refusal('changed-carried-handle-byte',lambda:policy.page(135,'before',page,original,native))
  graph=json.loads(pin(R/'reports/m4-fps-original/source-preparation-r4/source-contracts.json').read_bytes())['instructions'];own=[v for v in graph if v['pc']in(0x5a0142,0x5a0753)];assert len(own)==2
  pe=load('physical_widget_pair_PE',R/'tools/analysis/pe.py');image=pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  for row in own:
   assert row['bytes_hex']=='898658020000'and row['mnemonic']=='mov';b=bytes.fromhex(row['bytes_hex']);offset,_=image.rva_range(row['pc']-image.image_base,len(b));assert image.read(offset,len(b))==b
  literalrows=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_bytes());literalrows=literalrows['instructions']if isinstance(literalrows,dict)else literalrows
  providerpcs=(0x78004a67,0x7801e2aa,0x7801e2b5);assert all(any(v['pc']==pc for v in literalrows)for pc in providerpcs)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'report.json';r=dict(passed=passed,scope='Complete finite84 current native/42 own-original typed source GDI/FS/registrar/realloc/font/store/lifetime joins and physical literal controls; separate whole raw page policy remains required',whole_endpoint_authorization=False,current_native_source_admitted=True,native_source_sha256=sha(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json'),full_pair_executed=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,controls=controls,root_relations=len(allrelations),font_cleanup_relations=len(joined),physical_handle_store_PCs=[0x5a0142,0x5a0753],unresolved_source_operand_values=sum(len(r['unresolved_value_relations'])for r in allrelations),pending=['Current allphase exact physical observer/IAT spans','Native registry APIbirth fullbacking/replay/growth source helper joins'],files=pins);q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),roots=len(relations),controls=controls)))
  if passed:
   p=out/'relations.json';p.write_text(json.dumps(dict(roots=allrelations,font_cleanup=joined),indent=2)+'\n')
if __name__=='__main__':main(sys.argv[1])
