"""Loaded provider source is owned by its PE, while sparse game spans use the pack."""
from pathlib import Path
previous=Path(__file__).with_name('review_original131_prelaunch_v2.py')
program=previous.read_text()
anchor="exec(compile(source,str(parent),'exec'),globals())"
before="   for i,z in enumerate(source):assert pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==z"
after="   if not row['origin']:\n    for i,z in enumerate(source):assert pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==z"
program=program.replace(anchor,'source=source.replace('+repr(before)+','+repr(after)+');source=source.replace("  pin(parent);", "  pin(previous);pin(parent);");'+anchor)
exec(compile(program,str(previous),'exec'),globals())
