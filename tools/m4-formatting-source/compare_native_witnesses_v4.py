"""Exact private formatter observer joins to the independently computed source."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={}
def need(x,s):
 if not x:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve()
 with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
 need(h is None or v==h,'Exact witness dependency '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rows(a,p,n):
 raw=a.data(p);need(len(raw)%(8*n)==0,'Whole private witness rows '+p);return list(struct.iter_unpack('<'+str(n)+'Q',raw))
def equal(a,b,s):need(a==b,s+' '+str((a,b))[:450])
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;need(not out.exists(),'Fresh observer witness gate');out.mkdir(parents=True);passed=False;a=None;counts=collections.Counter();proofs=[]
 try:
  receipt_path=ROOT/'reports/m4-formatting-source/native-source-r9/report.json';source=read(receipt_path,'0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306');need(source['passed']and not source['candidate_AFTER_machine_seed']and source['reader_closed'],'Passed independent full source producing receipt')
  derivation=receipt_path.parent/'source-derivations.json';sources=read(derivation,source['files'][str(derivation.resolve())]);need(len(sources)==6,'All six literal source phases')
  execution=read(ROOT/'reports/m4-formatting-native/fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0');need(execution['passed'],'Both real native workers passed')
  normal=read(ROOT/'reports/m4-formatting-source/normal-contracts-r1/normal-contracts.json','121d091142d4a72a84e26aeb8254724b8f3a6ebac1593dc8296eecc2160e18aa')
  D=load('formatting_witness_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py')
  for level in('O0','O2'):
   a=D.DirectSet(execution['workers'][level]['transport'],pin);expected_calls=[];expected_owned=[];expected_pubs=[];expected_dispatch=[]
   for phase in range(3):
    r=next(r for r in sources if r['level']==level and r['phase']==phase);c=normal['cases'][phase];owner=r['owner'];guest=owner['guest'];generation=owner['generation'];stem=f'actual-after-root-{phase}/';source_accesses=list(struct.iter_unpack('<IIQII',a.data(stem+'locale-source-accesses.bin')));base=len(source_accesses)-len(r['source_accesses'])
    equal(source_accesses[base:],[tuple(row)for row in r['source_accesses']],'Authoritative source-derived complete phase ledger')
    F=r['calls'][0]['frame']+36
    for ci,call in enumerate(r['calls']):
     need(call['returned']and call['returned_ESP']==call['frame']+4,'Literal cdecl RET preserves exact current frame')
     row=[1,r['root'],call['PC'],call['target'],call['frame'],F,len(call['args'])]+call['args']+[0]*(4-len(call['args']))+[0,guest if ci else 0,generation if ci else 0,1,call['result']]
     need(len(row)==16,'Exact sixteen-Qword CALL observer schema');expected_calls.append(tuple(row));counts['literal_private_cdecl_rows']+=1
    own=[]
    for i,row in enumerate(source_accesses):
     if i>=base and row[0]in(0x7801042a,0x78022bd5):
      pc,address,value,width,writing=row;need(guest<=address and address+width<=guest+owner['requested'],'Exact live current requested owner interval')
      own.append((1,r['root'],len(own),pc,address,width,writing,value,guest,generation,address-guest,i+1))
    equal([(w[3],w[10],w[5],bool(w[6]))for w in own],[(w['PC'],w['offset'],w['width'],w['writing'])for w in c['owned_accesses']],'All source-defined normal owner operations in exact order')
    for w in own:
     if not w[6]:need(w[7]==bytes.fromhex(owner['initial'])[w[10]],'NUL RMW read is the genuine untouched acquired byte')
    expected_owned+=own;counts['literal_private_owned_operands']+=len(own)
    field=c['root_contract']['owned_pointer_field'];pub=[(i,row)for i,row in enumerate(source_accesses)if i>=base and row[0]==0x4deabc and row[1]==field]
    need(len(pub)==1 and pub[0][1]==(0x4deabc,field,guest,4,1),'One exact primary owner publication from literal source')
    expected_pubs.append((1,r['root'],0x4deabc,field,guest,generation,owner['requested'],owner['extent'],pub[0][0]+1,0,0,0));counts['literal_private_publications']+=1
    for di,d in enumerate(r['dispatches']):
     i=d['source_access_index'];need(source_accesses[i]==(d['PC'],d['table_read'],d['target'],4,0),'Exact literal physical table read relation')
     expected_dispatch.append((1,r['root'],di,d['PC'],d['index'],d['table_read'],d['target'],i+1));counts['literal_private_table_dispatches']+=1
    equal(rows(a,stem+'formatting-calls.bin',16),expected_calls,'Every complete actual private CALL row equals literal source')
    equal(rows(a,stem+'formatting-owned.bin',12),expected_owned,'Every complete actual private owner row equals literal source')
    equal(rows(a,stem+'formatting-publications.bin',12),expected_pubs,'Every complete actual private publication row equals literal source')
    equal(rows(a,stem+'formatting-dispatches.bin',8),expected_dispatch,'Every complete actual private dispatch row equals literal source')
    status=tuple(struct.unpack('<10I',a.data(stem+'formatting-status.bin')));equal(status,(1,0,phase+1,F,guest,generation,len(own),4,1,0),'Exact finite completed formatter lifetime status')
    proofs.append(dict(level=level,phase=phase,root=r['root'],source_access_start=base,status=status,owner=owner,calls=[list(w)for w in expected_calls[-3:]],owned=[list(w)for w in own],publication=list(expected_pubs[-1]),dispatches=[list(w)for w in expected_dispatch[-4:]]))
   for stem in('actual-live/','actual-cleaned/'):
    equal(rows(a,stem+'formatting-calls.bin',16),expected_calls,'Whole completed CALL history conserved after lifetime')
    equal(rows(a,stem+'formatting-owned.bin',12),expected_owned,'Whole completed owner history conserved after lifetime')
    equal(rows(a,stem+'formatting-publications.bin',12),expected_pubs,'Whole completed publication history conserved after lifetime')
    equal(rows(a,stem+'formatting-dispatches.bin',8),expected_dispatch,'Whole completed dispatch history conserved after lifetime')
    equal(a.data(stem+'formatting-status.bin'),a.data('actual-after-root-2/formatting-status.bin'),'Whole completed scalar status conserved')
   live=rows(a,'actual-live/locale-allocations.bin',16);cleaned=rows(a,'actual-cleaned/locale-allocations.bin',16);need(len(live)==len(cleaned)==4,'Producer plus three actual formatter owners')
   for before,after in zip(live,cleaned):
    need(before[:8]==after[:8]and before[12:]==after[12:]and before[8]and before[9]==1 and after[8:10]==(0,0)and before[7]==before[8]and before[10:12]==(0,0)and after[10:12]==((1,0)if before[1]==0x31000000 else(0,1)),'Every actual native allocation has one cleanup free and preserved identity')
    counts['actual_cleaned_allocation_lifetimes']+=1
   static=read(ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json');site_names={r['pc']:r['API']for r in static['API_sites']};enters=collections.Counter();leaves=collections.Counter()
   actual_summary=tuple(struct.unpack('<32I',a.data('actual-cleaned/locale-summary.bin')))
   for i in range(actual_summary[18]):
    w=a.words('actual-cleaned/locale-api-'+str(i)+'-witness.bin',32,'Q')
    if not w[31]and site_names.get(w[2])in('EnterCriticalSection','LeaveCriticalSection'):
     need(w[2]in {pc for row in sources if row['level']==level for pc in row['source_PCs']},'Actual serial lock API site was executed by literal selected source')
     (enters if site_names[w[2]]=='EnterCriticalSection'else leaves)[w[20]]+=1
   equal(enters,leaves,'All independently source-joined serial API pairs balance')
   sections=rows(a,'actual-cleaned/locale-critical-sections.bin',16);need(len(sections)==5 and all(w[0]==1 and w[3:6]==(enters[w[1]],leaves[w[1]],0)and w[6:10]==(1,1,1,1)and w[10]and w[11]==40 for w in sections),'All five actual native CS40 lifetimes match genuine source-joined enter/leave counts and one initialize/delete')
   summary=tuple(struct.unpack('<32I',a.data('actual-cleaned/locale-summary.bin')));need(summary[9:16]==(4,1,3,5,5,0,0)and summary[23]==1 and not summary[30]and not summary[31],'Actual finished allocations/resources/private heap all close')
   counts['actual_cleaned_native_CS_lifetimes']+=5
   need(source['counts']['complete_actual_lifecycles']==2 and source['counts']['literal_producer_source_frees']==2,'Authoritative source receipt derives complete postcleanup State/CPU and source producer release');counts['outside_return_whole_State_source_proofs_consumed']+=1
   a.close();a.entries.clear();a.bundles.clear();a=None
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if a is not None:a.close();a.entries.clear();a.bundles.clear()
  pin(__file__);(out/'witness-source-relations.json').write_text(json.dumps(proofs,indent=2)+'\n');pin(out/'witness-source-relations.json')
  report=dict(passed=passed,scope='Bounded private formatter observers and genuine native cleanup joined to independent persistent literal source',source_receipt=str(receipt_path),source_receipt_sha256='0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306',counts=dict(counts),reader_closed=True,candidate_AFTER_source_seed=False,initializer_credit=0,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
