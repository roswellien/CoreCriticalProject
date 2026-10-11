"""Frozen Extension with the additive explicit-consumer literal evaluator."""
from pathlib import Path
import hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'tools/m4-joint-startup131/mfc_source.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='591bbc9cde5e23c12c51236f9c812031de2eedde8eb9c4d51c9947d14b060d07'
s=importlib.util.spec_from_file_location('joint131_mfc_source_base',path);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
class Extension(M.Extension):
 def __init__(self,preparation,pin):
  super().__init__(preparation,pin);pin(path);self.literal=M.module(ROOT/'tools/m4-mfc1168-native/persistent_source_v2.py','joint131_mfc_literal_defined',pin);pin(ROOT/'tools/m4-joint-startup131/flag_consumers.py')
 def phase(self,machine,*args,**kwargs):
  result=super().phase(machine,*args,**kwargs);machine._source_undefined_flags=dict(result['final_undefined_flags']);self.counts['MFC_defined_flag_consumers']+=len(result['defined_flag_consumers']);return result
