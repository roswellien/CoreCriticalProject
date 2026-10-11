"""Place new member definitions in their actual inherited Binding namespace."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v7.py');source=p.read_text();anchor="exec(compile(source,str(p),'exec'),globals())";assert source.count(anchor)==1
extra=r'''
source=source.replace(".read_text().replace('++formatting_dispatch_cursor_;'", ".read_text().removeprefix('namespace {\\n').removesuffix('}\\n').replace('++formatting_dispatch_cursor_;'")
source=source.replace("namespace {void Binding::formatting_guard()", "void Binding::formatting_guard()")
source=source.replace("formatting_owner_);}}}\\\\n", "formatting_owner_);}}\\\\n")
'''
source=source.replace(anchor,extra+'\n'+anchor)
exec(compile(source,str(p),'exec'),globals())
