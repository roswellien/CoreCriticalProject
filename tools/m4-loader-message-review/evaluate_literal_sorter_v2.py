"""Add exact two literal CDQ sites: signed EAX projection to EDX, no flags."""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter.py');s=p.read_text()
def change(a,b):
 global s
 assert s.count(a)==1;s=s.replace(a,b)
change('literal-sorter-evaluation-r1','literal-sorter-evaluation-r2')
change("'sar','setl','call'","'sar','setl','cdq','call'")
change("    if row['mnemonic']!='setl':return super().step()", "    if row['mnemonic']not in('setl','cdq'):return super().step()")
change("self.destination(row['decoded_operands'][0],bool(self.flag('SF'))!=bool(self.flag('OF')));self.emit('instruction-after',row=row)","\n    if row['mnemonic']=='cdq':\n     S.I.need(row['bytes_hex']=='99'and not row['decoded_operands'],'Exact physical CDQ sign-extension form');self.reg('edx',0xffffffff if self.reg('eax')&0x80000000 else 0)\n    else:self.destination(row['decoded_operands'][0],bool(self.flag('SF'))!=bool(self.flag('OF')))\n    self.emit('instruction-after',row=row)")
exec(compile(s,str(p),'exec'))
