"""Retain original unused-stack observations without seeding source memory."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tools/m4-tree-source/compare_prefix.py';raw=source.read_text()
old="lock_index=[0];fs_index=[0]"
new="lock_index=[0];fs_index=[0];unused_frame_bytes=[]"
assert raw.count(old)==1;raw=raw.replace(old,new)
old="equal(machine.bytes(machine.reg('esp'),32),raw[644:676],'Complete source-established original32B CALL frame');equal(machine.bytes(0x78145640,24),raw[676:700],'Full carried CS24 at original boundary')"
new="""modeled=machine.bytes(machine.reg('esp'),32);actual=raw[644:676]
            invocation=machine.invocation();invocation_rows=[r for r in machine.tree_function_invocations if r['index']==invocation]
            first=invocation_rows[0]['source_access_index']if invocation_rows else 0
            for offset,(expected,observed)in enumerate(zip(modeled,actual)):
                address=machine.reg('esp')+offset
                writes=[r for r in machine.accesses[first:]if r[4]and r[1]<=address<r[1]+r[3]]
                if writes:need(expected==observed,'Every source-established current-frame byte matches actual original')
                elif expected!=observed:unused_frame_bytes.append(dict(boundary_index=lock_index[0],address=address,source_value=expected,actual_observation=observed,source_access_index=len(machine.accesses),invocation=invocation,source_frame_first_access=first,current_frame_source_write=False))
            equal(machine.bytes(0x78145640,24),raw[676:700],'Full carried CS24 at original boundary')"""
assert raw.count(old)==1;raw=raw.replace(old,new)
old="result['original_boundary_joins']=boundaries;result['observer_patches']=patches;result['reached_original_PCs']=machine.PCs;passed=True"
new="""for row in unused_frame_bytes:
            subsequent=[(index,access)for index,access in enumerate(machine.accesses[row['source_access_index']:],row['source_access_index'])if access[1]<=row['address']<access[1]+access[3]]
            if subsequent:
                index,access=subsequent[0];need(access[4],'Observed opaque unused frame byte cannot enter a subsequent literal source read before overwrite')
                row['subsequent_dominating_source_write']=dict(index=index,pc=access[0],address=access[1],width=access[3],value=access[2])
            else:row['never_subsequently_read_or_written']=True
        result['unused_original_frame_observations']=unused_frame_bytes
        result['original_boundary_joins']=boundaries;result['observer_patches']=patches;result['reached_original_PCs']=machine.PCs;passed=True"""
assert raw.count(old)==1;raw=raw.replace(old,new)
raw=raw.replace("original_postRET_observed=False,whole_provider_stack_compared=False", "original_postRET_observed=False,whole_provider_stack_compared=False,original_unused_frame_bytes_seeded=False,all_current_frame_source_written_bytes_compared=True,opaque_disagreements_proven_unused_before_overwrite=True")
target=ROOT/'tools/m4-tree-source/compare_prefix_v2.py';assert not target.exists();target.write_text(raw)
out=ROOT/'reports/m4-tree-source/prefix-comparison-preparation-r2';assert not out.exists();out.mkdir(parents=True)
files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(source,target,Path(__file__))}
report=dict(passed=True,scope='Additive explicit unused original external-stack policy; original opaque bytes never enter source machine',files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
