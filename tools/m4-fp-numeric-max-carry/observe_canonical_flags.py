"""Author input-derived observer of complete malformed-byte/refused-retry records."""
from pathlib import Path
import hashlib,importlib.util,itertools,json,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
helper=ROOT/'tools/m4-fp-numeric-max-host-boundary/observe.py';closure=ROOT/'reports/m4-fp-numeric-max-host-boundary/author-review-r1'
assert sha(closure/'report.json')=='efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a'
assert sha(helper)==json.loads((closure/'pins.json').read_text())['files'][str(helper)]
spec=importlib.util.spec_from_file_location('frozen_author_helpers',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def numeric(fx):return [fx[:5],fx[24:28]]+[fx[32+i*16:42+i*16] for i in range(8)]
def diagnostic_view(s):
 # Exact authored projection of malformed bytes; never an admission or execution model.
 sw=m.u16(s,2770)&0xb880
 for o,bit in zip(m.SWPOS,m.SWBITS):sw|=s[o]<<bit
 sw&=0xffff;fx=bytearray(s[2768:3280]);m.p16(fx,2,sw);fx[6:24]=bytes(18);top=(sw>>11)&7;ft=0xffff
 for i in range(8):
  raw=s[2486+i*16:2496+i*16];fx[32+i*16:42+i*16]=raw;fx[160+i*16:176+i*16]=s[16+i*64:32+i*64];phys=(top+i)&7
  if fx[4]&(1<<phys):ft=(ft&~(3<<(phys*2)))|(m.tag(raw)<<(phys*2))
 env=struct.pack('<7I',0xffff0000|m.u16(s,2768),0xffff0000|sw,0xffff0000|ft,m.u32(s,2776),m.u16(s,2780)|(m.u16(s,2774)<<16),m.u32(s,2784),0xffff0000|m.u16(s,2788))
 return m.cpu(s)+s+fx+env
def expected(field,bad,coherent,retry,fresh):
 t=(0,0,m.ROOTPC,0x37f,7 if field%2 else 0,1,0,0,0,0);valid=bytes(m.initial(t));s=bytearray(valid)
 if not retry:s[m.SWPOS[field]]=bad
 s=bytes(s);v=diagnostic_view(s);software=m.view(valid)[3544:4056] if retry or not coherent else v[3544:4056]
 return t,v,software
def check(n,field,bad,coherent,retry,scenario,fresh):
 errors=[]
 def eq(k,a,b):
  if a!=b:errors.append(k)
 t,v,software=expected(field,bad,coherent,retry,fresh)
 eq('exact_schedule_tag',n[:40],struct.pack('<10I',*t));eq('scenario_retry',n[40:48],struct.pack('<2I',scenario,retry));eq('whole_input_State_CPU_projectedFX_ENV',n[48:4132],v);eq('whole_after_State_CPU_projectedFX_ENV',n[4132:8216],v)
 unentered=bytearray(4084);m.p32(unentered,32,0x202) # Exact frozen Cpu32 default, not an executed checkpoint.
 eq('unentered_checkpoint',n[8216:12300],bytes(unentered));eq('whole_pages_before',n[12300:28684],fresh);eq('whole_pages_after',n[28684:45068],fresh);eq('unentered_events',n[46148:46588],bytes(440))
 rt=struct.pack('<15I',*([m.CAP,m.ROOTPC,m.CAP,0,0]+[0]*10 if not retry else [0]*15));eq('exact_incomplete_route_or_no_retry_route',n[46588:46648],rt);eq('fault_poison_owner_counts',n[46648:46680],struct.pack('<8I',0,0,1,1,0 if retry else 1,0,0,0))
 control=(field,bad,coherent,retry,0,0,m.ROOTPC,0,0,1,1,1 if retry else 0,1,1,1,1);eq('first_fault_status_and_reuse',n[46680:46744],struct.pack('<16I',*control));eq('actual_Runtime_FX_before',n[46744:47256],software);eq('actual_Runtime_FX_after',n[47256:47768],software)
 hb=n[45068:45580];ha=n[45580:46092];cw=(0x7f,0x37f,0xb7f)[scenario%3]
 eq('direct_numerical_host_preserved_before_cleanup',numeric(hb),numeric(ha));eq('direct_ENV_preserved_before_cleanup',n[46092:46120],n[46120:46148]);eq('authored_host_CW_SW_tag_MXCSR',(m.u16(hb),m.u16(hb,2),hb[4],m.u32(hb,24)),(cw,0x3a20,0x81,0x1f80));eq('authored_host_full_ENV',n[46092:46120],struct.pack('<7I',0xffff0000|cw,0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b));eq('authored_host_all_raw80',[hb[32+i*16:42+i*16] for i in range(8)],[struct.pack('<QH',0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0)) for i in range(8)])
 return errors
def main():
 build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();pins={};rows=[];negative=[];positive=[]
 def bind(p):pins[str(Path(p).resolve())]=sha(p)
 try:
  b=json.loads((build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed'];bind(build/'build.json');bind(helper);bind(closure/'report.json');bind(closure/'pins.json')
  game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';bind(game);bind(provider)
  assert sha(game)=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf' and sha(provider)=='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'
  fresh=bytearray(m.pe_page(game.read_bytes(),m.BASES[0])+m.pe_page(provider.read_bytes(),m.BASES[1])+m.pe_page(game.read_bytes(),m.BASES[2])+bytes(4096));m.p32(fresh,m.memoff(m.F),m.CAP);fresh=bytes(fresh)
  for level in ('O0','O2'):
   unit=build/f'unit-{level}';bind(unit/'canonical-controls.json');d=json.loads((unit/'canonical-controls.json').read_text());assert d['passed'] and d['checks']==661 and d['records']==132 and d['malformed_scenarios']==d['corrected_poisoned_retries']==66
   raw=m.Raw(unit/'canonical-controls.bin',b'MW4NMB01',47768);bind(raw.path);assert raw.count==132;i=0
   for scenario,(field,bad,coherent) in enumerate(itertools.product(range(11),(2,3,255),(0,1))):
    for retry in (0,1):
     n=raw.row(i);errors=check(n,field,bad,coherent,retry,scenario,fresh);assert not errors,(level,i,errors);i+=1
   rows.append(dict(level=level,records=i,malformed_scenarios=66,corrected_poisoned_retries=66,whole3504State=True,whole4pages=True,actual_Runtime_FX=True,direct_host_numerical_and_ENV=True))
   # Actual refused IE=2 alias case, plus corrected retry, tested by causal raw changes.
   for index in (2,3):
    n=raw.row(index);args=(0,2,1,index%2,1,fresh)
    for off in (0,40,44,88+m.SWPOS[0],4172+3503,8216,12300+0x800,28684+16383,45580+2,45580+24,45580+32,46120+12,46148,46588,46648,46680+16,46680+24,46680+40,46744+3,47256+3):
     q=bytearray(n);q[off]^=1;e=check(q,*args);assert e,(level,index,off);negative.append(dict(level=level,index=index,offset=off,rejected_by=e))
    for off in (45580+400,45580+5,45580+500):
     q=bytearray(n);q[off]^=1;assert not check(q,*args);positive.append(dict(level=level,index=index,offset=off,scope='volatile SIMD/reservedFX observed only'))
  bind(__file__);(out/'observer-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'observer-source.py')
  report=dict(passed=True,comparisons=rows,negative_controls=negative,scope_positive_controls=positive,scope='New canonical byte guard actual compiled refusals, not numeric equivalence of malformed inputs; direct host capture before cleanup',changes_separate=['11-byte boolean admission before status projection','Inherited PE/C1 admissible numerical domain','Inherited typed no-overflow FLD C1 zero write'],original_executed=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=True,rows=rows,negative=len(negative),positive=len(positive))))
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-observer-source.py').write_bytes(Path(__file__).read_bytes());raise
if __name__=='__main__':main()
