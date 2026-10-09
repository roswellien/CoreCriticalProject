"""Derive each new object header from its own genuine branch BEFORE input."""
from pathlib import Path
import importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('mfc_header_literal_game',ROOT/'tools/m4-mfc-source/game_model.py');G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
PROGRAM,CALLBACKS=G.source_program()
def derive(root,cpu,memory):
 state=bytearray(3504)
 for reg,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu):struct.pack_into('<I',state,G.I.REG[reg],value)
 for name,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[G.I.FLAGS[name]]=(cpu[8]>>bit)&1
 struct.pack_into('<I',state,2472,root['entry']);m=G.Machine(state,bytes(512),struct.pack('<10I',*cpu),memory,program=PROGRAM,callbacks=CALLBACKS);m.call_stack.append((root['entry'],cpu[4],0x410a80,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));allocs=[]
 def positive(model,target):
  G.I.need(target==0x780012b3 and model.PCs[-1]==0x5f401eb5,'Exact source positive MFC helper frontend');request=int.from_bytes(model.bytes(model.reg('esp')+4,4),'little');G.I.need(0<request<=512,'Bounded source request');pointer=0x36000000+len(allocs)*4096;model.memory[pointer]=bytearray(b'\xcd'*4096);allocs.append(pointer);model.api_return(0x5f401eb5,0,pointer)
 m.run(stop=lambda x:x.cursor==0x5ac140,api=positive)
 headers=[];addresses={o['address']for o in root['objects']}
 for ai,(pc,address,value,n,w)in enumerate(m.accesses):
  if not(w and n==1 and 0x400000<=address<0x1000000):continue
  previous=[(ri,rpc,ra,rv,rn)for ri,(rpc,ra,rv,rn,rw)in enumerate(m.accesses[:ai])if not rw and rn==1 and 0x20001000<=ra<0x20002000];G.I.need(previous,'Actual header requires literal source stack byte read');ri,rpc,ra,rv,rn=previous[-1]
  saves=[(si,spc,sa,sv,sn)for si,(spc,sa,sv,sn,sw)in enumerate(m.accesses[:ri])if sw and sa<=ra<sa+sn];G.I.need(saves,'Source high stack byte has explicit literal source store');si,spc,sa,sv,sn=saves[-1];G.I.need(((sv>>(8*(ra-sa)))&255)==rv==value,'Exact last stack-byte AL/source-store/header-write provenance')
  reads=[dict(access_index=ri,pc=rpc,address=ra,value=rv,bytes=rn,source_store_index=si,source_store_pc=spc,source_store_address=sa,source_store_value=sv,source_store_bytes=sn)]
  headers.append(dict(root=root['entry'],object=address,write_pc=pc,value=value,branch_BEFORE_cpu=list(cpu),source_stack_byte_provenance=reads))
 return headers
