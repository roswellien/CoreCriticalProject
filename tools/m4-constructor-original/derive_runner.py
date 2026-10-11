"""Reuse the admitted single-writer controller; no worker invocation here."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=here.parent/'m4-startup131-original/run.py'
target=here/'run.py'
assert not target.exists()
text=source.read_text()
assert "reports/m4-startup131-original" in text
text=text.replace('reports/m4-startup131-original','reports/m4-constructor-original')
text=text.replace('(131,786,356992)','(37,222,356992)')
text=text.replace('full131','chronological constructor37')
text=text.replace('Genuine chronological constructor37 original six-domain writer only; complete source/resource/semantic validation follows','Genuine37-root selected original chronology through three new constructors; semantic source/resource validation follows')
text=text.replace("pin(__file__);pin(R/'tools/m4-pipeline/stages.py')", "pin(__file__);pin(Path(__file__).with_name('derive_runner.py'));pin(R/'tools/m4-startup131-original/run.py');pin(R/'tools/m4-pipeline/stages.py')")
target.write_text(text)
