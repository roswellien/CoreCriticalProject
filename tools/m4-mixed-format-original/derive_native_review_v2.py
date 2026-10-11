from pathlib import Path
p=Path(__file__).with_name('review_native_preparation.py');s=p.read_text()
s=s.replace("specs=contract['mfc_allocation_contracts'] if 'mfc_allocation_contracts'in contract else contract['allocations']", "specs=contract['MFC_allocation_contracts']")
s=s.replace("for obj,h in body['objects'].items():pin(obj,h);need(report['entry_objects'].get(obj)==h,'Exact added object membership '+obj)", "for value in body['objects'].values():\n                obj,h=value['path'],value['sha256'];pin(obj,h);need(report['entry_objects'].get(obj)==h,'Exact added object membership '+obj)")
out=p.with_name('review_native_preparation_v2.py');assert not out.exists();out.write_text(s)
