"""Finite current chronology/raw static fields; no canonical reader or tree execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  p=pin(p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 D=load('ordinary_entry_index',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');old=load('accepted_tree',R/'tools/m4-startup131-paired/tree_relations.py');new=load('current_tree',R/'tools/m4-startup138-paired/tree_relations_v2.py');assert new.TREE_PHASE==83 and old.TREE_PHASE==79;assert pin(R/'tools/m4-startup138-paired/tree_relations_v2.py').read_text().replace('TREE_PHASE = 83','TREE_PHASE = 79')==pin(R/'tools/m4-startup131-paired/tree_relations.py').read_text()
 prep=pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161');order=json.loads(prep.read_bytes())['selected_order'];assert order[83]['entry']==new.TREE and order[79]['entry']==0x4b5af0
 baseline=pin(R/'reports/m4-startup131-original/preparation-r4/report.json');assert json.loads(baseline.read_bytes())['selected_order'][79]['entry']==new.TREE
 inherited=pin(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4');source=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052')
 def artifact(report,leaf):
  p=report.parent/leaf;return json.loads(pin(p,json.loads(report.read_bytes())['files'][str(p.resolve())]).read_bytes())
 originals=artifact(inherited,'original-Tree-source-derivations.json');natives=artifact(source,'Tree-source-derivations.json');assert len(originals)==6 and len(natives)==12 and all(r['phase']==r['source']['phase']==83 for r in originals)
 p=pin(R/'reports/m4-startup138-paired/comparer-preparation-r9/paired138.py');tree=ast.parse(p.read_text());pages=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PAGES'for t in n.targets));page=0x60b000;pi=pages.index(page);assert pi<17
 exports=json.loads(source.read_bytes())['paired_exports'];raws={};rawproof=[]
 for branch in('original','O0','O2'):
  e=next(v for v in exports if v['branch']==branch);index=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);pattern=re.compile(r'phase/[0-5]/(?:79|82|83)\.bin'if branch=='original'else r'sequence-[0-5]/phase-(?:79|82|83)\.bin');entries=D.entries(index,pattern);assert len(entries)==18
  with payload.open('rb')as f:
   for key,v in entries.items():
    f.seek(v['offset']);raw=f.read(v['bytes']);assert hashlib.sha256(raw).hexdigest()==v['sha256'];parts=[int(x)for x in re.findall(r'\d+',key)];seq,phase=parts;raws[branch,seq,phase]=raw;rawproof.append(dict(branch=branch,name=key,**v))
 rows=[];adverses=0
 def pagebytes(branch,seq,phase,side):
  base=(2276 if side=='before'else (178404 if branch=='original'else 71908));return raws[branch,seq,phase][base+pi*4096:base+(pi+1)*4096]
 for level in('O0','O2'):
  for seq in range(6):
   a=next(v['source']for v in originals if v['sequence']==seq);b=next(v['source']for v in natives if v['sequence']==seq and v['level']==level);aw=a['static_field_writes'];bw=b['static_field_writes'];assert [(v['pc'],v['address'],v['width'])for v in aw]==[(v['pc'],v['address'],v['width'])for v in bw];fields={}
   for av,bv in zip(aw,bw):
    for i in range(av['width']):fields[av['address']+i]=(av['value'].to_bytes(av['width'],'little')[i],bv['value'].to_bytes(bv['width'],'little')[i],av['pc'])
   for branch in('original',level):
    assert struct.unpack_from('<I',raws[branch,seq,83],36+9*4)[0]==new.TREE
    assert pagebytes(branch,seq,82,'after')==pagebytes(branch,seq,83,'before')
   for phase,side in((79,'before'),(79,'after'),(83,'before')):
    declared=set();new.carry(fields,phase,side,page,pagebytes('original',seq,phase,side),pagebytes(level,seq,phase,side),declared,{});assert not declared
   from collections import Counter
   ao=pagebytes('original',seq,83,'after');bn=pagebytes(level,seq,83,'after');declared=set();new.carry(fields,83,'after',page,ao,bn,declared,Counter());assert declared=={address&4095 for address in fields if address&~4095==page}
   for branch in('original','native'):
    aa=bytearray(ao);bb=bytearray(bn);(aa if branch=='original'else bb)[0x2f9]^=1
    try:new.carry(fields,83,'after',page,aa,bb,set(),Counter())
    except ValueError:adverses+=1
    else:raise AssertionError('Corrupt genuine activated tree field admitted')
   av,bv,pc=fields[0x60b2f9];rows.append(dict(level=level,sequence=seq,actual_tree_phase=83,root_at_old_phase=order[79]['entry'],address=0x60b2f9,write_PC=pc,source_original_expected=av,source_native_expected=bv,phase79_after_original=pagebytes('original',seq,79,'after')[0x2f9],phase79_after_native=pagebytes(level,seq,79,'after')[0x2f9],phase83_after_original=ao[0x2f9],phase83_after_native=bn[0x2f9]))
 assert len(rows)==12 and adverses==24;pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact current tree phase83 binding and all12 own source/raw static endpoint joins; unrelated phase79 cannot activate future tree values',original_source_cases=6,native_source_cases=12,raw_entries_authenticated=54,whole_before_tree_page_carries=18,activated_endpoint_adverses_refused=adverses,rows=rows,raw_entry_receipts=rawproof,all_ordinary_readers_closed=True,archive_reader_opened=False,tree_source_reexecuted=False,whole_tree_body_CPU_reproved=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
