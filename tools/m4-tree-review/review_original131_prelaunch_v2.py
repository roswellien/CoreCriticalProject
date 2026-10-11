"""Normalize old explicit phase metadata to literal table-pair chronology."""
from pathlib import Path
parent=Path(__file__).with_name('review_original131_prelaunch.py')
source=parent.read_text()
source=source.replace("old['selected_order']+[dict(slot=0x5e0040,entry=0x5ae3e4)]", "[dict(slot=v['slot'],entry=v['entry'])for v in old['selected_order']]+[dict(slot=0x5e0040,entry=0x5ae3e4)]")
source=source.replace("  pin(R/'tools/m4-startup131-original/run.py');", "  pin(parent);pin(R/'tools/m4-startup131-original/run.py');")
exec(compile(source,str(parent),'exec'),globals())
