"""Add exact 16-bit bridges used only by dormant literal formatter branches."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare.py');s=p.read_text()
a="else:raise ValueError(symbol)";assert s.count(a)==1
s=s.replace(a,"""elif symbol=='mw34_onexit_game_read16':s+='\\nextern "C" unsigned short mw34_onexit_game_read16(void*p,unsigned a){return static_cast<unsigned short>(mw34::m4_onexit::read(p,a,2));}\\n'
        elif symbol=='mw34_onexit_game_write16':s+='\\nextern "C" void*mw34_onexit_game_write16(void*p,unsigned a,unsigned short v){return mw34::m4_onexit::write(p,a,v,2);}\\n'
        else:raise ValueError(symbol)""")
s=s.replace('pin(__file__)','pin(__file__);pin(R/\'tools/m4-formatting-native/prepare.py\')')
exec(compile(s,str(p),'exec'),globals())
