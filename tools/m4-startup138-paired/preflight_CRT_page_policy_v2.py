"""Bounded complete CRT own-input/pointer-source relation, sealed ordinary files."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 m=load('crt_current',R/'tools/m4-startup138-paired/crt_page_policy_v2.py');d=load('ordinary',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');gp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(gp.read_bytes());assert gate['passed']and gate['reader_closed']and gate['complete_provider_lifecycle'];regp=pin(R/'reports/m4-startup138-paired/original-registry-backings-r4/report.json','e90c569fa71b0a8dbdbb857eb079eb39295181241cc443d47723fbdef70727f5');reg=json.loads(regp.read_bytes());rp=regp.parent/'relations.json';origpred=json.loads(pin(rp,reg['files'][str(rp.resolve())]).read_bytes());ow=json.loads(pin(R/'reports/m4-startup138-original/widget-complete-source-r1/source-derivations.json').read_bytes());nwpath=gp.parent/'Widget-source-derivations.json';nw=json.loads(pin(nwpath,gate['files'][str(nwpath.resolve())]).read_bytes());patches=json.loads(pin(R/'reports/m4-138-validation-review/mfc-transition-r4/patch-identities.json').read_bytes());patches=[r for r in patches if r['kind']=='registry-IAT'];assert len(patches)==8;reference=pin(R/'reports/m4-startup138-original/preparation-r8/reference.cpp').read_text();assert 'if(mfc_phase){require(phase==13,'in reference and 'remove_CRT_hooks();restore_registry_hooks();'in reference and 'reinstall_registry_hooks();install_CRT_hooks();'in reference;pages=(0x7802e000,0x78037000);exports={r['branch']:r for r in gate['paired_exports']};indices={};files={}
 try:
  for branch,e in exports.items():
   ip=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);pattern=re.compile(r'phase/[0-5]/\d+/extra-(before|after)/('+ '|'.join(str(p)for p in pages)+r')\.bin')if branch=='original'else re.compile(r'sequence-[0-5]/(phase-\d+-(before|after)-page-('+ '|'.join(str(p)for p in pages)+r')\.bin|selected/locale-source-accesses\.bin)');indices[branch]=d.entries(ip,pattern);files[branch]=payload.open('rb')
  def data(branch,seq,phase,side,page):
   key=f'phase/{seq}/{phase}/extra-{side}/{page}.bin'if branch=='original'else f'sequence-{seq}/phase-{phase}-{side}-page-{page}.bin';return read(branch,key)
  def read(branch,key):
   e=indices[branch][key];f=files[branch];f.seek(e['offset']);raw=f.read(e['bytes']);assert len(raw)==e['bytes']and hashlib.sha256(raw).hexdigest()==e['sha256'];return raw
  for level in('O0','O2'):
   for seq in range(6):
    a={p:data('original',seq,0,'before',p)for p in pages};b={p:data(level,seq,0,'before',p)for p in pages};unequal={i for i in range(4096)if a[0x78037000][i]!=b[0x78037000][i]}-set(range(0x888,0x890));ledger=list(struct.iter_unpack('<IIQII',read(level,f'sequence-{seq}/selected/locale-source-accesses.bin')));touches=[]
    for source in [ledger]+[r['source_accesses']for r in ow if r['sequence']==seq]+[r['source_accesses']for r in nw if r['level']==level and r['sequence']==seq]:
     for pc,address,value,width,write in source:
      if address<0x78038000 and address+width>0x78037000:
       overlap={v-0x78037000 for v in range(max(address,0x78037000),min(address+width,0x78038000))}&unequal
       assert not overlap,('Initial opaque byte is source-consumed',level,seq,hex(pc),hex(address),overlap)
    policy=m.Policy(a,b,patches,unequal);abegin,anext=struct.unpack_from('<II',a[0x78037000],0x888)[::-1];nbegin,nnext=struct.unpack_from('<II',b[0x78037000],0x888)[::-1];cursor=0;callback_count=0
    for phase in range(138):
     original_row=origpred[seq*138+phase];before_a=[abegin,anext];before_b=[nbegin,nnext]
     if original_row['callback']is not None:
      cb=original_row['callback'];store=original_row['source_store'];abegin=store['address']-callback_count*4;anext=store['address']+4;found=False
      while cursor<len(ledger):
       pc,address,value,width,write=ledger[cursor];cursor+=1
       if write and address in(0x78037888,0x7803788c):
        assert width==4 and pc in(0x7800448f,0x780044a2,0x7801e2aa,0x7801e2b5,0x78004a69)
        if address==0x7803788c:nbegin=value
        else:nnext=value
       if pc==0x78004a67:
        assert write and width==4 and value==cb and address==nbegin+callback_count*4;found=True
       if found and pc==0x78004a69 and write:break
      assert found and nnext-nbegin==(callback_count+1)*4;callback_count+=1
     for side,ameta,bmeta in [('before',before_a,before_b),('after',[abegin,anext],[nbegin,nnext])]:
      for page in pages:
       aa=data('original',seq,phase,side,page);bb=data(level,seq,phase,side,page);declared=policy.page(phase,side,page,aa,bb,ameta,bmeta);rows.append(dict(level=level,sequence=seq,phase=phase,side=side,page=page,original_sha256=hashlib.sha256(aa).hexdigest(),native_sha256=hashlib.sha256(bb).hexdigest(),exact_declared_offsets=sorted(declared)))
    assert callback_count==108 and not any(w and addr in(0x78037888,0x7803788c)for pc,addr,v,width,w in ledger[cursor:])
  for branch,e in exports.items():assert sha(e['index_path'])==e['index_sha256']and sha(e['payload_path'])==e['payload_sha256']
 finally:
  for f in files.values():f.close()
 p=out/'relations.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Bothlevels all6case twoCRTpage own-bootstrap carries, exact eight phase13 restore/phase14 reentry observer imports and literal-source registry pointer lastwriters; finite unused startup bytes disjoint from full current native selected source journal and complete current original/native widget operands',whole_page_endpoint_relations=len(rows),source_registry_field_schedule_relations=1656,all_phase_source_fields_derived=True,unused_input_difference_policy_is_finite=True,source_operand_scope_original='Complete current original42 widget source plus inherited same physical provider body; full original provider CPU is not replayed here',original_registry_source_sha256=sha(regp),native_source_sha256=sha(gp),complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
