"""Independent literal PE contract for the first actual null-only _initterm call."""
import hashlib,json,pathlib,re,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-initterm'
PINS={}
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
 p=pathlib.Path(p).resolve();h=sha(p);need(want is None or want==h,'Exact independent source binding '+str(p));PINS[str(p)]=h;return p
class PE:
 def __init__(self,path,want):
  self.path=pin(path,want);self.b=self.path.read_bytes();p=self.u32(60);need(self.b[p:p+4]==b'PE\0\0','Actual PE signature');self.opt=p+24;need(self.u16(self.opt)==0x10b,'Exact guest PE32');self.base=self.u32(self.opt+28);n=self.u16(p+6);size=self.u16(p+20)
  self.sections=[struct.unpack_from('<IIII',self.b,self.opt+size+40*i+8) for i in range(n)]
 def u16(self,o):return struct.unpack_from('<H',self.b,o)[0]
 def u32(self,o):return struct.unpack_from('<I',self.b,o)[0]
 def offset(self,rva,n=1):
  ranges=[raw+rva-start for vs,start,count,raw in self.sections if rva>=start and rva+n<=start+count]
  need(len(ranges)==1 and ranges[0]+n<=len(self.b),'Unique file-backed source VA');return ranges[0]
 def source(self,va,n):o=self.offset(va-self.base,n);return self.b[o:o+n]
 def string(self,rva):
  o=self.offset(rva);end=self.b.index(0,o);need(end-o<4096,'Bounded source PE string');return self.b[o:end].decode('ascii')
 def import_owner(self,slot):
  directory=self.u32(self.opt+104);rows=[]
  for i in range(256):
   o=self.offset(directory+20*i,20);original,stamp,forward,name,first=struct.unpack_from('<5I',self.b,o)
   if not any((original,stamp,forward,name,first)):break
   for j in range(4096):
    word=self.u32(self.offset((original or first)+4*j,4))
    if not word:break
    if self.base+first+4*j==slot:
     need(not word&0x80000000,'Named actual _initterm import');rows.append((self.string(name),self.string(word+2),self.u32(self.offset(first+4*j,4))))
  need(len(rows)==1,'Unique exact import owner');return rows[0]
def main(output):
 need(output.parent==BASE and output.name.startswith('independent-compiled-') and not output.exists(),'Fresh independent contract output');output.mkdir(parents=True)
 game=PE(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
 provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 leaf=provider.source(0x780014f8,28);need(hashlib.sha256(leaf).hexdigest()=='960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678','Complete literal 28-byte provider body')
 thunk=game.source(0x5ac598,6);need(thunk==bytes.fromhex('ff2510b55b00'),'Actual tail JMP source names IAT 5BB510')
 caller=game.source(0x5ac436,15);need(caller==bytes.fromhex('684c025e006848025e00e853010000'),'Actual two bounds PUSH and CALL to thunk')
 owner=game.import_owner(0x5bb510);need(owner[:2]==('MSVCRT.dll','_initterm'),'Exact real named import owner')
 first=game.source(0x5e0248,4);need(first==bytes(4),'First literal table interval has one null source DWORD')
 main=struct.unpack('<145I',game.source(0x5e0000,0x244));need(sum(bool(v)for v in main)==144,'Later distinct main interval has 144 nonzero callbacks')
 for name,b in [('provider.bin',leaf),('thunk.bin',thunk),('caller.bin',caller),('first-table.bin',first)]:p=output/name;p.write_bytes(b);pin(p)
 tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe');commands=[]
 for name,path,start,end in [('provider',provider.path,0x780014f8,0x78001514),('caller',game.path,0x5ac436,0x5ac46e),('thunk',game.path,0x5ac598,0x5ac59e)]:
  command=[str(tool),'-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={end}',str(path)];r=subprocess.run(command,capture_output=True,text=True);need(r.returncode==0,'Fresh independent PE source disassembly');p=output/(name+'-decode.txt');p.write_text(r.stdout);pin(p);commands.append({'arguments':command,'exit_code':r.returncode,'log':str(p),'log_sha256':sha(p)})
 pcs=[int(v,16)for v in re.findall(r'^([0-9a-f]+):', (output/'provider-decode.txt').read_text(),re.M)]
 need(pcs==[0x780014f8,0x780014f9,0x780014fd,0x780014ff,0x78001502,0x78001506,0x78001508,0x7800150a,0x7800150c,0x7800150e,0x78001510,0x78001512,0x78001513],'Complete static instruction source includes callback CALL branch')
 pin(__file__)
 report={'passed':True,'scope':'Independent source contract only; no candidate/native acceptance', 'provider_entry':0x780014f8,'provider_source_bytes':28,'complete_static_PCs':pcs,'thunk':0x5ac598,'real_IAT':0x5bb510,'raw_IAT':owner[2],'real_import_owner':owner[0:2],'callsite':0x5ac440,'return_PC':0x5ac445,'actual_first_interval':[0x5e0248,0x5e024c],'actual_first_interval_DWORDs':[0],'first_interval_runs_selected_initializers':False,'later_main_interval':[0x5e0000,0x5e0244],'later_main_nonzero':144,'next_required_callsite':0x5ac468,'next_required_IAT':0x5bb514,'original_executed':False,'ordinary_game_launched':False,'whole_M4_complete':False,'commands':commands,'files':PINS}
 (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if isinstance(v,(bool,int,str))}))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve())
