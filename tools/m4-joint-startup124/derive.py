"""Derive124 named schedules from120; binary ABI offsets remain unchanged."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=(ROOT/'tools/m4-joint-startup120/prepare.py').read_text()
s=one(s,'Join four literal roots to the immutable accepted116 connected corpus.','Join four literal Lockit roots to the immutable accepted120 connected corpus.')
s=one(s,"out.parent==ROOT/'reports/m4-joint-startup120'","out.parent==ROOT/'reports/m4-joint-startup124'")
s=one(s,'reports/m4-joint-startup116/preparation-r1','reports/m4-joint-startup120/preparation-r3')
s=one(s,'55c616f42ea7ed9458ed50cf999d31ee8f81df5d1df27419a56d4e3bfdd8aa0e','46e510f76d00722b2f46ef015d946a8ced3e0af0286e5ef8baf06e37797ff810')
s=one(s,'reports/m4-joint-startup116-root/acceptance-r1/report.json','reports/m4-joint-startup120-root/acceptance-r1/report.json')
s=one(s,'de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6','e640ff4eaa068a039a5e810ad99b4c0ca0336821b8b1a6f33f81012ad43ed0ee')
s=one(s,"len(selected)==120 and len(contract['roots'])==4","len(selected)==124 and len(contract['roots'])==4")
s=one(s,"start=protocol.index('constexpr std::array<std::uint32_t,116> entries')","start=protocol.index('constexpr std::array<std::uint32_t,120> entries')")
s=one(s,"protocol[:start]+'constexpr std::array<std::uint32_t,120> entries{'","protocol[:start]+'constexpr std::array<std::uint32_t,124> entries{'")
s=one(s,"len(pages)==23 and set(pages)-set(prior['extra_pages'])=={0x5bc000,0x5cf000,0x5fc000}","len(pages)==26 and set(pages)-set(prior['extra_pages'])=={0x7810a000,0x78145000,0x78146000}")
s=one(s,"set(contract['source_data_pages'])","set(contract['source_data_pages'])|{0x7810a000}")
s=one(s,'len(set(roots))==92','len(set(roots))==96')
s=one(s,'constexpr std::array<unsigned,23> registration_pages','constexpr std::array<unsigned,26> registration_pages')
s=one(s,'constexpr std::array<unsigned,92> registration_roots','constexpr std::array<unsigned,96> registration_roots')
s=one(s,"s=one(s,'phase==116&&r_.calls().size()==119&&r_.translation_count()==117','phase==120&&r_.calls().size()==123&&r_.translation_count()==121')","s=one(s,'phase==120&&r_.calls().size()==123&&r_.translation_count()==121','phase==124&&r_.calls().size()==127&&r_.translation_count()==125');s=one(s,'std::make_unique<m4_onexit::Session>(r_,crt,mfc)','std::make_unique<m4_onexit::Session>(r_,crt,mfc,provider)')")
s=one(s,"[('selected116','selected120'),('Connected116','Connected120'),('connected116','connected120'),('persistent116','persistent120'),('Joint116','Joint120'),('records.reserve(116)','records.reserve(120)'),('records.size()==116','records.size()==120'),('total==696','total==720'),('696native','720native'),('1,6,116,696,17,sizeof(Native)','1,6,120,720,17,sizeof(Native)'),('116-root','120-root')]","[('selected120','selected124'),('Connected120','Connected124'),('connected120','connected124'),('persistent120','persistent124'),('Joint120','Joint124'),('records.reserve(120)','records.reserve(124)'),('records.size()==120','records.size()==124'),('total==720','total==744'),('720native','744native'),('1,6,120,720,17,sizeof(Native)','1,6,124,744,17,sizeof(Native)'),('120-root','124-root')]")
s=s.replace('==336','==351').replace('}-336','}-351').replace('])-336','])-351')
s=one(s,"len(objects['O0'])==len(objects['O2'])==351 and added_counts['O0']==added_counts['O2']==15","len(objects['O0'])==len(objects['O2'])==363 and added_counts['O0']==added_counts['O2']==12")
s=one(s,'Selected literal finite-vtable constructor root','Selected literal Lockit container constructor root')
s=one(s,'Connected120 preparation only; no execution credit','Connected124 preparation only; no execution credit')
p=HERE/'prepare.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
for name in('CMakeLists.txt','build.py','build.ps1','run.py'):
 s=(ROOT/'tools/m4-joint-startup120'/name).read_text().replace('startup120','startup124').replace('Startup120','Startup124').replace('selected120','selected124').replace('connected120','connected124').replace('Connected120','Connected124').replace('changed120','changed124').replace('persistent120','persistent124').replace('120-root','124-root')
 if name=='run.py':
  s=one(s,"len(prep['selected_order'])==120","len(prep['selected_order'])==124");s=one(s,'(1,6,120,720,17,159716)','(1,6,124,744,17,159716)');s=one(s,"words('selected-table.bin',120)","words('selected-table.bin',124)");s=one(s,"words('registration-roots.bin',92)","words('registration-roots.bin',96)");s=one(s,'len(set(entries))==120','len(set(entries))==124');s=one(s,'(1,120,0,0,0,0,0,0)','(1,124,0,0,0,0,0,0)')
 assert not (HERE/name).exists();(HERE/name).write_text(s)
print('Generated124 named schedule/build/run tools with unchanged packed ABI')
