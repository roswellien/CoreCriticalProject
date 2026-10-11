from pathlib import Path
p=Path(__file__).with_name('review_controls.py');s=p.read_text()
s=s.replace("        need('source allocation' not in fixture.lower()or True,'Scope retained')\n",'')
s=s.replace("operations_path=Path(prep['native_preparation']).parent/'formatting_operations.inc'", "operations_path=Path(prep['native_preparation']).parent/'locale_batch_binding.inc'")
out=p.with_name('review_controls_v2.py');assert not out.exists();out.write_text(s)
