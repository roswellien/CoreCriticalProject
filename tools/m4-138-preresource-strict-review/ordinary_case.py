"""Bounded ordinary outputs only; no transport/capture reader or worker."""
from pathlib import Path
import hashlib,struct

def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s)

class DirectoryCase:
 def __init__(self,folder,pin):
  self.folder=Path(folder).resolve();self.pin=pin;self.entries={}
  total=0
  for p in self.folder.rglob('*'):
   if not p.is_file():continue
   need(not p.is_symlink() and p.resolve().is_relative_to(self.folder),'Ordinary bounded owned output')
   need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No transport/archive input')
   n=p.stat().st_size;need(n<=32*1024*1024,'Bounded individual output');total+=n
   self.entries[p.relative_to(self.folder).as_posix()]=p
   need(len(self.entries)<=100000 and total<=512*1024*1024,'Bounded current single-case output')
  need(self.entries and 'COMPLETE.txt'in self.entries and 'FAILED.txt'not in self.entries,'Actual complete single case')
 def data(self,k):return self.pin(self.entries[k]).read_bytes()
 def words(self,k,n,t='I'):return struct.unpack('<'+t*n,self.data(k))
 def close(self):pass

def retry_scope(a,b,c,required=()):
 left={k[len(b):]for k in a.entries if k.startswith(b)};right={k[len(c):]for k in a.entries if k.startswith(c)}
 eq(left,right,'Complete exact retry name inventory');need(left,'Nonempty complete retry domain')
 need(set(required)<=left,'Required whole retry fields present')
 for k in sorted(left):eq(a.data(b+k),a.data(c+k),'Whole unchanged same poisoned Context '+k)
 return len(left)

def hardware(raw):
 eq(len(raw),1632,'Whole actual hardware512/28 observations')
 eq(raw[:512],raw[1088:1600],'Whole caller FX512 restored');eq(raw[512:540],raw[1600:1628],'Whole caller ENV28 restored')

def frame64(raw,cpu,page):
 eq(len(raw),64,'Real complete current root entry frame64');eq(len(cpu),40,'Whole current entry CPU')
 w=struct.unpack('<10I',cpu);eq((w[4],w[9]),(0x20001800,0x5ae3e4),'Actual committed MFC root CALL frame')
 eq(len(page),4096,'Whole actual entry stack page');eq(raw,page[0x800:0x840],'All64 actual entry stack bytes')
 eq(struct.unpack_from('<I',raw)[0],0x410a80,'Actual captured root saved return')

def strict_case(a,mode,native_size=159716):
 stem=f'control-{mode}/';eq(a.words('control-header.bin',6),(2,12,14,17,native_size,mode),'Exact current single-mode header')
 t=a.words(stem+'terminal-facts.bin',13);eq(t[:7],(1,mode,0,1,1,13,13),'Exactly13 completed roots and poisoned failed Context')
 need(t[7]in(0,1)and t[8]==13,'Exact phase13 refusal and Boolean component extent')
 eq({k for k in a.entries if k.startswith(stem+'phase-')},{stem+f'phase-{i}.bin'for i in range(13)},'Exact completed root inventory without refused root output')
 roots=(0x40ffe0,0x410030,0x410080,0x4100d0,0x410120,0x410170,0x4101c0,0x410210,0x410260,0x4102b0,0x410300,0x410350,0x4103a0)
 for phase,root in enumerate(roots):
  raw=a.data(stem+f'phase-{phase}.bin');eq(len(raw),native_size,'Whole completed Native record')
  w=struct.unpack_from('<9I',raw);eq((w[0],w[1],w[2],w[4],w[5],w[6],w[7]),(0,0,phase,root,0x7f,0,0),'Exact current completed prefix root chronology')
 counts={}
 counts['runtime_private_public_retry_fields']=retry_scope(a,stem+'retry-before/',stem+'retry-after/',('State.bin','CPU.bin','FX.bin','memory-index.bin','Context-status.bin','Context-reason.txt','Runtime-calls.bin','Registry/registry-summary.bin'))
 for f,n in(('State.bin',3504),('CPU.bin',40),('FX.bin',512),('Context-status.bin',32)):eq(len(a.data(stem+'retry-before/'+f)),n,'Whole current retry '+f)
 counts['whole_registry_retry_fields']=retry_scope(a,stem+'retry-before/Registry/',stem+'retry-after/Registry/',('registry-summary.bin','registry-research-projections.bin','heap-source-accesses.bin','heap-api-accesses.bin','heap-events.bin'))
 counts['whole_widget_retry_fields']=retry_scope(a,stem+'Widget/pre-resource-retry-before/',stem+'Widget/pre-resource-retry-after/',('State.bin','CPU.bin','FX.bin','status.bin','accesses.bin','APIs.bin','fonts.bin','TIB.bin','stack.bin'))
 for k in('accesses.bin','APIs.bin','fonts.bin','frames.bin','FS-frames.bin','FS-events.bin','virtuals.bin','arrays.bin','imports.bin'):eq(a.data(stem+'Widget/pre-resource-retry-before/'+k),b'','No widget source/resource invocation before phase13')
 cleaned=a.words(stem+'Widget/cleaned/status.bin',12,'Q');eq(cleaned[1:3],(0,0),'No selected widget root');eq(cleaned[4:7],(0,1,1),'Actual widget fault and cleanup')
 eq(a.data(stem+'Widget/cleaned/fonts.bin'),b'','No owned or live font generation')
 r=a.words(stem+'cleaned/Registry/registry-summary.bin',32,'Q');eq((r[2],r[4],r[10],r[11],r[15]),(0,1,0,0,0),'Actual whole registry owner/heap/CS cleanup')
 hardware(a.data(stem+'caller-hardware.bin'));hardware(a.data(stem+'retry-hardware.bin'));hardware(a.data(stem+'Widget/font-cleanup-caller-hardware.bin'))
 p=stem+'MFC/entry/';own=a.data(p+'Native.bin');eq(len(own),native_size,'Whole actual refused root own entry Native')
 eq(own[36:76],a.data(p+'CPU.bin'),'Entry CPU equals own BEFORE snapshot')
 frame64(a.data(p+'entry-frame64.bin'),a.data(p+'CPU.bin'),own[2276+10*4096:2276+11*4096])
 if t[7]:
  counts['whole_MFC_retry_fields']=retry_scope(a,stem+'MFC/retry-before/',stem+'MFC/retry-after/',('State.bin','CPU.bin','FX.bin','accesses.bin','APIs.bin','resource-context.bin','nativeCS40.bin','native-thread-mirror.bin','guestCS24.bin'))
  api=a.data(stem+'MFC/refused/APIs.bin');eq(len(api),352 if mode in(7,8)else 0,'Exact accepted finite0/1 completed source API domain')
 else:
  need(not any(k.startswith(stem+'MFC/resources/')for k in a.entries),'Constructor refusal precedes owned native service initialization')
 counts['entryframe64_checked']=1;return counts
