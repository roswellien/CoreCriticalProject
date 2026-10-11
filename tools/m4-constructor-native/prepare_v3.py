"""Use the existing physical PE range adapter, retaining every source byte check."""
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'prepare_v2.py';s=p.read_text()
a="exec(compile(s,str(source),'exec'),globals())"
b="s=s.replace('game.data[game.rva_to_offset(address-game.image_base):game.rva_to_offset(address-game.image_base)+n]','game.data[game.rva_range(address-game.image_base,n)[0]:game.rva_range(address-game.image_base,n)[0]+n]',1)\ns=s.replace(\"for p in(__file__,R/'tools/m4-constructor-native/prepare.py'\",\"for p in(__file__,R/'tools/m4-constructor-native/prepare_v2.py',R/'tools/m4-constructor-native/prepare.py'\",1)\nexec(compile(s,str(source),'exec'),globals())"
if s.count(a)!=1:raise ValueError('One exact PE adapter execution seam')
exec(compile(s.replace(a,b,1),str(p),'exec'),globals())
