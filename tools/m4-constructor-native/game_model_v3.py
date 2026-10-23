"""Additive exact malloc source closure; inherited semantics unchanged."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_v2_frozen',R/'tools/m4-constructor-native/game_model_v2.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;Machine=P.Machine;from_original_before=P.from_original_before
def checked(p,h):
 raw=p.read_bytes();I.need(hashlib.sha256(raw).hexdigest()==h,'Pinned malloc physical literal descriptors');return json.loads(raw)
def source_program(preparation):
 program,callbacks=P.source_program(preparation)
 rows=checked(R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1/instructions.json','d0d25892ffbdf05d847cb190e42f3e7342ec1958e6ca7ea185f20b31492178a6')['instructions']
 cb=checked(R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1/callbacks.json','4bc26820a34cc488600c0e4b190da6b3dc77b3442179c0d3147a047db8e75b0a')['State_offsets_by_original_PC']
 for row in rows:
  pc=row['pc'];I.need(pc not in program or (program[pc]['width'],program[pc]['bytes_hex'],program[pc]['decoded_operands'])==(row['width'],row['bytes_hex'],row['decoded_operands']),'Exact shared literal row');program[pc]=row
 for pc,offsets in cb.items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact shared undefined callback order');callbacks[pc]=offsets
 return program,callbacks
