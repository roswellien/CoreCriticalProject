"""Keep the genuine getter BEFORE snapshot until its literal MOV comparison."""
from pathlib import Path
source=Path(__file__).resolve().with_name('validate.py')
target=source.with_name('validate_v2.py')
assert not target.exists()
text=source.read_text()
old="'Actual reached virtual getter entry');getter=row"
new="'Actual reached virtual getter entry');getter=dict(row)"
assert text.count(old)==1
text=text.replace(old,new,1)
old="        pin(__file__);pin(sys.executable);passed=True"
new="        pin(__file__);pin(Path(__file__).with_name('validate.py'));pin(Path(__file__).with_name('derive_validator_v2.py'));pin(sys.executable);passed=True"
assert text.count(old)==1
text=text.replace(old,new,1)
target.write_text(text)
