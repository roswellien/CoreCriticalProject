"""Physically bind implicit count-one D1F8 SAR forms before source evaluation."""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter_v2.py');s=p.read_text();a="exec(compile(s,str(p),'exec'))"
b="""s=s.replace('literal-sorter-evaluation-r2','literal-sorter-evaluation-r3')
before=\"self.program[pc]=self.D.instruction_contract(d)\"
after=\"\"\"self.program[pc]=self.D.instruction_contract(d)
   if d['mnemonic']=='sar'and len(self.program[pc]['decoded_operands'])==1:
    need(d['bytes_hex']=='d1f8'and d['operands']=='eax','Exact physical implicit SAR EAX,count1');self.program[pc]['decoded_operands'].append(dict(kind='immediate',value=1,signed_text='implicit encoding count-one',source_encoding='D1F8'))\"\"\"
assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'))"""
assert s.count(a)==1;s=s.replace(a,b);exec(compile(s,str(p),'exec'))
