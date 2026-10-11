"""Extend static operand grammar for exact x87 operands; no execution."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=R/'tools/m4-hypot-original/prepare.py';q=p.with_name('prepare_v2.py');assert not q.exists();s=p.read_text()
 a=" for graph in graphs.values():"
 b=""" saved_operand=D.operand
 def operand(value):
  v=value.strip();match=re.fullmatch(r'st\\((\\d)\\)',v)
  if match:return dict(kind='x87-register',index=int(match[1]),bits=80)
  return saved_operand(value)
 D.operand=operand
 for graph in graphs.values():"""
 assert s.count(a)==1;s=s.replace(a,b)
 a="));rows.append(r)"
 b="""))
   if v['mnemonic'].startswith('f'):
    memory=[i for i,o in enumerate(r['decoded_operands'])if o['kind']=='memory'];store=v['mnemonic']in('fst','fstp')
    r['explicit_memory_reads']=[]if store else memory;r['explicit_memory_writes']=memory if store else [];r['x87_effects']='Literal source FP instruction; no numerical expected values supplied'
   rows.append(r)"""
 assert s.count(a)==1;s=s.replace(a,b)
 a=" constants=json.loads(pin(BASE/'recovery-r1/physical-constants.json').read_bytes())"
 b=a+"\n for c in constants:\n  address=c['address'];need(bytes(records[address&~4095][1][address&4095:(address&4095)+c['bytes']]).hex()==c['hex'],'Whole raw source constant input equals exact physical image')"
 assert s.count(a)==1;s=s.replace(a,b)
 a="pin(__file__)";b="pin(__file__);pin(R/'tools/m4-hypot-original/prepare.py');pin(R/'tools/m4-hypot-original/derive_prepare_v2.py')"
 assert s.count(a)==1;s=s.replace(a,b);ast.parse(s);q.write_text(s)
 out=R/'reports/m4-hypot-original/preparation-derivation-r1';assert not out.exists();out.mkdir(parents=True)
 report=dict(passed=True,scope='Exact static source x87 operand grammar and read-only FLD/arithmetic versus write-only FSTP descriptors; source constant physical input admission',prior_preparation_attempt_error='Static decoder lacked st(3) operand; occurred before output directory creation and without machine execution',capture_reader_opened=False,original_executed=False,files={str(x.resolve()):sha(x)for x in (p,q,Path(__file__))})
 z=out/'report.json';z.write_text(json.dumps(report,indent=2)+'\n');print(sha(z))
if __name__=='__main__':main()
