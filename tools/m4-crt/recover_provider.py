"""Exact original staged CRT exports and game IAT sites, read-only recovery."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
ROOT=Path(__file__).resolve().parents[2]
IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
SELECTED={'_initterm':28,'__set_app_type':10,'__p__fmode':6,'__p__commode':6}
def need(ok,why):
 if not ok:raise ValueError(why)
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
class PE:
 def __init__(self,p,sha):
  self.path=p;self.bytes=p.read_bytes();need(hashlib.sha256(self.bytes).hexdigest()==sha,'Exact PE identity')
  self.pe=self.u32(0x3c);need(self.bytes[:2]==b'MZ' and self.bytes[self.pe:self.pe+4]==b'PE\0\0','PE headers')
  need(self.u16(self.pe+4)==0x14c,'i386');self.opt=self.pe+24;need(self.u16(self.opt)==0x10b,'PE32')
  self.base=self.u32(self.opt+28);self.sections=[]
  for n in range(self.u16(self.pe+6)):
   o=self.opt+self.u16(self.pe+20)+n*40;vs,va,rs,rp=struct.unpack_from('<4I',self.bytes,o+8)
   need(rp+rs<=len(self.bytes),'Section raw bounds');self.sections.append((va,vs,rs,rp,self.u32(o+36)))
 def u16(self,o):return struct.unpack_from('<H',self.bytes,o)[0]
 def u32(self,o):return struct.unpack_from('<I',self.bytes,o)[0]
 def offset(self,rva,count=1):
  for va,vs,rs,rp,flags in self.sections:
   if va<=rva and rva+count<=va+rs:return rp+rva-va
  raise ValueError('File-backed RVA bounds '+hex(rva))
 def read(self,rva,count):o=self.offset(rva,count);return self.bytes[o:o+count]
 def text(self,rva):
  o=self.offset(rva);end=self.bytes.index(0,o,o+4096);return self.bytes[o:end].decode('ascii')
 def exports(self):
  rva,size=struct.unpack_from('<2I',self.bytes,self.opt+96);o=self.offset(rva,40)
  base,nf,nn,functions,names,ordinals=struct.unpack_from('<6I',self.bytes,o+16)
  result={}
  for n in range(nn):
   name=self.text(struct.unpack('<I',self.read(names+4*n,4))[0]);index=struct.unpack('<H',self.read(ordinals+2*n,2))[0]
   need(index<nf,'Export ordinal index bounds');target=struct.unpack('<I',self.read(functions+4*index,4))[0]
   need(not rva<=target<rva+size,'Selected exports must not be forwarders')
   result[name]={'ordinal':base+index,'rva':target,'address':self.base+target}
  return result
 def imports(self):
  directory,size=struct.unpack_from('<2I',self.bytes,self.opt+104);items=[]
  for d in range(size//20):
   fields=struct.unpack('<5I',self.read(directory+d*20,20))
   if not any(fields):break
   original,_,_,name,iat=fields;library=self.text(name);lookup=original or iat
   for n in range(8192):
    value=struct.unpack('<I',self.read(lookup+4*n,4))[0]
    if not value:break
    item={'library':library,'iat':self.base+iat+4*n}
    if value&0x80000000:item['ordinal']=value&0xffff
    else:item['name']=self.text(value+2)
    items.append(item)
  return items
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args();out=Path(args.out).resolve()
 need(out.is_relative_to(ROOT/'reports/m4-crt') and not out.exists(),'Fresh private CRT recovery output')
 provider_path=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';game_path=ROOT/'MW3/Mech3.exe'
 provider=PE(provider_path,PROVIDER_SHA);game=PE(game_path,IMAGE_SHA);exports=provider.exports();imports=game.imports()
 out.mkdir(parents=True);records=[];tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';commands=[]
 for name,length in SELECTED.items():
  e=exports[name];code=provider.read(e['rva'],length);p=out/(name+'.bin');p.write_bytes(code)
  command=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(e['address']),'--stop-address='+hex(e['address']+length),str(provider_path)]
  result=subprocess.run(command,capture_output=True);need(result.returncode==0,'Actual LLVM disassembly failed')
  log=out/(name+'-llvm.txt');log.write_bytes(result.stdout+result.stderr);commands.append({'command':command,'exit_code':0,'log':bind(log)})
  site=[i for i in imports if i.get('name')==name and i['library'].lower()=='msvcrt.dll'];need(len(site)==1,'Exact one actual CRT IAT site')
  records.append({'name':name,**e,'size':length,'original_code':bind(p),'code_hex':code.hex(),'game_import':site[0]})
 init=next(r for r in records if r['name']=='_initterm')
 need(init['address']==0x780014f8 and init['original_code']['sha256']=='960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678','Complete actual _initterm source')
 report={'passed':True,'scope':'Exact original-provider CRT source recovery; no provider/game body execution or native service equivalence',
  'provider':bind(provider_path),'image':bind(game_path),'source':bind(__file__),'tool':bind(tool),'exports':records,'commands':commands,
  'initterm_contract':{'source_begin':0x780014f8,'source_end':0x78001514,'callback_call':0x7800150e,'callback_return':0x78001510,'cdecl_argument_bytes':8,'callee_pop_bytes':0,'preserved_nonvolatile':'ESI saved on guest stack; other nonvolatile registers untouched by provider','flags':'Final unsigned CMP ESI,end defines CF/PF/AF/ZF/SF/OF; caller other flags retained','read_policy':'Read each DWORD slot when reached; literal null skipped; no error return; exceptions propagate into still-unimplemented guest SEH.'},
  'provider_globals':{'app_type':0x78038ee8,'fmode':0x78038eec,'commode':0x78038ef0},
  'all_game_crt_imports':[i for i in imports if i['library'].lower()=='msvcrt.dll'],
  'limits':['Runtime provider selection not observed; explicitly recovered staged source identity only','No DLL load, relocation, imports, DllMain or guest SEH dispatch','Native service ABI still needs comparison/gate','All other reached CRT services remain unresolved; no success substitutes'],
  'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[p for p in out.iterdir() if p.is_file()]+[provider_path,game_path,Path(__file__),tool]
 (out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):bind(p)['sha256'] for p in files}},indent=2)+'\n')
 print('Exact staged CRT source recovered; original code unexecuted')
if __name__=='__main__':main()
