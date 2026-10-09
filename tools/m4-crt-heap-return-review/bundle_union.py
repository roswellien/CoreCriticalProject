"""Non-extracting exact disjoint union of two unchanged strict capture readers."""
import contextlib,json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,MAX_FILES,sha_file
from manifests import unique_object
from paths import logical_name

def need(ok,why):
    if not ok:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

class BundleUnion:
    def __init__(self,info,expected):
        self.info,self.expected=info,expected;self.stack=None;self.owners={}
    def __enter__(self):
        need(len(self.info['bundles'])==2 and [p['part'] for p in self.info['bundles']]==[1,2],'Exactly two declared bounded capture parts')
        self.stack=contextlib.ExitStack()
        try:
            for part in self.info['bundles']:
                need(sha_file(part['inventory_path'])==part['inventory_sha256'],'External per-part inventory digest')
                records=read(part['inventory_path'])['files']
                need(0<len(records)==part['logical_files']<=MAX_FILES,'Unchanged strict bounded part count')
                bundle=self.stack.enter_context(CaptureBundle(part['bundle'],part['bundle_sha256']))
                need(bundle.names()==tuple(sorted(records)),'Exact per-part externally bound inventory')
                for name,row in records.items():
                    logical_name(name);need(name not in self.owners and row==self.expected.get(name),'Disjoint original-relative-name and whole-inventory hash association')
                    self.owners[name]=bundle
            need(tuple(sorted(self.owners))==tuple(sorted(self.expected)) and len(self.owners)==self.info['logical_files'],'Complete exact archive union')
            return self
        except BaseException:
            self.stack.close();raise
    def __exit__(self,*args):
        self.stack.close()
    def names(self):return tuple(sorted(self.owners))
    def read_bytes(self,name):
        name=logical_name(name);need(name in self.owners,'No unbound union read');return self.owners[name].read_bytes(name)
