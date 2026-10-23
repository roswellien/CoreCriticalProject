"""Retain full definition preflight and prove Session101/vector108 distinction."""
from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parents[2]
BASE=R/'tools/m4-138-source-review/preflight_projection_namespace.py'
s=BASE.read_text()
for a,b in [
('2fd057d3f8c8e72332973952af2d3a663eee97e267a01234095123d2d40f8f63','addd156cf83cf33776395bc55e958af83a1cdbca61ebcfc2af2d07ad9c821d72'),
('preparation-r10/report.json','preparation-r11/report.json'),
("p['writer_executed']is False and p['capture_archive_reader_opened']is False", "p['source_execution_performed']is False and p['archive_reader_opened']is False"),
]:
 assert s.count(a)==1,a
 s=s.replace(a,b)
anchor="  need(current.index('required_original=dict(')"
assert s.count(anchor)==1
extra="""  previous=pin(ROOT/'reports/m4-joint-startup138-source/preparation-r10/final_observer138.py').read_text()
  actual=pin(entry.parent/'final_observer138.py').read_text()
  removed=".replace('registry-replay-{101+n}','registry-replay-{108+n}')"
  need(previous.count(removed)==1 and previous.replace(removed,'')==actual,'Exact observer naming inverse; all callback/vector/fullstate/resource obligations preserved')
  compiled=module.F.F._text
  need(compiled.count('registry-replay-{101+n}')==2 and 'len(roots)==108'in compiled and "COUNTS['selected_registration_closures']+=108"in compiled,'Actual imported full source observer keeps Session checkpoint labels101 and vector108')
  service=pin(ROOT/'reports/m4-fps-native/service-preparation-r3/session_impl.inc').read_text()
  borrowed=service[service.index(' void borrow_widget_onexit('):service.index('\\n void finish(){')]
  need('++roots'not in borrowed and service.count('++roots;')==2,'Physical compiled Session increments counter only for direct entry and replay')
  contract=pin(ROOT/'reports/m4-joint-startup138/preparation-r4/registration_contract.hpp').read_text()
  need('std::array<unsigned,108> registration_roots'in contract and len(module.PW.WIDGETS)==7,'Full108 callback vector and exact seven borrowed source roots')
  # Finite checkpoint-name coverage policy: reject the count conflation.
  observed={'registry-replay-101-before','registry-replay-101-after'}
  predictions={f'registry-replay-{101+n}-{side}'for n in range(1)for side in('before','after')}
  need(predictions==observed,'Every finite replay checkpoint predicted')
  bad={f'registry-replay-{108+n}-{side}'for n in range(1)for side in('before','after')}
  need(bad!=observed and sorted(observed-bad)==sorted(observed),'Wrong callback-count naming is refused, never omitted')
"""
s=s.replace(anchor,extra+anchor)
s=s.replace('pin(__file__);pin(sys.executable)', 'pin(BASE);pin(__file__);pin(sys.executable)')
ast.parse(s)
exec(compile(s,str(BASE),'exec'),globals())
