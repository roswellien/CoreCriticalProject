"""Bind actual original FS scalar through an unchanged literal prefix."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-original/format_source_v2.py';new=old.with_name('format_source_v3.py');assert not new.exists();body=old.read_text();hunks=[]
 def one(a,b):
  nonlocal body
  assert body.count(a)==1,a[:150];body=body.replace(a,b);hunks.append(dict(old=a,new=b))
 one("if fs_events:memory[0x7ffde000]=bytearray(struct.pack('<I',fs_events[0]['header'][4]))", "first_head=phase_boundaries[0]['header'][5];root_head=fs_events[0]['header'][4]if fs_events else first_head\n            memory[0x7ffde000]=bytearray(struct.pack('<I',root_head))\n            FS_input=dict(kind='genuine_first_game_FS_read'if fs_events else'genuine_first_strrchr_entry_FS_scalar_unchanged_until_entry',actual_value=root_head,first_entry_observed_value=first_head,original_snapshot_header_index=5,original_after_memory_seed=False)")
 one("if address!=0x7ffde000:return", "if address!=0x7ffde000 or source_pc>=0x78000000:return")
 one("eq(self.fx.hex(),actual['FX512_hex'],'Complete carried source FX')", "eq(self.fx.hex(),actual['FX512_hex'],'Complete carried source FX')\n                        if boundary_index[0]==0 and not fs_events:\n                            need(not any(r[1]==0x7ffde000 for r in self.accesses),'The genuine first entry FS scalar is unchanged throughout the literal root prefix');FS_input['literal_no_FS_access_before_first_entry']=True;FS_input['source_PCs_before_observation']=list(self.PCs)\n                        eq(u(self.bytes(0x7ffde000,4))[0],actual['header'][5],'Actual compiled observer FS head matches literal entry/return head');counts['actual_cdecl_FS_head_joins']+=1")
 one("results.append(dict(sequence=sequence,phase=phase,root=root['entry'],", "results.append(dict(sequence=sequence,phase=phase,root=root['entry'],FS_initial_input=FS_input,")
 one("allocator_FS_frames_literal_only=False", "allocator_FS_frames_literal_only=True,allocator_FS_individual_events_observed=False,actual_cdecl_FS_head_joins_required=144")
 ast.parse(body);new.write_text(body)
 out=R/'reports/m4-startup130-original/format-source-preparation-r3';assert not out.exists();out.mkdir(parents=True)
 vp=R/'reports/m4-startup130-original/validation-r2/report.json';v=json.loads(vp.read_bytes());assert v['passed']and sha(vp)=='91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca'
 cp=vp.parent/'fresh-cdecl.json';assert sha(cp)==v['files'][str(cp.resolve())];rows=json.loads(cp.read_bytes());first=[dict(sequence=r['sequence'],root=r['root'],actual_PC=r['header'][4],actual_frame=r['CPU'][4],actual_FS_head=r['header'][5],header=r['header'],source_original_observer='MOV EAX,FS:[0] before host stack switch; C++ snapshot.words[5]=format_head',unchanged_prefix_proof_required=r['root']!=0x4e1ca0)for r in rows if r['kind']==0];assert len(first)==24
 asm=R/'reports/m4-startup130-original/preparation-r2/format_observer_x86.asm';cpp=asm.with_name('format_observer.hpp');assert asm.read_text().count('mov eax,DWORD PTR fs:[0]')==6;assert 's.words[5]=format_head' in cpp.read_text()
 ep=out/'genuine-first-entry-FS-inputs.json';ep.write_text(json.dumps(first,indent=2)+'\n');hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n')
 paths=[old,new,Path(__file__),vp,cp,asm,cpp,ep,hp,R/'reports/m4-tree-review/original130-prelaunch-r7/report.json'];pins={str(p.resolve()):sha(p)for p in paths}
 report=dict(passed=True,scope='Prepared finite genuine original FS input adapter. Formatter3 first strrchr ENTRY head is admitted only under an executed literal no-prior-FS-access proof; mixed initial head remains actual game FS-read predecessor. All144 measured cdecl entry/return heads must match the source state. CRT internal FS frames remain literal-only; no individual observed CRT FS event claim.',original_validation_sha256=sha(vp),actual_FS_entry_inputs=24,required_cdecl_FS_head_joins=144,files=pins,capture_reader_opened=False,executed=False,native_input_seed=False,original_AFTER_memory_seed=False)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
