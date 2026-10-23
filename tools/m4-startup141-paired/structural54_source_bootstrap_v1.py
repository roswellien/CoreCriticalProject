"""Preload only the admitted physical struct facade, avoiding a cached-code import."""
from pathlib import Path
import hashlib,json,sys,types
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,native_path,native_sha,name):
 p=Path(admission_path).resolve();assert sha(p)==admission_sha;A=json.loads(p.read_bytes())
 assert A['passed']is True and A['physical_struct_facade_preload_reviewed']is True and A['files'][str(Path(__file__).resolve())]==sha(__file__)
 facade=Path(sys.base_prefix)/'Lib/struct.py';assert A['files'][str(facade)]==sha(facade) and '_struct'in sys.builtin_module_names
 source=facade.read_bytes();module=types.ModuleType('struct');module.__file__=str(facade);module.__package__='';exec(compile(source,str(facade),'exec'),module.__dict__);sys.modules['struct']=module
 assert sha(facade)==A['files'][str(facade)]
 driver=R/'tools/m4-startup141-paired/constructor_structural54_pair_v1.py';assert sha(driver)==A['files'][str(driver)]=='4cf4fc32cd7450abd22e6be12e1130c614aef729d00f38de95e46c676ba0a282'
 ns={'__file__':str(driver),'__name__':'ROOT_admitted_structural54'};exec(compile(driver.read_bytes(),str(driver),'exec'),ns);ns['main'](admission_path,admission_sha,native_path,native_sha,name)
if __name__=='__main__':main(*sys.argv[1:])
