"""Exact current publication guards and separately loaded provider pages."""
from pathlib import Path
parent=Path(__file__).with_name('review_original131_prelaunch.py')
source=parent.read_text()
source=source.replace("old['selected_order']+[dict(slot=0x5e0040,entry=0x5ae3e4)]", "[dict(slot=v['slot'],entry=v['entry'])for v in old['selected_order']]+[dict(slot=0x5e0040,entry=0x5ae3e4)]")
source=source.replace("   for i,z in enumerate(source):assert pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==z", "   if not row['origin']:\n    for i,z in enumerate(source):assert pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==z")
source=source.replace("  assert main_cpp.count('std::find(entries.begin(),entries.begin()+phase+1,binding.root)!=entries.begin()+phase+1')==2", "  assert main_cpp.count('std::find(entries.begin(),entries.begin()+phase+1,binding.root)==entries.begin()+phase+1)continue;')==1 and main_cpp.count('std::find(entries.begin(),entries.begin()+phase+1,binding.entry)==entries.begin()+phase+1)continue;')==1")
source=source.replace("  pin(R/'tools/m4-startup131-original/run.py');", "  pin(parent);pin(R/'tools/m4-startup131-original/run.py');")
exec(compile(source,str(parent),'exec'),globals())
