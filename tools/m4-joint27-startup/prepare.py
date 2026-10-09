"""Read-only finite joint27 prerequisite/order/carry inventory, no execution."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True);pins={};copies=[]
def bind(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or h==actual,(str(p),h,actual);pins[str(p)]=actual;return actual
def literal(p):
 p=Path(p).resolve();q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(p);bind(q,h);copies.append(dict(original_path=str(p),preserved_path=str(q),sha256=h))
for rel,h in (
 ('reports/m4-mixed-startup/independent-review-r1/report.json','3c4f6b2903efeca37f08b2119b1dc87d374a39cc2284079ccc26abfd30db9f96'),
 ('reports/m4-fp-numeric-max-carry/author-canonical-review-r1/report.json','624cedf34d980780016afac8de7234e9d3aa8cd29269c82f644caff276506ae7'),
 ('reports/m4-fp-numeric-max-carry/author-canonical-worker-addendum-r1/report.json','888cd95632b22ac2fd6d119b8c4e29e6234cefe39ac42c3ec462ab6b46a5d30d'),
 ('reports/m4-fp-numeric-max-carry/independent-canonical-closure-r1/report.json','4bba2d6167d14e371153b78ed12261209951fb0271e494f1601362ada6214395')):
 bind(ROOT/rel,h);bind((ROOT/rel).with_name('pins.json'))
build=ROOT/'reports/m4-mixed-startup/native-r3';d=json.loads((build/'build.json').read_text());assert d['passed'];bind(build/'build.json');gen=Path(d['generation']);bind(gen,d['generation_sha256']);g=json.loads(gen.read_text())
for p,h in g['generated_sources'].items():bind(p,h);literal(p)
for p in (ROOT/'tools/m4-mixed-startup/native_main.cpp',ROOT/'tools/m4-mixed-startup/native_protocol.hpp',ROOT/'tools/m4-mixed-startup/CMakeLists.txt',ROOT/'tools/m4-mixed-startup/build_native.py',ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp',ROOT/'tools/m4-runtime/runtime.hpp',ROOT/'tools/m4-runtime/runtime.cpp'):
 literal(p)
for p in (ROOT/'reports/m4-fp-numeric-max-integration/preparation-r4').glob('*-runtime.ll'):literal(p)
entries=(0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c78f0,0x4c7940,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0)
cw=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f);swpos=(2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743);swbits=(0,1,2,3,4,5,6,8,9,10,14)
u16=lambda b,o:struct.unpack_from('<H',b,o)[0];u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');image=game.read_bytes();nt=u32(image,0x3c);opt=nt+24;ib=u32(image,opt+28)
assert image[:2]==b'MZ' and image[nt:nt+4]==b'PE\0\0' and u16(image,nt+4)==0x14c and u16(image,opt)==0x10b
def fileoff(a):
 r=a-ib;found=[]
 for i in range(u16(image,nt+6)):
  p=opt+u16(image,nt+20)+40*i;vs,va,rs,rp=struct.unpack_from('<4I',image,p+8)
  if va<=r<va+rs:found.append(rp+r-va)
 assert len(found)==1;return found[0]
table=[(0x5e0000+4*i,u32(image,fileoff(0x5e0000+4*i))) for i in range(145)];selected=[(slot,target) for slot,target in table if target in set(entries)|{0x4c19f0}]
assert len(selected)==27 and tuple(x[1]for x in selected if x[1]!=0x4c19f0)==entries
assert selected[17][1]==0x4b7020 and selected[18]==(0x5e016c,0x4c19f0) and selected[19][1]==0x4c78f0
counts=Counter();rows=[]
for level in ('O0','O2'):
 p=build/f'native-{level}.bin';bind(p,d['artifacts'][str(p)]);f=p.open('rb');raw=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
 assert raw[:8]==b'MW4MXN01' and struct.unpack_from('<6I',raw,8)==(1,48,26,1248,11,103468) and len(raw)==32+1248*103468
 for seq in range(48):
  n=raw[32+(seq*26+17)*103468:32+(seq*26+18)*103468];following=raw[32+(seq*26+18)*103468:32+(seq*26+19)*103468]
  assert u32(n,16)==0x4b7020 and u32(following,16)==0x4c78f0 and u32(n,0)==seq
  s=n[95892:99396];before=following[92388:95892];sw=u16(s,2770)&0xb880
  for offset,bit in zip(swpos,swbits):assert s[offset]<=1;sw|=s[offset]<<bit
  top=(sw>>11)&7;sticky=sw&~0x3800;assert top in (0,7) and sticky in (0,2,32,34,512,514,544,546) and s[2772]==0 and u16(s,2768)in cw and u32(s,2792)==0x1f80
  carry=bytearray(s);struct.pack_into('<I',carry,2312,0x20001800);struct.pack_into('<I',carry,2472,0x4c78f0);assert bytes(carry)==before,('hidden State carry differs',level,seq)
  assert n[47332:92388]==following[2276:47332],('whole11page carry differs',level,seq)
  counts[(level,sticky)]+=1;rows.append(dict(level=level,sequence=seq,predecessor=0x4b7020,next_existing_root=0x4c78f0,new_root=0x4c19f0,new_table_slot=0x5e016c,cw=u16(s,2768),top=top,depth=0,incoming_status=sw,sticky=sticky,C1=(sw>>9)&1,whole3504_State_sha256=hashlib.sha256(s).hexdigest(),all11carried_pages_sha256=hashlib.sha256(n[47332:92388]).hexdigest(),projection='Existing next-root BEFORE changes only EIP and pushed-frame ESP; all other State and eleven pages exact persistent carry'))
 raw.close();f.close()
literal(Path(__file__).resolve())
report=dict(passed=True,scope='Preparation only: no compile/execution/27-root acceptance',sources=copies,selected_actual_table_order=[dict(slot=s,target=t)for s,t in selected],actual26_predecessor_inputs=rows,carry_status_counts=[dict(level=l,sticky=s,count=c)for(l,s),c in sorted(counts.items())],
 planned_recipe=dict(runtime='Exact frozen r9 freshly compiled, stable single Runtime and canonical Session owner per sequence',registration='Register inherited26 callbacks and numeric root/body plus named MSVCP50 service before one registry freeze; 28 translations/one extra import service,27 selected table roots',provider='Exact admitted MSVCP50 SHA; owned RX780C1000/RO78115000; real raw game IAT5BB4FC, no MSVCRT identity substitution or DLL initializer',numeric='Reuse canonical source-guard/numerical outer invoke API; complete checked compiled root/body/provider objects, typed CALL/RET with real4C1A09 ST0 checkpoint',carry='Seed coherent State once per48 complete sequences; invoke in actual table order; no FP/hiddenState/page reseed around inserted initializer',observer='New common raw format preserves whole3504State and current CPU/FX/legacyENV and expanded14pages, direct numerical host captures before cleanup,22 PC-bearing numeric events/three nested routes; old26 event routes remain exact',faults='Actual registered root/source/frame/provider/IAT/ownership/wholeState-canonical fault and poisoned retry controls before any acceptance'),
 blockers=['Independent candidate/root acceptance must finish before any joint27 execution','New numeric boundary needs same stable owner and guest State storage; derivative may add observational hook at admitted root entry to capture actual BEFORE after real Runtime CALL, without guest computation change','Fresh full record schema and independent predictive joint model/causal controls must be agreed before capture'],
 inherited_condition_scope='FLD C1=0 defined in no-overflow domain; final FSTP condition/dead storage observations distinct. Current hardware relation is authored local unit, not new actual guest original connected27 execution',ordinary_game_launch=False,original_executed=False,whole_M4_complete=False)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),sources=len(copies),predecessor_records=len(rows),statuses=report['carry_status_counts'])))
