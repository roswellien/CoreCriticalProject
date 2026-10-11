from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=(ROOT/'tools/m4-fs-source/derive_geometry.py').read_text().replace("BASE=ROOT/'reports/m4-fs-source'","BASE=ROOT/'reports/m4-container-source'").replace("ROOT/'tools/m4-fs-source/game_model.py'","ROOT/'tools/m4-container-source/game_model.py'").replace('17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b','b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b')
s=s.replace('memory[0x5f498000]=rawpage(mfc,0x5f498000)','memory[0x5f498000]=rawpage(mfc,0x5f498000);memory[0x5f4cc000]=rawpage(mfc,0x5f4cc000)')
s=s.replace("need(target==0x780012b3 and machine.PCs[-1]==0x5f401eb5,'Exact normal MFC malloc frontier')","site=machine.PCs[-1];need(target==0x780012b3 and site in(0x5f401eb5,0x78010a7e),'Exact source MFC/string malloc frontier')")
s=s.replace("need(frame[0]==0x5abd26 and frame[3] in program,'Literal owning game allocator CALL')","need(frame[0]==(0x5abd26 if site==0x5f401eb5 else 0x78010a6d)and frame[3]in program,'Literal owning allocator/strdup CALL')")
s=s.replace("extent<=512","extent<=1024").replace("source_entry_ECX=machine.reg('ecx')","source_entry_ECX=machine.reg('ecx'),role='vector'if site==0x5f401eb5 else'string'")
s=s.replace("machine.api_return(0x5f401eb5,0,pointer)","machine.api_return(site,0,pointer)").replace("need(writes and all(","need(all(")
s=s.replace("shared=int.from_bytes(model.bytes(0x60b888,4),'little')","shared=int.from_bytes(model.bytes(0x60b888,4),'little')")
start=s.index("  need(len(allocations)==10");end=s.index("  for filename,data",start)
s=s[:start]+"  need(len(allocations)==8 and len(observations)==7,'Eight source-derived positive allocations across seven persistent container/string roots')\n  need([r['new_allocation_count']for r in observations]==[1,1,1,1,2,1,1],'Exact successful three-string/five-vector source allocation distribution')\n"+s[end:]
p=ROOT/'tools/m4-container-source/derive_geometry.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
