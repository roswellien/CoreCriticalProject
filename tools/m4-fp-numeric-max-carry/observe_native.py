"""Author model of new carry-domain unit; the frozen helper model remains unchanged."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,itertools,json,mmap,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ancestor=ROOT/'tools/m4-fp-numeric-max-host-boundary/observe.py';closure=ROOT/'reports/m4-fp-numeric-max-host-boundary/author-review-r1'
assert sha(closure/'report.json')=='efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a'
assert sha(ancestor)==json.loads((closure/'pins.json').read_text())['files'][str(ancestor)]
spec=importlib.util.spec_from_file_location('frozen_author_helpers',ancestor);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def initial(t,c1):
 a=list(t);a[6]=0;s=m.initial(a);m.p16(s,2770,(t[4]<<11)|t[6])
 for o,bit in zip(m.SWPOS,m.SWBITS):s[o]=(t[6]>>bit)&1
 s[2739]=c1;return bytes(s)
def expected(s,mem):
 # Exact source-defined FLD C1 write, not a comparison mask or AFTER input.
 s=bytearray(s);s[2739]=0;return m.expected(bytes(s),mem)
def numeric(fx):return [fx[:5],fx[24:28]]+[fx[32+i*16:42+i*16] for i in range(8)]
def check(n,before,mem):
 errors=[]
 def eq(k,a,b):
  if a!=b:errors.append(k)
 eq('whole_expected_BEFORE_view',n[48:4132],m.view(before));eq('whole_expected_BEFORE_pages',n[12300:28684],mem)
 a,cp,ma,ev,rt=expected(before,mem)
 for k,actual,wanted in [('whole_AFTER_CPU_State_FX_ENV',n[4132:8216],a),('complete_provider_checkpoint',n[8216:12300],cp),('whole_four_pages_after',n[28684:45068],ma),('22_ordered_events',n[46148:46588],ev),('three_CALL_RET_routes',n[46588:46648],rt),('complete_counts',struct.unpack_from('<8I',n,46648),(22,1,0,0,3,1,1,2))]:eq(k,actual,wanted)
 hb=n[45068:45580];ha=n[45580:46092];eq('direct_host_numerical_before_cleanup',numeric(hb),numeric(ha));eq('direct_host_full_ENV_before_cleanup',n[46092:46120],n[46120:46148])
 t=struct.unpack_from('<10I',n);eq('authored_host_before_CW_SW_tag_MXCSR',(m.u16(hb),m.u16(hb,2),hb[4],m.u32(hb,24)),(t[3],0x3a20,0x81,0x1f80));eq('authored_host_before_raw80',[hb[32+i*16:42+i*16] for i in range(8)],[struct.pack('<QH',0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0)) for i in range(8)]);eq('authored_host_before_ENV',n[46092:46120],struct.pack('<7I',0xffff0000|t[3],0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b))
 sw=m.status(before);eq('explicit_input_C1_sticky_fields',struct.unpack_from('<2I',n,46680),((sw>>9)&1,sw&0x3f))
 return errors,(a,cp,ma,ev,rt)
def view_c1_diff(actual,wanted):
 allowed={40+2739,3544+3,4056+5};diff={i for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b};return diff<=allowed,diff
def main():
 build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();mode=sys.argv[3];assert mode in ('baseline','repair') and out.parent==BASE and not out.exists();out.mkdir();pins={};rows=[];controls=[];positive=[];fail_samples=[]
 def bind(p,expected_hash=None):
  p=Path(p).resolve();h=sha(p);assert expected_hash is None or h==expected_hash,(str(p),h,expected_hash);pins[str(p)]=h
 try:
  b=json.loads((build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed'];bind(build/'build.json');bind(ancestor);bind(closure/'report.json');bind(closure/'pins.json')
  game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');bind(provider,'91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  fresh=bytearray(m.pe_page(game.read_bytes(),m.BASES[0])+m.pe_page(provider.read_bytes(),m.BASES[1])+m.pe_page(game.read_bytes(),m.BASES[2])+bytes(4096));m.p32(fresh,m.memoff(m.F),m.CAP)
  for level in ('O0','O2'):
   unit=build/f'unit-{level}';bind(unit/'compiled-controls.json');assert json.loads((unit/'compiled-controls.json').read_text())['checks']==106
   hardware=m.Raw.__new__(m.Raw);hardware.path=BASE/f'hardware-build-r1/hardware-{level}.bin';hardware.f=hardware.path.open('rb');hardware.m=mmap.mmap(hardware.f.fileno(),0,access=mmap.ACCESS_READ);hardware.count=18432;hardware.stride=2736;bind(hardware.path);assert hardware.m[:8]==b'MW4NMC01' and len(hardware.m)==24+18432*2736
   for corpus,count in (('carry',18432),('persistent',2304)):
    raw=m.Raw(unit/f'{corpus}.bin',b'MW4NMCI1',46688);assert raw.count==count;bind(raw.path);errors=Counter();failed=0;c1_only=0;carry=0;previous=None;sample=None
    cases=itertools.product(range(2),range(16) if corpus=='carry' else (0,),(0,1,7),(0,2,32,34),m.CW,(0,7),(0,1));i=0
    for seq,case in enumerate(cases):
     rep,inp,depth,sticky,cw,top,c1=case;t=(rep,inp,m.ROOTPC,cw,top,depth,sticky,0,1,1);first=initial(t,c1);mem=bytearray(fresh);m.p32(mem,m.memoff(0x78115004),m.INPUTS[inp])
     for phase in range(1 if corpus=='carry' else 2):
      n=raw.row(i);assert struct.unpack_from('<10I',n)==t and struct.unpack_from('<2I',n,40)==(seq,phase)
      if phase:
       first=bytearray(previous[0][40:3544]);m.p32(first,2312,m.F);m.p32(first,2472,m.ROOTPC);first=bytes(first);mem=bytearray(previous[2]);carry+=1
      e,ex=check(n,first,bytes(mem));errors.update(e);failed+=bool(e)
      checks=[view_c1_diff(n[48:4132],m.view(first)),view_c1_diff(n[4132:8216],ex[0]),view_c1_diff(n[8216:12300],ex[1])]
      only=all(x[0] for x in checks) and n[12300:28684]==bytes(mem) and n[28684:45068]==ex[2] and n[46148:46588]==ex[3] and n[46588:46648]==ex[4]
      only=only and not set(e)-{'whole_expected_BEFORE_view','whole_AFTER_CPU_State_FX_ENV','complete_provider_checkpoint','explicit_input_C1_sticky_fields'};c1_only+=int(bool(e) and only)
      if e and len(fail_samples)<8:fail_samples.append(dict(level=level,corpus=corpus,index=i,case=case,phase=phase,errors=e,C1_only=only,diff_view_offsets=[sorted(x[1]) for x in checks]))
      if corpus=='carry':
       h=hardware.row(seq);cp=n[8216+3544:8216+4056];after=n[4132+3544:4132+4056]
       # Actual local hardware and native source PCs/selectors/cap masks differ.
       # Compare the declared numerical/tag/status domain, retaining provenance.
       differences=[]
       for name,x,y in (('BEFORE',n[48+3544:48+4056],h[36:548]),('FLD',cp,h[548:1060]),('FSTP',after,h[1060:1572])):
        if numeric(x)!=numeric(y):differences.append(name)
       if mode=='repair':assert not differences,(level,seq,differences)
       else:assert differences==(['FLD','FSTP'] if c1 else []),(level,seq,differences)
      previous=ex;sample=n;i+=1
    assert i==count
    rows.append(dict(level=level,corpus=corpus,records=count,failed_records=failed,C1_only_failures=c1_only,differences=dict(errors),carry_boundaries=carry))
    if mode=='repair':
     # Source-computed whole-State and direct numerical preservation controls.
     for off in (48,88+3503,88+2739,4132,4172+2739,8256+2739,8256+2772,12300+0x800,28684+16383,45580+24,46120+12,46148,46588,46648,46680,46684):
      q=bytearray(sample);q[off]^=1;e,_=check(q,first,bytes(mem));assert e,(level,corpus,off);controls.append(dict(level=level,corpus=corpus,offset=off,rejected_by=e))
     for off in (45580+400,45580+5,45580+500):
      q=bytearray(sample);q[off]^=1;assert not check(q,first,bytes(mem))[0];positive.append(dict(level=level,corpus=corpus,offset=off,scope='volatile SIMD/reserved storage'))
  passed=not any(x['failed_records'] for x in rows)
  if mode=='baseline':assert not passed and all(x['failed_records']==x['C1_only_failures']==(9216 if x['corpus']=='carry' else 1152) for x in rows)
  else:assert passed
  bind(__file__);(out/'observer-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'observer-source.py')
  report=dict(passed=passed,mode=mode,expected_measured_baseline_failure=mode=='baseline',comparisons=rows,samples=fail_samples,negative_controls=controls,scope_positive_controls=positive,scope='Authored carry native/hardware unit only, no actual original guest execution or connected27 acceptance',provenance='Compiled native full3504 State/events/r9 routes vs input-derived architecture model; hardware unit has separately captured host64 metadata. Neither hardware nor earlier original AFTER feeds native execution.',FP_condition_scope='FLD no-overflow C1=0 source-defined. FSTP final C1/no new precision and C0/C2/C3/dead raw80 observational; incoming sticky PE never grants new rounding credit',original_executed=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=passed,expected_baseline_failure=mode=='baseline',comparisons=rows,controls=len(controls))))
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-observer-source.py').write_bytes(Path(__file__).read_bytes());raise
if __name__=='__main__':main()
