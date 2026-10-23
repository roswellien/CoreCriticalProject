"""Finite1577-only larger budget and lossless streamed source ledgers.

Prior failed budget outputs and accepted interpreters remain unchanged. This
isolated source evaluation cannot confer accepted initializer/loader credit.
"""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter_v3.py');s=p.read_text();a="exec(compile(s,str(p),'exec'))"
b='''
s=s.replace('literal-sorter-evaluation-r3','literal-sorter-evaluation-r4')
def revise(before,after):
 global s
 assert s.count(before)==1,before;s=s.replace(before,after)
revise('import collections,hashlib,importlib.util,json,re,struct,sys,time,traceback','import ast,collections,gzip,hashlib,importlib.util,json,re,struct,sys,time,traceback')
revise("self.I=load('message_accepted_integer',pin(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py'));", """original=pin(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py');text=original.read_text();need(text.count('self.steps<=1000000')==1,'Only one inherited base loop budget');bounded=out/'bounded-integer.py';bounded.write_text(text.replace('self.steps<=1000000','self.steps<=40000000'));self.I=load('message_finite1577_integer',pin(bounded));""")
revise("self.P=load('message_accepted_SAR',pin(R/'tools/m4-onexit-review/provider_model.py'))", """provider=pin(R/'tools/m4-onexit-review/provider_model.py');text=provider.read_text();tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Machine');body=ast.get_source_segment(text,node);need(body.count('B.OwnedMachine')==1 and body.count('self.steps<=1000000')==1,'Exact inherited SAR body and only loop budget');body=body.replace('B.OwnedMachine','I.Machine').replace('self.steps<=1000000','self.steps<=40000000');derived=out/'bounded-SAR.py';derived.write_text(body+'\\n');pin(derived);ns={'I':self.I};exec(compile(body,str(derived),'exec'),ns);self.P=type('LiteralSARNamespace',(),dict(Machine=ns['Machine']))""")
revise("self.flag_joins=[];self.current_cpu=None;", "self.flag_joins=FlagLedger(out/'source-defined-flag-joins.bin.gz');self.current_cpu=None;")
revise("self.steps<=1000000,'Finite source evaluation budget'", "self.steps<=40000000,'Finite1577-only source evaluation budget'")
revise("tracepath=self.out/'source-PC-CPU-before-after.bin';self.trace=tracepath.open('wb')", "tracepath=self.out/'source-PC-CPU-before-after.bin.gz';self.trace=gzip.open(tracepath,'wb',compresslevel=1);m.accesses=OperandLedger(self.out/'source-operands.bin.gz');m.PCs=PCInventory()")
revise("finally:self.trace.close()", "finally:self.trace.close();m.accesses.close();self.flag_joins.close()")
revise("self.emit('source-operands.bin',b''.join(struct.pack('<5I',*row)for row in m.accesses));self.emit('source-defined-flag-joins.bin',b''.join(struct.pack('<3I',*row)for row in self.flag_joins));", "self.pin(m.accesses.path);self.pin(self.flag_joins.path);")
revise("return dict(endpoints=endpoints,counts=dict(self.counts)", "return dict(finite_instruction_budget=40000000,lossless_gzip_ledgers=True,endpoints=endpoints,counts=dict(self.counts)")
revise('class SourceEval:', """class OperandLedger:
 def __init__(self,path):self.path=path;self.file=gzip.open(path,'wb',compresslevel=1);self.count=0
 def append(self,row):self.file.write(struct.pack('<5I',*row));self.count+=1
 def __len__(self):return self.count
 def close(self):self.file.close()
class FlagLedger(OperandLedger):
 def append(self,row):self.file.write(struct.pack('<3I',*row));self.count+=1
class PCInventory:
 def __init__(self):self.pcs=set()
 def append(self,pc):self.pcs.add(pc)
 def __iter__(self):return iter(self.pcs)
class SourceEval:""")
exec(compile(s,str(p),'exec'))
'''
assert s.count(a)==1;s=s.replace(a,b);exec(compile(s,str(p),'exec'))
