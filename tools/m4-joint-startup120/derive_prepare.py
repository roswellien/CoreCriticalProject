"""Derive a fresh120 preparation with exact immutable116 parent identities."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent;ROOT=HERE.parents[1]
s=(ROOT/'tools/m4-joint-startup116/prepare.py').read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one('Join seven literal roots to the immutable accepted109 connected corpus.','Join four literal roots to the immutable accepted116 connected corpus.')
one('def main(nativeprep,digest,source_lifts,lift_digest,contracts,contract_digest,out):','def main(nativeprep,digest,source_lifts,lift_digest,contracts,contract_digest,preflight_path,preflight_sha,ghidra_path,ghidra_sha,out):')
one("out.parent==ROOT/'reports/m4-joint-startup116'","out.parent==ROOT/'reports/m4-joint-startup120'")
one("reports/m4-joint-startup109/preparation-r5","reports/m4-joint-startup116/preparation-r1")
one('6c5f17771b30504c5aec036cc8f578be21a3ce3e6563dd4a429c0e523ec18989','55c616f42ea7ed9458ed50cf999d31ee8f81df5d1df27419a56d4e3bfdd8aa0e')
one('reports/m4-joint-startup109-root/acceptance-r1/report.json','reports/m4-joint-startup116-root/acceptance-r1/report.json')
one('697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6')
one("len(selected)==116 and len(contract['roots'])==7","len(selected)==120 and len(contract['roots'])==4")
one("preflight=ROOT/'reports/m4-container-review/preflight-r1/report.json';bind(preflight,'a102855701639f356308f8f7f39338a7dea6975ce1c55c45aff4fc9eddd96aee')","preflight=Path(preflight_path).resolve();bind(preflight,preflight_sha)")
one("ghidra=ROOT/'reports/m4-container-ghidra/export-r1/report.json';bind(ghidra,'261466c6cf42fb04b2ac9858bdd6c637c8753fffb97ad135b1457d85ee4b7a6b')","ghidra=Path(ghidra_path).resolve();bind(ghidra,ghidra_sha)")
one("start=protocol.index('constexpr std::array<std::uint32_t,109> entries')","start=protocol.index('constexpr std::array<std::uint32_t,116> entries')")
one("protocol[:start]+'constexpr std::array<std::uint32_t,116> entries{'","protocol[:start]+'constexpr std::array<std::uint32_t,120> entries{'")
one("len(pages)==20 and set(pages)-set(prior['extra_pages'])=={0x736000,0x5f4cc000}","len(pages)==23 and set(pages)-set(prior['extra_pages'])=={0x5bc000,0x5cf000,0x5fc000}")
one('len(set(roots))==88','len(set(roots))==92')
one('constexpr std::array<unsigned,20> registration_pages','constexpr std::array<unsigned,23> registration_pages')
one('constexpr std::array<unsigned,88> registration_roots','constexpr std::array<unsigned,92> registration_roots')
one("'phase==109&&r_.calls().size()==112&&r_.translation_count()==110','phase==116&&r_.calls().size()==119&&r_.translation_count()==117'","'phase==116&&r_.calls().size()==119&&r_.translation_count()==117','phase==120&&r_.calls().size()==123&&r_.translation_count()==121'")
one("[('selected109','selected116'),('Connected109','Connected116'),('connected109','connected116'),('persistent109','persistent116'),('Joint109','Joint116'),('records.reserve(109)','records.reserve(116)'),('records.size()==109','records.size()==116'),('total==654','total==696'),('654native','696native'),('1,6,109,654,17,sizeof(Native)','1,6,116,696,17,sizeof(Native)'),('109-root','116-root')]","[('selected116','selected120'),('Connected116','Connected120'),('connected116','connected120'),('persistent116','persistent120'),('Joint116','Joint120'),('records.reserve(116)','records.reserve(120)'),('records.size()==116','records.size()==120'),('total==696','total==720'),('696native','720native'),('1,6,116,696,17,sizeof(Native)','1,6,120,720,17,sizeof(Native)'),('116-root','120-root')]")
s=s.replace('==312','==336').replace('}-312','}-336').replace('])-312','])-336')
one("len(objects['O0'])==len(objects['O2'])==336 and added_counts['O0']==added_counts['O2']==24","len(objects['O0'])==len(objects['O2'])==351 and added_counts['O0']==added_counts['O2']==15")
one('Selected literal container/string constructor root','Selected literal finite-vtable constructor root')
one('Connected116 preparation only; no execution credit','Connected120 preparation only; no execution credit')
p=HERE/'prepare.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
print('Generated additive120 prepare.py')
