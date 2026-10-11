"""Current source guards, physical tail entries and borrowed Runtime entry seam."""
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'prepare_v4.py';s=p.read_text()
needle="exec(compile(s,str(p),'exec'),globals())"
if s.count(needle)!=1:raise ValueError('One staged current Component generator')
edit='''
for a,b in [("for filename in('component.hpp','component.cpp'):shutil.copyfile(pin(R/'tools/m4-constructor-native'/filename),out/filename)","for filename in('component.hpp','component.cpp'):shutil.copyfile(pin(R/'tools/m4-constructor-native'/filename.replace('.', '_v4.',1)),out/filename)"),("need(len(entries)==len(set(entries))==31", "need(len(entries)==len(set(entries))==33"),("literal_bodies=31,new_bodies_from_existing_compiled_IR=25,reused_helper_IRs=6", "literal_bodies=33,new_bodies_from_existing_compiled_IR=25,reused_helper_IRs=6,new_exact_tail_bodies=2"),("source_store_operand_value_guard_pending=True", "source_store_operand_value_guard_pending=False")]:
 if s.count(a)!=1:raise ValueError('Exact current guard/entry Component hunk '+a)
 s=s.replace(a,b,1)
needle=" need(len(entries)==len(set(entries))==33"
position=s.index(needle)
extension=""" tails=read(R/'reports/m4-constructor-native/entry-lifts-r1/report.json','e6082e83ba2c48342ca13c26e79e2b63a6533726d222e64b96cb17cece5e7103');need(tails['passed']and set(tails['source_bodies'])=={'f_4c0310','f_4c0570'},'Two exact missing tail-entry literal bodies')
 for body in tails['source_bodies'].values():
  entry=body['entry'];entries.append(entry);p=pin(R/f'reports/m4-constructor-native/entry-lifts-r1/f_{entry:x}-host.ll',body['host_sha256']);raw=p.read_text();transformed=raw.replace('mw34_onexit_game_','mw34_constructor_game_');need(transformed.replace('mw34_constructor_game_','mw34_onexit_game_')==raw,'Exact new tail IR namespace-only substitution');q=out/p.name;q.write_text(transformed);irs.append(str(q));origins.append(dict(entry=entry,original_IR=str(p),original_sha256=sha(p),component_IR=str(q),component_sha256=sha(q),change='Exact symbol-prefix substitution only; separate physical existing-row tail entry'));bridge_names|=set(re.findall(r'@(mw34_constructor_game_[A-Za-z0-9_]+)',transformed))
"""
s=s[:position]+extension+s[position:]
s=s.replace("public_methods=['borrow_constructor_mfc", "public_methods=['abort_constructor(State&,root) noexcept','constructor_scope(State&,root,bool entering)','borrow_constructor_mfc",1)
s=s.replace("for p in(__file__,R/'tools/m4-constructor-native/prepare.py'", "for p in(__file__,R/'tools/m4-constructor-native/prepare_v4.py',R/'tools/m4-constructor-native/prepare_v5.py',R/'tools/m4-constructor-native/prepare_v6.py',R/'tools/m4-constructor-native/prepare.py'",1)
'''
s=s.replace(needle,edit+'\n'+needle,1)
exec(compile(s,str(p),'exec'),globals())
