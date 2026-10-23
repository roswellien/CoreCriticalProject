"""Current physical131 source continuity; no cached current result oracle."""
import json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def prove(C,pin):
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=read(R/'reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
 actual=read(C['source_preparation']['path'],C['source_preparation']['sha256']);order=read(C['selected_order']['path'],C['selected_order']['sha256']);directory=Path(C['source_preparation']['path']).parent
 assert actual['root_count']==len(order)==141 and actual['phases']==846 and actual['callback_count']==111
 prior={r['entry']for r in old['selected_order']};assert len(prior)==131 and [r for r in order if r['entry']in prior]==old['selected_order']
 text=pin(directory/'spec.hpp').read_text();match=re.search(r'std::array<CodeBinding,(\d+)> code_bindings\{\{(.*?)\}\};',text,re.S);assert match
 current=[tuple(int(v.strip(),0)for v in row.split(','))for row in re.findall(r'\{([^{}]+)\}',match[2])];assert len(current)==int(match[1])==6411 and len(set(current))==6411
 declared=set(current);rows=old['source_spans'];assert len(rows)==3980
 for row in rows:assert tuple(row[k]for k in('pc','size','image_offset','origin'))in declared
 def pages(p):
  b=pin(p).read_bytes();assert b[:8]==b'MW4J124P';n=struct.unpack_from('<I',b,8)[0];assert len(b)==12+n*4104
  out={}
  for i in range(n):
   off=12+i*4104;address,permission=struct.unpack_from('<2I',b,off);assert address not in out and address%4096==0;out[address]=(permission,b[off+8:off+4104])
  return out
 oldpages=pages(R/'reports/m4-startup131-original/preparation-r4/pages.bin');newpages=pages(directory/'pages.bin')
 for row in rows:
  at=row['pc'];n=row['size'];assert n>0 and(at&4095)+n<=4096;page=at&~4095;assert oldpages[page][1][at&4095:(at&4095)+n]==newpages[page][1][at&4095:(at&4095)+n]
 return dict(passed=True,current_physical_131_root_table_pairs=131,current_exact_retained_source_spans=3980,current_total_source_spans=6411,source_model_equivalence=False,current_result_oracle_used=False,full_original131_CPU_executed=False,scope='Every accepted131 physical source declaration and byte span remains current141, exact relative root/slot order. Fresh semantic families and actual strict observation are separate required domains.',original_validation_sha256=C['validation']['sha256'],source_AFTER_seed=False,canonical_reader_opened=False,initializer_credit=0)
