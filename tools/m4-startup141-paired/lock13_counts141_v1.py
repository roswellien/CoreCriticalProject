"""Finite current141 lock13 Enter/Leave count derivation; ordinary exports only.

Applies the inherited prove_CRT_lock13_v2 per-record rules unchanged to the
current strict original141 export (all141 phases, 26-DWORD ledgers) and to the
native141 combined source6 O0/O2 typed API witnesses. Counts are DERIVED from
exhaustive chronology, never copied (108) or guessed (111). Whole index and
payload files are hashed before and after. No capture, canonical reader,
worker or source model. Grants no CRT whole-page policy or accepted credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
CS=0x78037130;PAGE=0x78037000
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Never a capture archive';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);helper=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');spec=importlib.util.spec_from_file_location('ordinary_entries',helper);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());assert V['passed']and V['reader_closed']and V['counts']['phases']==846
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True and N['paired_export_readers_closed']is True and N['complete_persistent141_constructors']is True
 bundles={}
 for branch,row,pattern in [('original',next(e for e in V['paired_exports']if e['branch']=='original'),re.compile(r'phase/[0-5]/\d+/(?:api-ledger|CRT-(?:before|after)/2013491200)\.bin')),
                            *[(lv,next(e for e in N['paired_exports']if e['branch']==lv),re.compile(r'sequence-[0-5]/(?:(?:selected/locale-(?:api-\d+-(?:witness|input-0)|critical-sections))|cleaned/locale-critical-sections|phase-\d+-(?:before|after)-page-2013491200)\.bin'))for lv in('O0','O2')]]:
  i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256']);bundles[branch]=(i,p,D.entries(i,pattern))
 def data(f,es,k,n=None):
  z=es[k];assert n is None or z['bytes']==n,(k,z['bytes']);f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
 original=[];i,p,es=bundles['original']
 with p.open('rb')as f:
  for seq in range(6):
   count=[0,0];depth=0;per_phase=[];descriptor=None
   for phase in range(141):
    stem=f'phase/{seq}/{phase}/';a=data(f,es,stem+'CRT-before/2013491200.bin',4096);b=data(f,es,stem+'CRT-after/2013491200.bin',4096);cs=a[0x130:0x148]
    assert b[0x130:0x148]==cs and struct.unpack('<6I',cs)==(0xffffffff,0xffffffff,0,0,0,0x020007d0),'Inherited idle OS CS24 descriptor at every phase boundary'
    assert struct.unpack_from('<I',a,0x5c)[0]==CS,'Lock table slot13 names the same CS';descriptor=cs.hex();n=[0,0]
    for index,v in enumerate(struct.iter_unpack('<26I',data(f,es,stem+'api-ledger.bin'))):
     if v[24]not in(5,6):continue
     kind=v[24];assert v[20]==CS and v[9]==v[19]==0 and v[25]==(0x78001075 if kind==5 else 0x780012b1),'Only lock13 Enter/Leave via exact _lock/_unlock return'
     assert v[14]==v[4]+8 and all(v[k]==v[k+10]for k in(3,5,6,7)),'stdcall stack/nonvolatile ABI'
     if kind==5:assert v[0]==13,'Lock index13'
     depth+=1 if kind==5 else -1;assert depth in(0,1),'Same-instance balanced depth';count[kind-5]+=1;n[kind-5]+=1
    assert depth==0,'Balanced at every phase boundary';per_phase.append(n)
   original.append(dict(sequence=seq,enter_leave=count,phases=141,phases_with_lock13=sum(1 for x in per_phase if x[0]),per_phase_enter=[x[0]for x in per_phase],idle_descriptor_hex=descriptor))
 native=[]
 for level in('O0','O2'):
  i,p,es=bundles[level]
  with p.open('rb')as f:
   for seq in range(6):
    stem=f'sequence-{seq}/selected/';native_ptr=None;depth=0;counts=[0,0];init=0;guest=None;apis=0
    names=sorted((k for k in es if k.startswith(stem+'locale-api-')and k.endswith('-witness.bin')),key=lambda k:int(k.split('locale-api-')[1].split('-')[0]))
    for k in names:
     v=struct.unpack('<32Q',data(f,es,k,256));index=int(k.split('locale-api-')[1].split('-')[0]);assert v[:2]==(1,index)
     if v[20]!=CS or v[7]!=1:continue
     assert v[14]==v[15]==1 and v[8]==v[12]==0 and v[16]and v[17]==40 and v[9]==v[11]and v[19]==0,'Typed native CS40 witness'
     g=data(f,es,stem+f'locale-api-{index}-input-0.bin',24);assert guest is None or g==guest,'One immutable guest CS24 input';guest=g
     if v[3]==0x7802e03c:assert init==0 and depth==0;init+=1;native_ptr=v[16]
     elif v[3]in(0x7802e044,0x7802e048):
      assert init==1 and native_ptr==v[16],'Same initialized native resource';kind=5 if v[3]==0x7802e044 else 6;depth+=1 if kind==5 else -1;counts[kind-5]+=1;assert depth in(0,1)
      assert v[2]==(0x7800106f if kind==5 else 0x780012ab)and v[6]==(0x78001075 if kind==5 else 0x780012b1),'Exact source CALL/return pair';apis+=1
     else:raise AssertionError(('Unexpected CS13 API',v))
     assert v[18]==depth
    assert init==1 and depth==0 and counts[0]==counts[1]and apis==sum(counts)
    section=next(v for v in struct.iter_unpack('<16Q',data(f,es,stem+'locale-critical-sections.bin'))if v[1]==CS);assert section[3:5]==tuple(counts)and section[10]==native_ptr and section[11]==40,'Section ledger equals witness counts'
    terminal=next(v for v in struct.iter_unpack('<16Q',data(f,es,f'sequence-{seq}/cleaned/locale-critical-sections.bin'))if v[1]==CS);assert terminal[2]==section[2]and terminal[3]==terminal[4]and terminal[10:12]==(native_ptr,40),'Same balanced native resource at cleanup'
    for phase in range(141):
     for side in('before','after'):assert data(f,es,f'sequence-{seq}/phase-{phase}-{side}-page-2013491200.bin',4096)[0x130:0x148]==guest,'Immutable guest descriptor at every native phase'
    native.append(dict(level=level,sequence=seq,selected_enter_leave=counts,initializations=init,section_selected_fields=list(section[3:10]),section_cleaned_fields=list(terminal[3:10]),cleaned_enter_leave=list(terminal[3:5]),guest_descriptor_hex=guest.hex(),native_resource_extent=40))
 for i,p,es in bundles.values():assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)],'Whole index/payload unchanged after reads'
 paired=[dict(sequence=o['sequence'],original=o['enter_leave'],**{lv:next(n['selected_enter_leave']for n in native if n['level']==lv and n['sequence']==o['sequence'])for lv in('O0','O2')})for o in original]
 equal=all(r['original']==r['O0']==r['O2']for r in paired)
 rp=out/'lock13-counts.json';rp.write_text(json.dumps(dict(original=original,native=native,paired=paired),indent=2)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='Derived current141 lock13 Enter/Leave counts from exhaustive original141 ledgers and native141 source6 typed witnesses with inherited per-record rules; not CRT whole-page policy, footprint or paired141 credit',
  original_per_sequence=[o['enter_leave']for o in original],native_selected_per_sequence={lv:[n['selected_enter_leave']for n in native if n['level']==lv]for lv in('O0','O2')},
  native_cleaned_per_sequence={lv:[n['cleaned_enter_leave']for n in native if n['level']==lv]for lv in('O0','O2')},original_native_selected_counts_equal=equal,inherited_hardcoded_108_reused=False,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,source_model_executed=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(q),sha256=sha(q),original=report['original_per_sequence'],native=report['native_selected_per_sequence'],cleaned=report['native_cleaned_per_sequence'],equal=equal)))
if __name__=='__main__':main(sys.argv[1])
