"""Use exact generic malloc owner source in an explicit additive input file."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v9.py');source=p.read_text();anchor="exec(compile(source,str(p),'exec'),globals())";assert source.count(anchor)==1
source=source.replace(anchor,"source=source.replace(\"R/'tools/m4-formatting-native/formatting_operations.inc'\",\"R/'tools/m4-formatting-native/formatting_operations_v2.inc'\").replace('a->kind!=2','a->kind!=1')\n"+anchor)
exec(compile(source,str(p),'exec'),globals())
