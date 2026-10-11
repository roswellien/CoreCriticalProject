"""Add literal function-entry ledger offsets and strict logical scratch LIFO."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tools/m4-tree-source/game_model.py';raw=source.read_text()
replacements=[
    ("self.tree_site_ordinals={};self.tree_frame_ids={};self.tree_definitions={}","self.tree_site_ordinals={};self.tree_frame_ids={};self.tree_definitions={};self.tree_lock_scopes=[]"),
    ("record=dict(index=index,entry=data['target'],CALL_pc=pc,frame=list(frame),entry_ECX=self.reg('ecx'))", "record=dict(index=index,entry=data['target'],CALL_pc=pc,frame=list(frame),entry_ECX=self.reg('ecx'),source_access_index=len(self.accesses))"),
    ("pc=row['pc'];spec=self.tree_scratch[pc]", "pc=row['pc'];spec=self.tree_scratch[pc]\n        if spec['role'].endswith('dtor'):\n            I.need(self.tree_lock_scopes,'Destructor has a source-established outstanding Lockit scope')\n            scope=self.tree_lock_scopes[-1]\n            I.need(scope['invocation']==self.invocation()and scope['ECX']==self.reg('ecx'),'Same invocation/scratch strict Lockit LIFO')\n            if pc==0x4badd0 and self.reg('ecx')==((self.reg('esp')-4+24)&0xffffffff):I.need(scope['CALL_pc']==0x4bad8f,'Outer-left shared destructor has exact originating constructor')"),
    ("self.tree_lockit_calls.append(proof)", "self.tree_lockit_calls.append(proof)\n                    if proof['role'].endswith('ctor'):self.tree_lock_scopes.append(proof)\n                    else:\n                        scope=self.tree_lock_scopes.pop();proof['matching_constructor_CALL_pc']=scope['CALL_pc'];proof['matching_constructor_invocation']=scope['invocation']"),
    ("not self.tree_pending_lockits and not self.tree_open_FS", "not self.tree_pending_lockits and not self.tree_open_FS and not self.tree_lock_scopes"),
]
for old,new in replacements:
    assert raw.count(old)==1,old;raw=raw.replace(old,new)
target=ROOT/'tools/m4-tree-source/game_model_v2.py';assert not target.exists();target.write_text(raw)
out=ROOT/'reports/m4-tree-source/model-preparation-r2';assert not out.exists();out.mkdir(parents=True)
files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(source,target,Path(__file__))}
report=dict(passed=True,scope='Additive exact invocation-entry ledgers and constructor/destructor scratch LIFO; no AFTER seeds',replacements=replacements,files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
