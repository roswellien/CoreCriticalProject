"""Only measured physical tag bookkeeping and FSTP accumulated DE repair."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
CANON={'4c19f0': '674ce43a0ccf798c26399dd8637e647923c2d9675747fd4c4d112832d341735c', '4c1a00': 'f4194963e65fcb6c07de7641a29287b5478f0f42249926abfa0dc70df595e678', '780c10f0': '05d0ae4078ed7b7548b59960dcedd4893a91bfb20b6d99f5eee6d3b4ffe1c3ff'}
def main():
 source,out,report=map(lambda p:Path(p).resolve(),sys.argv[1:4]);assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists() and not report.exists()
 text=source.read_text();entry=next(x for x in CANON if '@sub_'+x+'(' in text and (x!='4c1a00' or source.name.startswith(x)))
 canonical=hashlib.sha256('\n'.join(text.splitlines()[1:]).encode()).hexdigest();assert canonical==CANON[entry],'Exact honest strict baseline differs'
 changes=[]
 if entry in ('780c10f0','4c1a00'):
  # The unique final TOP update follows the original FLD push/FSTP pop.
  pointer=re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 2770',text);assert len(pointer)==1
  writes=list(re.finditer(r'^  store i16 (%\d+), ptr '+re.escape(pointer[0])+r', align 2$',text,re.M));assert len(writes)==1
  at=writes[0].end();kind='fld' if entry=='780c10f0' else 'fstp'
  text=text[:at]+f'\n  call void @mw34_numeric_{kind}_commit(ptr %state, ptr %memory)'+text[at:]+f'\ndeclare void @mw34_numeric_{kind}_commit(ptr, ptr)\n';changes.append('Typed checked physical tag '+kind+' commit')
 if entry=='4c1a00':
  pointers=set(re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 2753',text));phis=set(re.findall(r'(%\d+) = phi i8',text));changed=0
  for value,pointer in re.findall(r'^  store i8 (%\d+), ptr (%\d+), align 1$',text,re.M):
   if pointer not in pointers or value not in phis:continue
   old=f'  store i8 {value}, ptr {pointer}, align 1';new=f'  %numeric_prior_de = load i8, ptr {pointer}, align 1\n  %numeric_sticky_de = or i8 {value}, %numeric_prior_de\n  store i8 %numeric_sticky_de, ptr {pointer}, align 1';assert text.count(old)==1;text=text.replace(old,new);changed+=1
  assert changed==1;changes.append('Preserve prior State DE through unconditional FSTP classification overwrite')
 out.write_text(text);report.write_text(json.dumps({'entry':entry,'input_sha256':sha(source),'output_sha256':sha(out),'source_sha256':sha(__file__),'canonical_baseline_sha256':canonical,'changes':changes,'numerical_changes':0,'C1_changes':0,'baseline_failure_report':str(ROOT/'reports/m4-fp-numeric-max/baseline-comparison-r1/report.json')},indent=2)+'\n')
 print(json.dumps({'entry':entry,'changes':changes}))
if __name__=='__main__':main()
