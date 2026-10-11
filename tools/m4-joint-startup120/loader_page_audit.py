"""Independently retain and verify the complete two-branch MFC540 page inputs."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PAGE=0x5f4cc000;NIL=0x5f4ccb54;VALUE=0x5f4cecec
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(original_run,original_sha,native_run,native_sha,bootstrap_template,name):
 out=ROOT/'reports/m4-joint-startup120-root'/name;need(not out.exists(),'Fresh loader input audit');out.mkdir(parents=True);pins={};counts=collections.Counter();passed=False;relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical loader input identity '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable physical dependency');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def own(p,n):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  o=read(original_run,original_sha);n=read(native_run,native_sha);need(o['passed']and o['original_executed']and n['passed']and n['native_executed'],'Actual original/native runs')
  ob=read(o['build_path'],o['build_sha256']);op=read(Path(ob['preparation'])/'report.json',ob['preparation_sha256']);pages=op['observed_pages'];need(len(pages)==len(set(pages))==40 and PAGE in pages,'Exact original40-page ABI')
  nb=read(n['build_path'],n['build_sha256']);np=read(nb['preparation'],nb['preparation_sha256']);need(len(np['selected_order'])==120 and PAGE in np['extra_pages'],'Exact native120 schema')
  m=own(ROOT/'tools/analysis/pe.py','loader_audit_pe');pe=m.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());offset=pe.rva_range(PAGE-pe.image_base,4096)[0];raw=pe.data[offset:offset+4096];need(len(raw)==4096 and struct.unpack_from('<I',raw,NIL-PAGE)[0]==VALUE,'Entire genuine raw PE page and nil DWORD')
  d=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','loader_audit_direct');original=d.DirectSet(Path(o['original_capture']),pin)
  try:
   for level in n['levels']:
    reader=d.DirectSet(Path(level['capture']),pin)
    try:
     need(reader.words('selected-table.bin',120)==tuple(r['entry']for r in op['order']),'Same exact relative table order')
     for seq in range(6):
      boot_name=bootstrap_template.format(sequence=seq);loaded=original.data(boot_name);need(len(loaded)==4096 and struct.unpack_from('<I',loaded,NIL-PAGE)[0]==VALUE,'Complete same-worker initialized bootstrap page; exact nil DWORD')
      differences=[dict(offset=i,address=PAGE+i,original=a,native=b)for i,(a,b)in enumerate(zip(loaded,raw))if a!=b]
      need(all(not NIL<=r['address']<NIL+4 for r in differences),'All actual branch-input differences exclude the reached exact DWORD')
      relations.append(dict(level=level['level'],sequence=seq,original_bootstrap_logical_name=boot_name,original_page_sha256=hashlib.sha256(loaded).hexdigest(),native_page_sha256=hashlib.sha256(raw).hexdigest(),differences=differences))
      for phase in range(120):
       record=original.data(f'phase/{seq}/{phase}.bin');need(len(record)==332416,'Exact whole original record ABI')
       for side,start in(('before',2276),('after',2276+40*4096)):
        begin=start+pages.index(PAGE)*4096;need(record[begin:begin+4096]==loaded,'Whole original loaded input page carried without overwriting or reseeding');counts['whole_original_bootstrap_page_carries']+=1
        actual=reader.data(f'sequence-{seq}/phase-{phase}-{side}-page-{PAGE}.bin');need(actual==raw,'Whole native raw PE input page carried without modification');counts['whole_native_raw_page_carries']+=1
        counts['exact_nil_DWORD_relations']+=1
      accesses=reader.data(f'sequence-{seq}/selected/locale-source-accesses.bin');need(len(accesses)%24==0,'Exact authenticated SourceAccess24B record layout');reached=[]
      for pc,address,value,width,write in struct.iter_unpack('<IIQII',accesses):
       need(width>0,'Positive source access width')
       if address<PAGE+4096 and PAGE<address+width:
        need((pc,address,value,width,write)==(0x5f4020bc,NIL,VALUE,4,0),'Entire reached native page footprint is only the literal nil DWORD read');reached.append(pc)
       need(not(address<0x5f4cf000 and 0x5f4ce000<address+width),'Borrowed pointee page receives zero source dereferences')
      need(len(reached)==3,'Exactly three original CString constructors reached per actual native sequence');counts['exact_reached_native_nil_reads']+=len(reached);counts['actual_native_sequences']+=1
    finally:
     reader.close()
     del reader
  finally:
   original.close()
   del original
  need(counts['whole_original_bootstrap_page_carries']==counts['whole_native_raw_page_carries']==2880 and counts['exact_reached_native_nil_reads']==36,'Complete fresh paired120 extent')
  (out/'branch-input-page-relations.json').write_text(json.dumps(relations,indent=2)+'\n');pin(out/'branch-input-page-relations.json');pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  r=dict(passed=passed,scope='Complete same-worker initialized original MFC page versus entire raw native PE page, each unchanged across all120 roots; exact reached nil DWORD and zero native pointee reads. Original reached footprint remains independently source-verified. Separate branch-input relation, no page mask or prior-process input seed.',counts=dict(counts),observed_page=PAGE,reached_DWORD=NIL,borrowed_value=VALUE,original_page_overwritten=False,native_page_modified=False,blanket_page_mask=False,prior_process_page_seed=False,whole_loader_state_equivalence=False,initializer_credit=False,files=pins)
  (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(*sys.argv[1:])
