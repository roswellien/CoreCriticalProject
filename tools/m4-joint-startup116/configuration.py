"""Freeze exact116 measured receipts without granting execution credit."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(specification,name):
 source=Path(specification).resolve();spec=json.loads(source.read_bytes())
 module=importlib.util.spec_from_file_location('accept116',Path(__file__).with_name('accept.py'))
 acceptance=importlib.util.module_from_spec(module);module.loader.exec_module(acceptance)
 assert set(spec)==acceptance.REQUIRED
 gates={}
 for label,item in spec.items():
  assert set(item)=={'path','sha256','equal'}
  path=(ROOT/item['path']).resolve();report=json.loads(path.read_bytes())
  assert report['passed'] is True and sha(path)==item['sha256'],label
  assert item['equal'],label
  for field,expected in item['equal'].items():
   actual=report
   for key in field.split('.'):actual=actual[key]
   assert actual==expected,(label,field,actual,expected)
  gates[label]=dict(path=path.relative_to(ROOT).as_posix(),sha256=item['sha256'],equal=item['equal'])
 scope=dict(callback_execution=False,full_CRT_attach=False,full_native_MFC_attach=False,native_menu=False,native_Training=False,whole_game_alias_liveness=False,handler_execution=False,exception_dispatch=False,allocation_NULL_paths=False,whole_original_provider_stack_equality=False,whole_original_Windows_TIB_page_claimed=False,capture_shared_format_adopted=False,naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed=False,controls_host_boundary_scope='Authored caller NumericHostBoundary enclosing invocation and C++ catch',original_chain='Authentic opaque Windows FS0; no actual whole TIB page or host-chain equivalence claim',native_chain='Runtime-owned minimal TIB fields at7FFDE000 and explicit FFFFFFFF initial chain identity; complete normal12B records',new_header='Inherited exact byte60B51C from genuine branch BEFORE stack byte at200017EB; no whole-game alias liveness claim',FSQRT='Inherited accepted zero-vector constructor only',provider_growth='First genuine source replay HeapSize capacity independently predicts first replay growth; same old owner/capacity authenticated for the realloc-side query',source_owned_header_and_pointer_relations=True,borrowed_MFC_nil='Actual same-worker DLL bootstrap DWORD and native raw PE DWORD independently authenticated; borrowed pointee remains outside admitted read footprint',whole_loader_page='Complete original bootstrap page and native raw page carried separately; every actual branch page difference enumerated',normal_CRT_free_NULL='Literal normal free(NULL) path with authentic CPU/FX/ENV and nested12B chain frames; allocation-NULL and exception paths remain outside scope')
 result=dict(gates=gates,extent=acceptance.EXTENT,bounded_scope=scope,configuration_source=str(Path(__file__).resolve()),configuration_source_sha256=sha(__file__),review_specification=str(source),review_specification_sha256=sha(source))
 out=ROOT/'reports/m4-joint-startup116-root'/name;assert not out.exists()
 out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(configuration=str(out),sha256=sha(out),gates=len(gates))))

if __name__=='__main__':main(*sys.argv[1:])
