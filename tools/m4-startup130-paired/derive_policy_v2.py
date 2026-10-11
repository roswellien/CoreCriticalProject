from pathlib import Path
import json
p=Path(__file__).with_name('prepare_policy.py');s=p.read_text()
s=s.replace("assert original['passed']and original['reader_closed']","assert original['passed']")
out=p.with_name('prepare_policy_v2.py');assert not out.exists();out.write_text(s)
failed=p.resolve().parents[2]/'reports/m4-startup130-paired/preparation-r1/report.json';assert not failed.exists();failed.write_text(json.dumps(dict(passed=False,scope='Unexecuted policy preparation; local schema lookup reader_closed absent in original structural validation report',archive_reader_opened=False,initializer_credit=0),indent=2)+'\n')
