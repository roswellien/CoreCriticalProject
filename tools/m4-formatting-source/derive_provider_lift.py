"""Reuse literal COFF lowering, adding normal indirect continuation entries."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    base=R/'tools/m4-formatting-frontier/lift.py';s=base.read_text()
    def one(a,b):
        nonlocal s
        assert s.count(a)==1,a;s=s.replace(a,b)
    one("REC=ROOT/'reports/m4-formatting-frontier/recovery-r1'","REC=ROOT/'reports/m4-formatting-source/provider-recovery-r2'")
    one("REC_SHA='8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15'","REC_SHA='2aa9a712983ab98a08c3f59adf8e29b24c17f1f8c0d41ebb786a55c7241a13b9'")
    one("out=ROOT/'reports/m4-formatting-frontier'/name","out=ROOT/'reports/m4-formatting-source'/name")
    a="pin(REC/'report.json',REC_SHA);graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());strrchr=json.loads(pin(REC/'strrchr-graph.json').read_bytes());graphs[str(strrchr['entry'])]=strrchr;need(len(graphs)==11,'Ten game plus one closed strrchr source graph');roots=json.loads(pin(REC/'roots.json').read_bytes());inputs={} "
    b="""pin(REC/'report.json',REC_SHA);rows=json.loads(pin(REC/'instruction-contracts.json').read_bytes())['instructions'];graphs={};entries=(0x780264a9,0x78022b9a,0x7800fc9b,0x7800fd04,0x7800fe69,0x7801041a,0x7801044f,0x78010480,0x780104b8)
  for entry in entries:
   selected_rows=[r for r in rows if (0x7800fc9b<=r['pc']<0x7801041a if entry in(0x7800fc9b,0x7800fd04,0x7800fe69)else (entry<=r['pc']<(0x780264cc if entry==0x780264a9 else 0x78022beb if entry==0x78022b9a else 0x7801044f if entry==0x7801041a else 0x78010480 if entry==0x7801044f else 0x780104b8 if entry==0x78010480 else 0x780104c5)))]
   graphs[str(entry)]=dict(entry=entry,instructions=[dict(pc=r['pc'],size=r['width'],bytes=r['bytes_hex'],mnemonic=r['mnemonic'],operands=r['operands'])for r in selected_rows],unresolved_controls=[],FS_sites=[],FP_sites=[],research_terminal=False)
  roots=[];inputs={}"""
    one(a,b)
    one("entry=g['entry'];component=f'f_{entry:x}';commands=[];source_pe=crt if entry>=0x78000000 else pe","entry=g['entry'];component=f'f_{entry:x}';commands=[];source_pe=crt if entry>=0x78000000 else pe;codebase=min(x['pc']for x in g['instructions'])")
    one("code=bytearray(b'\\xcc'*(end-entry))","code=bytearray(b'\\xcc'*(end-codebase))")
    one("if row['pc']<entry:continue # Separately literal lower tail body.","need(row['pc']>=codebase,'Exact physical lower continuation bytes retained')")
    one("code[a-entry:a-entry+len(raw)]=raw","code[a-codebase:a-codebase+len(raw)]=raw")
    one("'--address='+str(entry)","'--address='+str(codebase)")
    one("scope='Exact formatting game and strrchr source/COFF preparation only; sprintf and runtime remain open'","scope='Literal narrow formatter seven helpers plus two exact indirect continuations; dormant physical branches unadmitted'")
    one("root_count=3","root_count=0")
    one("ROOT/'tools/m4-formatting-frontier/derive_lift.py'","ROOT/'tools/m4-formatting-frontier/derive_lift.py',ROOT/'tools/m4-formatting-source/derive_provider_lift.py'")
    p=base.with_name('lift.py') if False else R/'tools/m4-formatting-source/lift_provider.py';assert not p.exists();p.write_text(s)
    print(json.dumps(dict(passed=True,source=str(p),sha256=sha(p))))
if __name__=='__main__':main()
