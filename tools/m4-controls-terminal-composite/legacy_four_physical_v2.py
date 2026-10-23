"""UNEXECUTED legacy12 four-facet physical prover, requiring ROOT admission.

Not current8 proof, semantic control execution, whole7 composite, or acceptance.
Every source/body read must belong to the future immutable ROOT input gate.
"""
from pathlib import Path
import ast, hashlib, json, re, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PREP='8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'
BUILD='9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
REVIEW='c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb'
def need(value,why):
 if not value:raise ValueError(why)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inverse(text,deltas):
 for old,new in reversed(deltas):need(text.count(new)==1,'Exactly one physical inverse site');text=text.replace(new,old)
 return text
def literal_assignments(source,wanted):
 """Only literal AST assignment RHS; never execute a derivation script."""
 output={}
 for node in ast.parse(source).body:
  if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in wanted:output[node.targets[0].id]=ast.literal_eval(node.value)
 need(set(output)==set(wanted),'Exact finite derivation literal schema');return output
def main(admission,admission_sha,name):
 ap=Path(admission).resolve();need(sha(ap)==admission_sha,'ROOT admission identity');A=json.loads(ap.read_bytes());need(A['passed']is True and A['legacy_four_physical_prover_admitted']is True,'ROOT must review source and input scope first');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.drive.casefold()in(R.drive.casefold(),'c:')and p.suffix.lower()not in('.mwb','.mwi','.mwc','.zip')and p.name!='transport.json','Only admitted bounded workspace physical inputs');need(str(p)in A['files'],'Actual physical input admitted before open');value=sha(p);need(value==A['files'][str(p)]and(h is None or value==h),'Exact current whole physical input');need(files.setdefault(str(p),value)==value,'Stable identity');return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def definitions(p,names,scope):
  nodes=ast.parse(text(p)).body;selected=[node for node in nodes if isinstance(node,(ast.FunctionDef,ast.ClassDef))and node.name in names];need({n.name for n in selected}==set(names),'Exact reused physical parser definitions');exec(compile(ast.Module(body=selected,type_ignores=[]),str(p),'exec'),scope)
 pin(__file__);folder=R/'reports/m4-138-preresource-controls/preparation-r3';prep=read(folder/'report.json',PREP);build=read(R/'reports/m4-138-preresource-controls/build-r4/build.json',BUILD);review=read(R/'reports/m4-138-preresource-root-review/root-review-r1/report.json',REVIEW);need(prep['passed']and build['passed']and review['passed']and build['preparation_sha256']==PREP,'Exact legacy12 current preparation/build/ROOT physical review')
 for gate in(prep,build,review):
  for p,h in gate['files'].items():pin(p,h)
 rootlinks=read(Path(R/'reports/m4-138-preresource-root-review/root-review-r1/links.json'));need(review['prelaunch_checks']['complete_source_inverse']and review['prelaunch_checks']['typed_COFF_CALL_TLS_ownership'],'Retained whole ROOT proof, not occurrence annotations')
 old3=text(R/'tools/m4-mfc1168-native/connected_controls_v3.inc');old4=text(R/'tools/m4-mfc1168-native/connected_controls_v4.inc');old5=text(R/'tools/m4-mfc1168-native/connected_controls_v5.inc')
 d4=literal_assignments(text(R/'tools/m4-mfc1168-native/derive_connected_controls_v4.py'),('old','new'));need(inverse(old4,[(d4['old'],d4['new'])])==old3,'Whole diagnostic-only v4 to v3 inverse')
 need('terminal-facts.bin'in d4['new']and 'if(!precise_refusal)'in d4['new']and 'need(precise_refusal,'in d4['new'],'Diagnostic records before retained exact refusal predicate')
 d5=[]
 for cell,page,mode in(('0x5f498330','0x5f498000',3),('0x7802e0c8','0x7802e000',9)):
  before=f'case {mode}:scalar({cell},0);break;';after=f'case {mode}:r.memory().protect({{{page}}},mw34::Permissions::read|mw34::Permissions::write);scalar({cell},0);r.memory().protect({{{page}}},mw34::Permissions::read);break;';d5.append((before,after))
 need(inverse(old5,d5)==old4,'Entire two readonly IAT repairs v5 to v4 inverse; no other line change')
 legacy=text(R/'reports/m4-mfc1168-native/connected-controls-preparation-r6/connected_controls.inc');need(legacy==old5,'Physically retained legacy source equals exact repaired v5')
 need(len(prep['legacy_controls_changes'])==12 and len(prep['parent_main_changes'])==5,'Exact retained twelve/five finite source inverse geometry');controls=text(folder/'controls_main.cpp');start=controls.index(legacy.splitlines()[0]);need(inverse(controls[start:],[(d['before'],d['after'])for d in prep['legacy_controls_changes']])==legacy,'Whole current controls to legacy source inverse, retaining exact twelve declared adaptations')
 native=text(folder/'native_main.cpp');parent=text(Path(prep['parent_preparation']).parent/'native_main.cpp');need(inverse(native,[(d['before'],d['after'])for d in prep['parent_main_changes']])==parent,'Whole current Context source inverse')
 entryline=[line for line in native.splitlines()if 'static void mfc_entry('in line];need(len(entryline)==1,'One literal root entry');line=entryline[0];ordered=['overlay_cpu(c->s_,r.cpu());','snapshot(r,c->s_,true);','mfc_control_entry(r,c->s_);','c->mfc_component_=std::make_unique<mc::Component>','mc::Borrow borrow','mc::entry(r);'];need(all(line.count(v)==1 for v in ordered)and[line.index(v)for v in ordered]==sorted(line.index(v)for v in ordered),'Same Runtime source CALL entry observer BEFORE component construction')
 hookstart=controls.index('static void mfc_control_entry(');hookend=controls.index('\nstatic unsigned mfc_control_mode',hookstart);hook=controls[hookstart:hookend]
 for token in('std::array<std::byte,64>frame{}','r.cpu().eip==mc::root&&r.cpu().esp==mw34::m4_mixed::frame','r.memory().read({r.cpu().esp},frame)','put("entry-frame64.bin",frame.data(),frame.size())'):need(hook.count(token)==1,'Actual own live CPU/rESP 64-byte hook geometry')
 scope={'struct':struct,'need':need};definitions(R/'tools/m4-tree-review/amd64_coff.py',('parse','function','linked_candidates'),scope);definitions(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py',('AMD64Image',),scope)
 bodies=[]
 def linked(level,w,symbol):
  objectpath=pin(w['object'],w['object_sha256']);workerpath=pin(w['path'],w['sha256']);symbols,sections=scope['parse'](objectpath.read_bytes());raw,relocs=scope['function'](symbols,sections,symbol);image=scope['AMD64Image'](workerpath.read_bytes());own=[row for row in rootlinks if row.get('level')==level and row.get('symbol')==symbol and row.get('scope')=='actual prefix control/caller/cleanup'];need(len(own)==1,'Unique ROOT whole owning function row');row=own[0];need(row['whole_bytes']==len(raw)and row['relocations']==len(relocs),'Whole physical function extent/relocation schema');need(all(4<=r['type']<=9 or r['type']==11 for r in relocs),'Only ROOT-proven exact typed REL32/TLS fields');matches=scope['linked_candidates'](image,raw,[dict(r,type=4)for r in relocs]);matches=[(a,b)for a,b in matches if a==row['address']];need(len(matches)==1,'Entire COFF nonrelocated bytes at actual unique ROOT-owned linked address');address,actual=matches[0];witness=dict(level=level,symbol=symbol,address=address,whole_bytes=len(raw),COFF_sha256=hashlib.sha256(raw).hexdigest(),linked_sha256=hashlib.sha256(actual).hexdigest(),relocations=relocs,ROOT_whole_CALL_TLS_review_sha256=REVIEW);bodies.append(witness);return symbols,sections,raw,relocs,image,address,actual
 for level,w in build['workers'].items():
  need(level in('O0','O2')and str(folder/'controls_main.cpp')in[argument for command in build['commands']for argument in command['arguments']],'Actual legacy controls compile')
  deps={str(Path(p).resolve())for p in w['compiler_dependencies']};need(str(folder/'native_main.cpp')in deps,'Owning current Context actual compiler dependency');[pin(p)for p in deps]
  sy,se,raw,relocs,image,address,actual=linked(level,w,'?mfc_entry@Context@m4_mixed@mw34@@SAXAEAVRuntime@m4_runtime@3@@Z')
  if level=='O0':
   names=[s['name']for s in sy.values()if s['section']>0 and s['type']==32 and s['name'].startswith('?mfc_control_entry@@')];need(len(names)==1,'Actual O0 source hook');*_,hookaddr,hookactual=linked(level,w,names[0]);calls=[r for r in relocs if r['symbol']['name']==names[0]];need(len(calls)==1,'One typed own source hook edge');r=calls[0];need(raw[r['offset']-1]==0xe8 and address+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',actual,r['offset'])[0]==hookaddr,'Physical root-entry CALL reaches whole compiled source hook')
  else:
   need(not any(s['section']>0 and s['type']==32 and s['name'].startswith('?mfc_control_entry@@')for s in sy.values()),'O2 hook is inlined, no invented dropped-body requirement')
   # Two independently named constants must be referenced by actual whole
   # mfc_entry instructions, with exact linked target bytes, not merely anywhere
   # in the binary. All remaining typed targets/TLS use retained ROOT proof.
   for needle in(b'entry-frame64.bin\0',b'Actual committed MFC CALL frame\0'):
    witnesses=[]
    for r in relocs:
     sym=r['symbol'];sec=se.get(sym['section']);offset=sym['value']
     if sec is None or not sec['bytes'][offset:].startswith(needle):continue
     need(4<=r['type']<=9,'Exact inline named constant REL32');target=address+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',actual,r['offset'])[0]
     for secimg in image.sections:
      begin=image.image_base+secimg['virtual_address']
      if begin<=target and target+len(needle)<=begin+secimg['raw_size']:
       pos=secimg['raw_offset']+target-begin;need(image.data[pos:pos+len(needle)]==needle,'Whole actual inline source hook named constant');witnesses.append(dict(offset=r['offset'],target=target,symbol=sym['name']))
    need(witnesses,'Actual whole O2 entry inline references own frame emission AND exact live CPU/rESP guard');bodies[-1].setdefault('inline_named_source_relations',[]).append(dict(bytes=needle.hex(),rows=witnesses))
 need(set(build['workers'])=={'O0','O2'},'Both actual compiled domains')
 counts=dict(whole_intended_protected_IAT_mutation_repairs=len(d5),whole_diagnostic_only_delta=1,whole_true_source_entry_observer=len(entryline),entry_observer_inlined_in_whole_MFC_entry=sum(b['level']=='O2'and'inline_named_source_relations'in b for b in bodies));need(counts==dict(whole_intended_protected_IAT_mutation_repairs=2,whole_diagnostic_only_delta=1,whole_true_source_entry_observer=1,entry_observer_inlined_in_whole_MFC_entry=1),'Finite exact original named domains')
 for p,h in files.items():need(sha(p)==h,'Final bounded physical code/input identity')
 need(re.fullmatch('[A-Za-z0-9_-]{1,90}',name),'Simple namespace');out=R/'reports/m4-controls-terminal-composite'/name;need(not out.exists(),'Fresh output');out.mkdir();(out/'whole-hook-bodies.json').write_text(json.dumps(bodies,indent=2)+'\n')
 files[str(out/'whole-hook-bodies.json')]=sha(out/'whole-hook-bodies.json');report=dict(passed=True,scope='legacy12 four static physical facets only; other three and actual24 terminal joins remain separate',legacy_preparation_sha256=PREP,legacy_build_sha256=BUILD,counts=counts,whole_source_inverse=True,whole_O0_CALL_and_O2_inline_physical_join=True,whole_four_named_fields_physically_reviewed=True,all_seven_named_fields_physically_reviewed=False,runtime_control_cases_executed=False,canonical_reader_opened=False,accepted_function_credit=0,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
