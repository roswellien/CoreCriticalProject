"""Route each source hook to its physically owning legacy image."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
parent=Path(__file__).with_name('review_original138_prelaunch.py')
t=parent.read_text()
a="        cp = PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())"
assert t.count(a)==1
t=t.replace(a,a+"\n        crt = PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())",1)
a="        actual_pack = sparse(folder/'pages.bin',p['pack_sha256'])"
assert t.count(a)==1
t=t.replace(a,"        def hook_image(pc):\n            if pc < 0x10000000: return game\n            return cp if pc >= cp.image_base else crt\n\n"+a,1)
a="physical(game,row['PC'],len(raw))"
assert t.count(a)==1
t=t.replace(a,"physical(hook_image(row['PC']),row['PC'],len(raw))",1)
a="physical(game,row['pc'],row['bytes'])"
assert t.count(a)==1
t=t.replace(a,"physical(hook_image(row['pc']),row['pc'],row['bytes'])",1)
assert t.count("r'std::array<unsigned,\\d+> bases") == 2
t=t.replace("r'std::array<unsigned,\\d+> bases","r'std::array<std::uint32_t,\\d+> bases")
a="        pin(__file__)"
assert t.count(a)==1
t=t.replace(a,"        pin(parent)\n"+a,1)
exec(compile(t,str(Path(__file__)),'exec'),globals())
