"""Finite current141 widget ENV last-writer evidence probe (phases 137..140).

Hypothesis: the x87 instruction/data pointer metadata (FIP/FCS/FOP/FDP/FDS) at
phase137 BEFORE belongs to `fstp dword [0x60B494]` at 4CE618 (phase101 root
4CE600), and no later source instruction through phase140 updates it; the
original-only clear inside CreateFontA is an opaque API effect.

Evidence gathered (ordinary inputs; llvm-objdump 21.1.8 linear decode):
1. Phase137 BEFORE ENV on all 16 probe endpoints decodes exactly to that fstp
   (FOP from the actual instruction bytes).
2. Phases137..139 (all six sequences): every actually executed original widget
   source PC (widget r7 derivations) decodes as an instruction start in the
   admitted Mech3.exe / staged MSVCRT; none is a metadata-updating x87 op.
3. Phase140 root 5A7DC0: static over-approximation of directly reachable code
   in Mech3.exe and the MFC42 operator new/delete ordinals it imports; MSVCRT
   instruction contracts checked whole. Remaining indirect transfers are listed;
   while any stays unresolved, phase140 is reported OPEN, never inferred.
No ENV policy admission, paired gate or credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
OBJ=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf';MSVCRT_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
PREFIX={0x66,0x67,0xf2,0xf3,0x2e,0x36,0x3e,0x26,0x64,0x65}
CONTROL={'fldcw','fnstcw','fstcw','fnstsw','fstsw','fnclex','fclex','fninit','finit','fnstenv','fstenv','fldenv','fnsave','fsave','frstor','fwait','wait','fnop','ffree','fdecstp','fincstp'}
CONTROL|={m+'l'for m in list(CONTROL)}|{m+'s'for m in list(CONTROL)}
FSTP_PC=0x4ce618
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def disasm(image,a,b):
 out=subprocess.run([str(OBJ),'-d',f'--start-address={hex(a)}',f'--stop-address={hex(b)}',str(image)],capture_output=True,text=True);assert out.returncode==0,out.stderr
 rows={}
 for line in out.stdout.splitlines():
  m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} ?)+?)\s*\t(\S+)\s*(.*)',line)
  if m:rows[int(m[1],16)]=(bytes.fromhex(m[2].replace(' ','')),m[3],m[4].strip())
 return rows
def is_x87(raw):
 op=[b for b in raw if b not in PREFIX];return bool(op)and 0xd8<=op[0]<=0xdf
def updating(raw,mn):return is_x87(raw)and mn not in CONTROL
def walk(image,start,lo,hi):
 seen={};todo=[start];indirect=[];outside=[]
 while todo:
  a=todo.pop()
  if a in seen:continue
  if not lo<=a<hi:outside.append(a);continue
  for pc,(raw,mn,ops)in sorted(disasm(image,a,a+0x400).items()):
   if pc in seen:break
   seen[pc]=(raw,mn,ops);t=re.match(r'(0x[0-9a-f]+)',ops)
   if mn.startswith('j')or mn.startswith('call'):
    if t and '*'not in ops:todo.append(int(t[1],16))
    else:indirect.append(dict(pc=pc,mnemonic=mn,operand=ops))
   if mn.startswith('ret')or mn in('jmp','jmpl'):break
 return seen,indirect,outside
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);pin(OBJ);game=pin(R/'MW3/Mech3.exe',GAME_SHA);msvcrt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',MSVCRT_SHA);mfc=pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL')
 PE=load('pe',R/'tools/analysis/pe.py');F=load('scanner',R/'tools/m4-startup141-paired/footprint141_v2.py');J=load('stream',R/'tools/m4-138-controls-review/full_raw_review_v2.py')
 # 1. Phase137 BEFORE metadata decodes to the phase101 fstp.
 P=json.loads(pin(R/'reports/m4-startup141-paired/widget-ENV-ordinary-probe-r1/report.json','979782111ec93d66f4067b7fa28671470288384c7364a3da88eafa23398d3b0c').read_bytes())
 fstp=disasm(game,FSTP_PC,FSTP_PC+8)[FSTP_PC];assert fstp[0][:2]==b'\xd9\x1d'and fstp[1].startswith('fstp');operand=struct.unpack_from('<I',fstp[0],2)[0];fop=((fstp[0][0]&7)<<8)|fstp[0][1]
 meta=set()
 for r in P['relations']:
  if r['phase']==137 and r['side']=='before':
   for k in('original_ENV_hex','native_ENV_hex'):
    e=bytes.fromhex(r[k]);fip,fcs,fop_,fdp,fds=struct.unpack_from('<IHHIH',e,12);meta.add((fip,fop_,fdp))
 assert meta=={(FSTP_PC,fop,operand)},('Phase137 BEFORE metadata is the 4CE618 fstp',meta)
 # 2. Executed widget PCs for phases 137..139.
 W=json.loads(pin(R/'reports/m4-original141-source/source-r7-widgets/report.json').read_bytes());wpath=R/'reports/m4-original141-source/source-r7-widgets/source-derivations.json';pin(wpath,W['files'][str(wpath.resolve())])
 pcs=collections.defaultdict(set)
 for c in F.stream_cases(wpath,J):
  if c.get('phase')in(137,138,139):pcs[c['phase']]|=set(c['source_PCs'])
 assert set(pcs)=={137,138,139}
 decoded={}
 def clusters(v):
  v=sorted(v);res=[[v[0],v[0]]]
  for p in v[1:]:
   if p-res[-1][1]<=48:res[-1][1]=p
   else:res.append([p,p])
  return res
 allpcs=set().union(*pcs.values())
 for image,sel in((game,lambda p:p<0x70000000),(msvcrt,lambda p:p>=0x78000000)):
  chosen=[p for p in allpcs if sel(p)]
  for a,b in clusters(chosen)if chosen else[]:decoded.update(disasm(image,a,b+16))
 resync=0
 for p in sorted(p for p in allpcs if p not in decoded):
  # Linear cluster decode can desynchronize after embedded data/padding; an
  # executed PC is a genuine instruction start, so decode from it directly.
  one=disasm(game if p<0x70000000 else msvcrt,p,p+16)
  if p in one:decoded[p]=one[p];resync+=1
 missing=sorted(p for p in allpcs if p not in decoded);assert not missing,('Every executed PC decodes as an instruction start',[hex(p)for p in missing[:20]])
 executed_x87={ph:[dict(pc=p,mnemonic=decoded[p][1],operand=decoded[p][2])for p in sorted(v)if is_x87(decoded[p][0])]for ph,v in pcs.items()}
 executed_updating={ph:[x for x in xs if x['mnemonic']not in CONTROL]for ph,xs in executed_x87.items()}
 # 3. Phase140 root static over-approximation.
 seen,ind,outside=walk(game,0x5a7dc0,0x401000,0x5b0000);assert not outside
 gim=PE.PEImage(game.read_bytes());slots={gim.image_base+s['iat_rva']:(lib['library'],s.get('name')or'#'+str(s.get('ordinal')))for lib in gim.imports()for s in lib['symbols']}
 mim=PE.PEImage(mfc.read_bytes());mexp={e['ordinal']:mim.image_base+e['rva']for e in mim.exports()};mslots={mim.image_base+s['iat_rva']:(lib['library'],s.get('name')or'#'+str(s.get('ordinal')))for lib in mim.imports()for s in lib['symbols']}
 contracts=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d').read_bytes())['instructions']
 contract_x87=[r for r in contracts if is_x87(bytes.fromhex(r['bytes_hex']))]
 static_x87=[dict(pc=p,mnemonic=v[1])for p,v in seen.items()if is_x87(v[0])];unresolved=[];resolved=[];mfc_walks={}
 for i in ind:
  m=re.fullmatch(r'\*(0x[0-9a-f]+)',i['operand'])
  if not m:unresolved.append(dict(module='Mech3',**i));continue
  lib,sym=slots[int(m[1],16)]
  if lib.upper()=='MSVCRT.DLL':resolved.append(dict(pc=i['pc'],import_=sym,rule='MSVCRT function within the x87-free instruction contract set'));continue
  if lib.upper()=='MFC42.DLL'and sym.startswith('#'):
   start=mexp[int(sym[1:])];s2,i2,o2=walk(mfc,start,0x5f401000,0x5f500000);x2=[dict(pc=p,mnemonic=v[1])for p,v in s2.items()if is_x87(v[0])]
   rest=[]
   for j in i2:
    mm=re.fullmatch(r'\*(0x[0-9a-f]+)',j['operand'])
    if mm and int(mm[1],16)in mslots:
     l2,s_=mslots[int(mm[1],16)]
     if l2.upper()=='MSVCRT.DLL'and s_ in('malloc','free'):continue
     rest.append(dict(module='MFC42',import_=l2+'!'+s_,**j))
    else:rest.append(dict(module='MFC42',**j))
   mfc_walks[sym]=dict(entry=start,reachable=len(s2),x87=x2,unresolved=len(rest),outside=len(o2));unresolved.extend(rest)
   continue
  unresolved.append(dict(module='Mech3',import_=lib+'!'+sym,**i))
 for p_,h in list(pins.items()):assert sha(p_)==h
 closed137_139=all(not v for v in executed_updating.values())
 closed140=not static_x87 and not contract_x87 and all(not w['x87']for w in mfc_walks.values())and not unresolved
 rp=out/'lastwriter.json';rp.write_text(json.dumps(dict(executed_x87=executed_x87,phase140_static=dict(reachable=len(seen),x87=static_x87,resolved=resolved,mfc_walks=mfc_walks,unresolved=unresolved)),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='ENV last-writer evidence for phases137..140: phase137 BEFORE metadata = 4CE618 fstp; executed widget source PCs 137..139 decoded; phase140 static over-approximation with unresolved transfers listed. Evidence probe only, no ENV policy admission or credit',
  phase137_metadata_is_fstp_4CE618=True,fstp_operand=operand,fstp_FOP=fop,executed_unique_PCs={str(k):len(v)for k,v in sorted(pcs.items())},resynchronized_PC_decodes=resync,executed_metadata_updating_x87={str(k):len(v)for k,v in executed_updating.items()},phases137_139_closed=closed137_139,
  phase140_static_reachable=len(seen),phase140_static_x87=len(static_x87),MSVCRT_contract_x87=len(contract_x87),MFC_ordinal_walks={k:dict(reachable=v['reachable'],x87=len(v['x87']),unresolved=v['unresolved'])for k,v in mfc_walks.items()},phase140_unresolved_transfers=len(unresolved),phase140_closed=closed140,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('phase137_metadata_is_fstp_4CE618','executed_unique_PCs','executed_metadata_updating_x87','phases137_139_closed','phase140_static_reachable','phase140_static_x87','MSVCRT_contract_x87','MFC_ordinal_walks','phase140_unresolved_transfers','phase140_closed')}))
if __name__=='__main__':main(sys.argv[1])
