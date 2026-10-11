"""Ordinary-file-only physical source review of borrowed widget registry growth.

No game worker, controller, archive reader or capture is opened by this tool.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE=R/'reports/m4-fps-native/service-preparation-r2'
PROVIDER=R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
OBJDUMP=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
SPANS=[(0x78004a36,69,'7ebcaeac92f9b00df418338e72b49b5dc534a6dc3f451364d8cc5cc9e179376b'),(0x7801e27b,69,'ae634431a3fbdf6309e26410d89cc9339599582872dceac4c856d8bbb9594cf6'),(0x78011c0a,72,'d04396eb188d0c05c54dff14900c80fea1c0e6c9e07e76b058c3b21fc27d8819')]
PINS={}
def raw(p):
 p=Path(p);b=p.read_bytes();PINS[str(p.resolve())]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def need(v,m):
 if not v:raise ValueError(m)
def main(out):
 out=Path(out).resolve();need(not out.exists(),'Immutable additive output');out.mkdir(parents=True)
 b=raw(PROVIDER);need(hashlib.sha256(b).hexdigest()=='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7','Exact source provider')
 pe=struct.unpack_from('<I',b,0x3c)[0];opt=pe+24;sections=struct.unpack_from('<H',b,pe+6)[0];optsize=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,opt+28)[0]
 need(b[pe:pe+4]==b'PE\0\0' and base==0x78000000 and struct.unpack_from('<H',b,pe+4)[0]==0x14c,'Physical provider PE32 owner')
 def slice(a,n):
  r=a-base;matches=[]
  for i in range(sections):
   q=opt+optsize+i*40;va,rs,rp=struct.unpack_from('<III',b,q+12)
   if va<=r and r+n<=va+rs:matches.append((rp+r-va,struct.unpack_from('<I',b,q+36)[0]))
  need(len(matches)==1,'Unique complete physical source span');p,flags=matches[0];need(flags&0x60000000==0x60000000 and p+n<=len(b),'Complete raw readable executable span');return b[p:p+n]
 contract=raw(BASE/'registry_contract.inc').decode();instructions={}
 for line in contract.splitlines():
  m=re.match(r'\{(\d+),(\d+),"([^"]+)",',line)
  if m:instructions[int(m[1])]=(int(m[2]),m[3])
 raw(BASE/'registry_api.inc');raw(BASE/'session_impl.inc');raw(BASE/'locale_batch_operations.inc');raw(BASE/'locale_batch.hpp');raw(OBJDUMP)
 relationships=[];count=0
 for a,n,wanted in SPANS:
  source=slice(a,n);need(hashlib.sha256(source).hexdigest()==wanted,'Frozen contract physical whole span hash')
  p=subprocess.run([str(OBJDUMP),'-d',f'--start-address=0x{a:x}',f'--stop-address=0x{a+n:x}',str(PROVIDER)],capture_output=True,text=True,check=True)
  rows=[]
  for line in p.stdout.splitlines():
   m=re.match(r'^([0-9a-f]{8}):\s+((?:[0-9a-f]{2}\s+)+)(\S+)\s*(.*)$',line)
   if not m:continue
   pc=int(m[1],16);bb=bytes.fromhex(m[2]);mnemonic=m[3];canonical=mnemonic[:-1] if mnemonic in ['pushl','popl','movl','subl','addl','cmpl','calll','retl','xorl','testl','sarl','leal','andl','jmpl'] else mnemonic
   need(instructions.get(pc)==(len(bb),canonical),'Physical whole instruction/contract relation')
   need(bb==slice(pc,len(bb)),'Physical disassembly complete instruction bytes')
   rows.append({'pc':pc,'bytes':bb.hex(),'mnemonic':canonical,'operands':m[4]});count+=1
  need(rows and rows[0]['pc']==a and rows[-1]['pc']+len(bytes.fromhex(rows[-1]['bytes']))==a+n,'Physical complete source decode coverage')
  relationships.append({'address':a,'bytes':n,'sha256':wanted,'instructions':rows})
 detail=out/'physical-source.json';detail.write_text(json.dumps(relationships,indent=2)+'\n');raw(detail);raw(__file__);raw(sys.executable)
 report={'passed':True,'scope':'Independent physical source and frozen private allocation/growth guard review; no native/source output equivalence claimed','archive_reader_opened':False,'game_worker_executed':False,'capture_opened':False,'initializer_credit':0,'whole_physical_spans':len(SPANS),'whole_physical_instructions':count,'preconditions':['Same source State/Runtime owner and exact committed source CALL/import/FS chain','Live private Allocation object: native/mapped/not pending, retained native acquired identity/generation/request/extent and complete preextent bytes','DWORD-aligned cursor offset 0 <= used <= extent; append need not already fit before literal msize'],'source_relations':['First literal msize at 78004A42 measures actual capacity and selects growth iff measured capacity < used+4','Growth second literal msize at 7801E27C supplies source_request=second capacity+16; actual mode1 realloc rounds (request+15)&~15','Growth successful literal publish begins at7801E2AA and next=newbegin+used at7801E2B5; callback store78004A67 and next+=4 at78004A69','No post-realloc msize exists before successful onexit return'],'postconditions':['Same private Allocation object selected by newly source-published begin; current live owner, acquired==native, not pending, no retained retired alias, unchanged allocation kind/lifetime','Exact logical count oldcount+1, callback at newbegin+used, next=newbegin+used+4, callback returned in EAX and real committed frame consumed','Non-growth: no growth witness; same alias/acquired/generation/request; complete final measured capacity derived from actual HeapSize output with exactly callback DWORD replacement','Growth: exactly one complete successful witness joining old/new allocation identities, source request/rounding and actual HeapReAlloc output; final extent=rounded/capacity=0, generation joins witness and is greater than old generation','Growth full final extent equals actual retained ReAlloc initial/output bytes with exactly callback DWORD replacement; whole old measured capacity preserved in actual ReAlloc input/output','Moved native pointer maps new alias from prior allocation_cursor and unmaps old alias; in-place retains guest alias/mapped extent; both successful branches advance generation','Null native ReAlloc keeps old live owner/bytes but source returns zero; success postcondition rejects without fabricating publication'],'critical_pitfalls':['Global generation can advance through unrelated allocations; new generation is not generically oldgeneration+1','Second HeapSize result is the direct source of growth request and witness oldcapacity; verify first and second actual API measurements separately','Pre-call capacity may be zero immediately following earlier growth; extent is the valid mapped native ownership bound','Only checking preextent bytes misses any newly measured capacity tail; join whole final extent to real native output','Native pointer motion and guest alias motion are coupled by actual provider bridge, with same Allocation object retained'],'files':PINS}
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True,'whole_physical_instructions':count,'reader_opened':False}))
if __name__=='__main__':main(sys.argv[1])
