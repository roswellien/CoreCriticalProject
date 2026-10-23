"""Bounded whole CS24 helper inverse and finite ownership/carry adversaries."""
from pathlib import Path
import copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 parent=pin(R/'tools/m4-startup138-paired/crt_page_policy_v4.py','0d4797ccdf4d7adc5372893366a0e2d2bbd678ab65b8963769698d80c45d4cc8');helper=pin(R/'tools/m4-startup138-paired/crt_page_policy_v5.py');a=parent.read_text();b=helper.read_text();import difflib
 opcodes=[(tag,i,j,k,l)for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes()if tag!='equal'];hunks=[];al=a.splitlines(True);bl=b.splitlines(True)
 for tag,i,j,k,l in opcodes:hunks.append(dict(tag=tag,old=''.join(al[i:j]),new=''.join(bl[k:l]),old_lines=[i,j],new_lines=[k,l]))
 reverse=bl[:]
 for h in reversed(hunks):k,l=h['new_lines'];assert ''.join(reverse[k:l])==h['new'];reverse[k:l]=h['old'].splitlines(True)
 assert ''.join(reverse)==a and len(hunks)==2
 gp=pin(R/'reports/m4-startup138-paired/CRT-lock13-domain-r2/report.json','6bf6c226e40dea50912fb126eaaa97715af4aadd436189114ec292f599a161eb');g=json.loads(gp.read_bytes());assert g['passed']and g['ordinary_readers_closed']and g['typed_lock13_object_relations']==12
 for p,h in g['files'].items():pin(p,h)
 domains=json.loads(pin(g['domains_path'],g['domains_sha256']).read_bytes());ip=pin(R/'reports/m4-startup138-paired/CRT-import-cell-policy-r3/report.json','07a81409de7d5aae90945079dd4ce295ead37fd6b3ea1cac4e723e95792e10aa');ig=json.loads(ip.read_bytes());imports=json.loads(pin(ig['physical_import_cells_path'],ig['physical_import_cells_sha256']).read_bytes());s=importlib.util.spec_from_file_location('lock13policy',helper);M=importlib.util.module_from_spec(s);s.loader.exec_module(M);controls=[];positive=0
 for d in domains:
  a={int(k):bytes.fromhex(v)for k,v in d['original_inputs'].items()};b={int(k):bytes.fromhex(v)for k,v in d['native_inputs'].items()};physical=next(r['physical_import_cells']for r in imports if r['level']==d['level']and r['sequence']==d['sequence']);args=[a,b,d['patches'],d['unused_input_offsets'],physical,d['typed_CRT_loader_cells'],d['typed_CRT_lock13_objects']];P=M.Policy(*args)
  for row in d['registry_fields']:
   for side in('before','after'):
    am=row[side+'_original'];bm=row[side+'_native']
    for page in(0x7802e000,0x78037000):
     aa=bytearray(a[page]);bb=bytearray(b[page])
     if page==0x78037000:struct.pack_into('<II',aa,0x888,am[1],am[0]);struct.pack_into('<II',bb,0x888,bm[1],bm[0])
     elif row['phase']==13:
      for p in d['patches']:offset=p['pc']&4095;aa[offset:offset+4]=bytes.fromhex(p['original_hex'])
     declared=P.page(row['phase'],side,page,bytes(aa),bytes(bb),am,bm);assert page!=0x78037000 or set(range(0x130,0x148))<=declared;positive+=1
  am=d['registry_fields'][0]['before_original'];bm=d['registry_fields'][0]['before_native']
  for side in('original','native'):
   for offset in range(0x130,0x148):
    aa=bytearray(a[0x78037000]);bb=bytearray(b[0x78037000]);(aa if side=='original'else bb)[offset]^=1
    try:P.page(0,'before',0x78037000,bytes(aa),bytes(bb),am,bm)
    except ValueError:controls.append(dict(level=d['level'],sequence=d['sequence'],name='whole-own-CS24-carry',side=side,offset=offset,refused=True))
    else:raise AssertionError(('Accepted changed CS24',side,offset))
  for field,value in [('size',23),('offset',0x131),('guest_address',0x78037118),('native_resource_extent',24),('native_resource_pointer',0),('native_initializations',0),('native_enter_leave',[108,107]),('original_enter_leave',[107,108]),('opaque_API_internals_equivalent',True),('native_initial_hex','01'+bytes(23).hex()),('original_initial_hex',bytes(24).hex())]:
   bad=copy.deepcopy(args);bad[-1][0][field]=value
   try:M.Policy(*bad)
   except ValueError:controls.append(dict(level=d['level'],sequence=d['sequence'],name='typed-CS24-'+field,refused=True))
   else:raise AssertionError(field)
  for missing in('missing-object','consumed-byte-declared-unused'):
   bad=copy.deepcopy(args)
   if missing=='missing-object':bad[-1]=[]
   else:bad[3].append(0x130)
   try:M.Policy(*bad)
   except ValueError:controls.append(dict(level=d['level'],sequence=d['sequence'],name=missing,refused=True))
   else:raise AssertionError(missing)
 assert positive==6624 and len(controls)==732
 hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact two diff hunks (three explicit additions) over retained helper4; whole24 explicitly typed API descriptor, all24 excluded fromunused;6624 bounded source-expected pages and732 finite ownership/carry adversaries; no raw reader or full comparer invocation',domains_path=g['domains_path'],domains_sha256=g['domains_sha256'],helper=str(helper),helper_sha256=sha(helper),exact_inverse_restores_helper4=True,parent_helper_sha256=sha(parent),helper_hunks=2,whole_source_expected_pages=positive,negative_controls=controls,complete_paired_policy_admitted=False,archive_reader_opened=False,raw_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
