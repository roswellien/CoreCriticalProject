"""Immutable missing CRT own-BEFORE mapping repair; no actual reviewer run."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];files={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
source=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json';report=json.loads(pin(source,'40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052').read_bytes())
helper=R/'tools/m4-138-controls-review/crt_heap_before_words.py'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
CS=load('bounded_CRT_source_birth',helper);PE=load('bounded_CRT_before_physical',R/'tools/analysis/pe.py');dll=R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=PE.PEImage(pin(dll,report['files'][str(dll.resolve())]).read_bytes())
for pc,wanted in((0x780039d8,b'\xa3\x00\x50\x03\x78'),(0x780039eb,b'\xa3\x04\x50\x03\x78')):
 offset=pe.rva_range(pc-pe.image_base,len(wanted))[0];assert pe.read(offset,len(wanted))==wanted
changes=[];derivatives=[]
def derive(old,name,patches):
 p=R/old;text=p.read_text();original=text;delta=[]
 for a,b in patches:
  assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b);delta.append(dict(before=a,after=b))
 inverse=text
 for c in reversed(delta):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
 assert inverse==original;ast.parse(text);q=R/'tools/m4-138-controls-review'/name;assert not q.exists();q.write_text(text);pin(p);pin(q);derivatives.append(dict(parent=str(p.resolve()),child=str(q.resolve()),changes=delta,inverse_restores_entire_parent=True));return q
bf=derive('tools/m4-138-controls-review/widget_byteflow.py','widget_byteflow_v2.py',[
 ("def verify(row,getter,phase):","def verify(row,getter,phase,*,crt_source_words):"),
 (" raw=getter('sequence-'+str(row['sequence'])+'/phase-'+str(phase)+'-before-page-'+str(0x78035000)+'.bin');need(len(raw)==4096,'Entire source-computed CRT heap global page');add(0x78035000,raw)"," need(isinstance(crt_source_words,bytes)and len(crt_source_words)==8,'Exact independently derived two CRT birth globals');add(0x78035000,crt_source_words)")])
old=R/'tools/m4-138-controls-review/review_source6_widgets_v5.py'
q=derive('tools/m4-138-controls-review/review_source6_widgets_v5.py','review_source6_widgets_v6.py',[
 ("helper_path=pin(R/'tools/m4-138-controls-review/widget_byteflow.py',"+repr(sha(R/'tools/m4-138-controls-review/widget_byteflow.py'))+")","helper_path=pin(R/'tools/m4-138-controls-review/widget_byteflow_v2.py',"+repr(sha(bf))+")"),
 ("  for level in('O0','O2'):\n","  crt_path=pin(R/'tools/m4-138-controls-review/crt_heap_before_words.py',"+repr(sha(helper))+");spec=importlib.util.spec_from_file_location('independent_CRT_source_birth',crt_path);CS=importlib.util.module_from_spec(spec);spec.loader.exec_module(CS)\n  for level in('O0','O2'):\n"),
 ("proof=BF.verify(row,facade.data,phase_map[key]['phase']);growth=growth_results[key]","crt_words=CS.derive(facade.data,row['sequence']);need(not any(a in(0x78035000,0x78035004)and writing for pc,a,v,n,writing in row['source_accesses']),'No intervening selected widget overwrites CRT birth globals');proof=BF.verify(row,facade.data,phase_map[key]['phase'],crt_source_words=crt_words);growth=growth_results[key]")])
# Small exact positive/adverse finite birth controls; no retained payload read.
base={};w=(1,0,1,0,4096,0,0x123450000,0x48450001,0,0,0,0x123450000,0x20001848,0x780039d6,0x20001858,0x780039d6);query=(1,1,1,1,148,0x200017b8,0x20000618,0x78003a31,0,0,0,37,1,1,1,1,1,0,6,2)
stem='sequence-0/cleaned/';base[stem+'heap-create-witness.bin']=struct.pack('<16Q',*w);base[stem+'heap-query-witness.bin']=struct.pack('<20Q',*query);i=bytearray(148);struct.pack_into('<I',i,0,148);z=bytearray(i);struct.pack_into('<I',z,4,6);struct.pack_into('<I',z,16,2);base[stem+'heap-query-input.bin']=bytes(i);base[stem+'heap-query-output.bin']=bytes(z);journal=[(0x780039d8,0x78035000,0x48450001,4,1),(0x780039eb,0x78035004,1,4,1)]+[(0x78003000,0x20001000,0,4,0)]*126;base[stem+'heap-source-accesses.bin']=b''.join(struct.pack('<5I',*v)for v in journal)
assert CS.derive(base.__getitem__,0)==struct.pack('<2I',0x48450001,1);controls=[dict(name='qualifying actual finite birth positive',passed=True)]
for name,k,raw in [('journal cannot seed different token',stem+'heap-source-accesses.bin',struct.pack('<5I',0x780039d8,0x78035000,7,4,1)+base[stem+'heap-source-accesses.bin'][20:]),('mode journal cannot seed unknown branch',stem+'heap-source-accesses.bin',base[stem+'heap-source-accesses.bin'][:20]+struct.pack('<5I',0x780039eb,0x78035004,2,4,1)+base[stem+'heap-source-accesses.bin'][40:]),('whole query response required',stem+'heap-query-output.bin',bytes(148)),('missing create witness rejected',stem+'heap-create-witness.bin',bytes(128))]:
 values=dict(base);values[k]=raw
 try:CS.derive(values.__getitem__,0)
 except ValueError:controls.append(dict(name=name,rejected=True))
 else:raise AssertionError(name)
pin(Path(__file__));pin(R/'reports/m4-138-controls-review/source6-widget-raw-identity-preparation-r1/report.json')
out=R/'reports/m4-138-controls-review/source6-widget-crt-before-repair-preparation-r1';assert not out.exists();out.mkdir(parents=True)
r=dict(passed=True,scope='Exact absent CRT page mapping repair: sparse source-derived HeapCreate opaque token and accepted fixed NT6/platform2 mode1 literal branch globals. Full query/birth witnesses, source publication journal solely equality target; physically matched CRT stores. No journal/AFTER values seed memory. All prior byteflow/rawGDI predicates retained.',derivatives=derivatives,controls=controls,files=files,reviewer_executed=False,capture_archives_opened=0,source_machine_executed=False,full_source_widget_acceptance_closed=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),tool_sha256=sha(q),controls=len(controls))))
