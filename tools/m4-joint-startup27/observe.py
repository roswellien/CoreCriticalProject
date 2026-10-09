"""Author checkpoint of actual original/native27 sequences and carried state.

The root's separate full semantic/failure review remains required. Numeric
expectations come from the previously reviewed BEFORE-only oracle; original
software State/events/routes remain unobserved by hardware.
"""
from pathlib import Path
import hashlib,importlib.util,json,mmap,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup27';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),h,v);PINS[str(p)]=v;return p
prior=ROOT/'reports/m4-joint27-startup/root-numeric-carry-r2/pins.json'
bindings=json.loads(pin(prior).read_text())['files'];oracle=ROOT/'tools/m4-joint27-startup/root_numeric_carry.py';pin(oracle,bindings[str(oracle.resolve())])
spec=importlib.util.spec_from_file_location('author_joint27_numeric',oracle);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
def words(b,o,n):return struct.unpack_from('<'+'I'*n,b,o)
def fields(b):return {'tag':words(b,0,9),'before':words(b,36,10),'after':words(b,76,10),'fx0':b[116:628],'fx1':b[628:1140],'env0':b[2164:2192],'env1':b[2192:2220],'memory0':b[2276:59620],'memory1':b[59620:116964]}
def fx(f):return M.C.numerical(f)+[f[160:288]]
def common_check(original,native,iat):
 o=fields(original);n=fields(native);assert o['tag'][:8]==n['tag'][:8]
 for name in ('before','after'):
  a=list(o[name]);b=list(n[name]);a[8]&=~16;b[8]&=~16;assert a==b,('definedCPU',name)
 for name in ('fx0','fx1'):assert fx(o[name])==fx(n[name]),('architecturalFP/XMMandrawdeadobservation',name)
 assert o['env0']==n['env0'] and o['env1']==n['env1'],'Complete direct legacyENV'
 for name in ('memory0','memory1'):
  projected=bytearray(o[name]);assert words(projected,11*4096+0x4fc,1)==(0x780c10f0,);struct.pack_into('<I',projected,11*4096+0x4fc,iat);assert projected==n[name],('14wholepagesonlyoneIATprojection',name)
 return o,n
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True);failure=None
 counts={'architectural_pairs':0,'numeric_BEFORE_only_predictions':0,'whole3504_carry_boundaries':0,'original_CPU_FX_ENV_page_carry_boundaries':0,'host_sequence_boundaries':0,'repeat_phase_pairs':0,'corruption_rejections':0}
 try:
  native=BASE/'native-boundary-capture-r1';original=BASE/'original-capture-r1'
  for run in (native,original):
   receipt=json.loads(pin(run/'report.json').read_text());assert receipt['passed']
   for p,h in json.loads(pin(run/'pins.json').read_text())['files'].items():pin(p,h)
  extract=json.loads(pin(BASE/'original-extraction-r1/extraction.json').read_text());iat=extract['IAT_relocation']['raw_file'];order=extract['order'];assert len(order)==27
  with pin(original/'raw.bin').open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
   assert raw[:8]==b'MW4J27O1' and words(raw,8,6)==(1,48,27,1296,14,117684)
   for level in ('O0','O2'):
    with pin(native/level/'native.bin').open('rb')as nf,pin(native/level/'sequences.bin').open('rb')as sf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ)as nr,mmap.mmap(sf.fileno(),0,access=mmap.ACCESS_READ)as sr:
     assert nr[:8]==b'MW4J27N1' and words(nr,8,6)==(1,48,27,1296,14,132636)
     repeated={}
     for seq in range(48):
      summary=sr[24+seq*122824:24+(seq+1)*122824];assert words(summary,0,12)==(seq,seq//24,M.C.O.ORACLE.CWS[(seq%24)//2],(seq%2)*7,1,27,0,0,0,0,0,0)
      M.numerical_boundary(summary);counts['host_sequence_boundaries']+=1;previous=None;previous_o=None
      for phase,entry in enumerate(order):
       index=seq*27+phase;o=raw[32+index*117684:32+(index+1)*117684];n=nr[32+index*132636:32+(index+1)*132636]
       assert words(n,0,5)==(seq,seq//24,phase,entry['slot'],entry['entry']);assert o[116964:]==bytes(720)
       of,nf=common_check(o,n,iat);counts['architectural_pairs']+=1
       M.projection(n,M.state(n));M.projection(n,M.state(n,True),True)
       if phase:
        assert M.state(n)==M.external(M.state(previous,True),entry['entry']) and M.memory(n)==M.memory(previous,True),'Every3504Statebyte/all14pages carry with explicit external CALL CPU and integerFXalias projection'
        counts['whole3504_carry_boundaries']+=1
        cpu=list(previous_o['after']);cpu[4]=0x20001800;cpu[9]=entry['entry'];assert tuple(cpu)==of['before']
        assert of['fx0']==previous_o['fx1'] and of['env0']==previous_o['env1'] and of['memory0']==previous_o['memory1'];counts['original_CPU_FX_ENV_page_carry_boundaries']+=1
       if entry['entry']==0x4c19f0:M.numeric(n);counts['numeric_BEFORE_only_predictions']+=1
       if seq>=24:
        prior_o,prior_n=repeated[(seq%24,phase)]
        for key in ('before','after','fx0','fx1','env0','env1','memory0','memory1'):assert of[key]==prior_o[key]
        # Native hidden State seed intentionally depends on repeat; observable
        # CPU/FX/ENV/pages are the repeat relation, every otherbyte still carries.
        for key in ('before','after','fx0','fx1','env0','env1','memory0','memory1'):assert nf[key]==prior_n[key]
        counts['repeat_phase_pairs']+=1
       else:repeated[(seq%24,phase)]=(of,nf)
       if seq in (0,47)and phase in (0,18,26):
        for at in (36,76,116,628,2164,2192,2276,59620):
         changed=bytearray(n);changed[at]^=1;rejected=False
         try:common_check(o,changed,iat)
         except AssertionError:rejected=True
         assert rejected;counts['corruption_rejections']+=1
       previous=n;previous_o=of
      assert summary[4632:8136]==M.state(previous,True) and summary[65480:122824]==M.memory(previous,True)
  for module in (M,M.C,M.P,M.R,M.C.O):
   for p,h in getattr(module,'PINS',{}).items():pin(p,h)
 except Exception:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 report={'passed':failure is None,'failure':failure,'scope':'Author actual original/native27 architectural pairs, numeric BEFORE prediction, complete State/pagecarry and direct sequence caller numerical/legacyENV preservation; separate independent whole semantic/failure gate required','counts':counts,'root_count':27,'AF_bit4_defined_equality_excluded':'Source XOR leaves AF architecturally undefined; all otherCPU/flagbits checked','FX_scope':'CW/SW/TOP/tag/MXCSR/eight raw80 registers/eight XMM; reservedpadding/capabilitymask not equalityguarantee; deadraw80 equality observation only','ENV_scope':'Direct full28B legacy metadata separatefromFX metadata','IAT_scope':'Only original owning5BB4FCcell actualleaf→admitted rawfile input for exactfull14page transport','original_software_State_events_routes_observed':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__)
 for p in out.iterdir():
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n');print(json.dumps({'passed':failure is None,'counts':counts}),flush=True)
 if failure:raise RuntimeError(failure)
if __name__=='__main__':main(sys.argv[1])
