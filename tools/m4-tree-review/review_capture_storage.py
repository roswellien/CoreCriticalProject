"""Keep strict capture integrity unchanged while admitting a fixed storage root."""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={}
 p=R/'reports/m4-capture-storage/preparation-r1/report.json';assert sha(p)=='cf096edbcd81ef23424abf16ffd4057eed23b511ff59b45ab005e8aa18886bb9';d=json.loads(p.read_bytes());pins[str(p)]=sha(p)
 for p,h in d['files'].items():assert sha(p)==h;pins[p]=h
 assert d['passed']and not d['worker_binaries_changed']and not d['existing_outputs_moved']and not d['archives_opened']
 for row in d['relations']:
  text=Path(row['parent']).read_text()
  for before,after in row['exact_import_changes']:assert text.count(before)==1;text=text.replace(before,after)
  assert text==Path(row['current']).read_text()
 from paths_capture_storage import workspace_path,STORAGE_ROOT
 allowed=[(R/'reports/m4-capture-storage/future/report.json',True),(STORAGE_ROOT/'reports/m4-joint-startup138/future/O0/transport.json',True),(STORAGE_ROOT,False)]
 for p,reports in allowed:assert workspace_path(p,reports=reports)==p
 rejected=[(STORAGE_ROOT/'..'/'unrelated'/'data',False),(STORAGE_ROOT/'reports'/'..'/'elsewhere'/'data',True),(STORAGE_ROOT/'reports',True),(R/'reports',True),(Path('E:/Projects/Unrelated/reports/data'),True)]
 for p,reports in rejected:
  try:workspace_path(p,reports=reports)
  except ValueError:pass
  else:raise AssertionError('Undeclared root/escape admitted '+str(p))
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetDriveTypeW.argtypes=[ctypes.c_wchar_p];assert kernel.GetDriveTypeW('G:\\')==3
 fs=ctypes.create_unicode_buffer(64);assert kernel.GetVolumeInformationW('G:\\',None,0,None,None,None,fs,len(fs))and fs.value=='NTFS'
 free=ctypes.c_ulonglong();total=ctypes.c_ulonglong();wholefree=ctypes.c_ulonglong();assert kernel.GetDiskFreeSpaceExW('G:\\',ctypes.byref(free),ctypes.byref(total),ctypes.byref(wholefree));assert free.value>160*1024**3
 workspace_path(STORAGE_ROOT);STORAGE_ROOT.mkdir(parents=True,exist_ok=True);workspace_path(STORAGE_ROOT)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable)
 for p,h in pins.items():assert sha(p)==h
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,storage_root=str(STORAGE_ROOT),storage_drive_type=3,storage_filesystem=fs.value,available_bytes=free.value,minimum_free_bytes=160*1024**3,whole_unchanged_stage_reader_relations=3,declared_path_cases=len(allowed),rejected_path_cases=len(rejected),hash_index_payload_limits_and_stable_close_unchanged=True,archives_opened=False,workers_launched=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
