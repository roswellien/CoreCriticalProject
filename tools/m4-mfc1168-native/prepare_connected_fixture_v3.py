from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;v2=p/'prepare_connected_fixture_v2.py';text=v2.read_text()
text=text.replace('"pin(parent)\\n  for p in', '"pin(R/\'tools/m4-mfc1168-native/prepare_connected_fixture.py\');pin(R/\'tools/m4-mfc1168-native/prepare_connected_fixture_v2.py\')\\n  for p in')
exec(compile(text,str(v2),'exec'),globals())
