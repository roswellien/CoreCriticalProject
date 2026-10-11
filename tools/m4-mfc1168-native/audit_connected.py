"""Read-only connected gap audit. No archives or native AFTER state consumed."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');a=sha(p);assert h is None or a==h,(p,h,a);pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def text(p):return pin(p).read_text()
 acceptance=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa');assert acceptance['passed']
 j=read(R/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c');assert j['passed']
 original=read(R/'reports/m4-startup130-original/preparation-r2/report.json');contracts=read(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json','f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64')
 source=read(R/'reports/m4-mfc1168-native/resource-source-r1/report.json','9195e7107ec29ef8ee6b97694b1eae9a9c18aacdfe5a8aa27e5aca4d8f88d2aa');resource=read(R/'reports/m4-mfc1168-native/resource-verification-r1/report.json','4dfcf886d6a4c6c2dd0f86a04a8d7db87056db325a9fe7987ce59a416f8e38fb');prefix=read(R/'reports/m4-mfc1168-native/resource-prefixes-r2/report.json','d4b3d38cf1e9b0dd9f8f9d5d2ad434dfb7f9655ded3680977b0c0f4550f6bb64');assert source['passed']and resource['passed']and prefix['passed']
 policy=read(R/'reports/m4-mfc1168-native/resource-preparation-r3/relocation-proof.json');slot,entry=0x5e0040,0x5ae3e4
 s=importlib.util.spec_from_file_location('mfc_gap_pe',pin(R/'tools/analysis/pe.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);game=m.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());offset,_=game.rva_range(slot-game.image_base,4);assert struct.unpack_from('<I',game.data,offset)[0]==entry
 selected=j['selected_order'];assert len(selected)==130 and not any(x['slot']==slot or x['entry']==entry for x in selected);prior=[dict(phase=i,**x)for i,x in enumerate(selected)if x['slot']<slot];assert len(prior)==13
 pages=original['observed_pages']+original['extra_whole_source_pages'];assert len(pages)==46 and 0x5f4cb000 not in pages and 0x78037000 not in pages
 native=r=Path(j['native_include']);texts={n:text(r/n)for n in('session_impl.inc','fs_operations.inc','locale_batch_operations.inc','lockit_operations.inc','source_contract.inc')};protocol=text(R/'reports/m4-joint-startup130/preparation-r2/joint_protocol.hpp');original_protocol=text(R/'reports/m4-startup130-original/preparation-r2/protocol.hpp');runtime=text(R/'tools/m4-runtime/runtime.hpp');seed=text(R/'reports/m4-joint-startup130/preparation-r2/seed.inc')
 assert 'frame=0x20001800' in protocol and 'frame=0x20001800' in original_protocol and 'GuestAddress teb{0x7ffde000}'in runtime
 assert 'Only an actual registered literal initializer root may enter'in texts['session_impl.inc'];assert entry not in j['registration_roots']
 expected=dict(root=entry,slot=slot,new_selected_initializer=True,new_registered_callback=False,implementation_dependency_only=False,insertion_phase=13,current_selected_count=130,proposed_selected_count=131,preceding_selected=prior,next_selected=next(x for x in selected if x['slot']>slot),unaccepted_earlier_table_slots=[dict(slot=s,entry=struct.unpack_from('<I',game.data,game.rva_range(s-game.image_base,4)[0])[0])for s in(0x5e0038,0x5e003c)],ordinary_original_and_native_root_frame=0x20001800,isolate_root_frame=0x20008000,registration_bootstrap_research_frame=0x20001860,native_FS_base=0x7ffde000,genuine_isolated_TEB=contracts['thread_contract']['source_TEB'],accepted_record_pages=pages,missing_current_source_domain_pages=[0x5f4cb000,0x78037000],five_role_relocation=policy,new_game_row_count=25,new_literal_entries=13,new_literal_normal_instructions=142,normal_source_operands=113,source_owning_API_count=4,typed_native_resource_services=9,existing_body_PC_overlap=[x['pc']for x in original['source_spans']if x['pc']in{r['pc']for r in contracts['instructions']}],genuine_chronological_MFC_prefix_evidenced=False,connected_native_preparation_admitted=False,initializer_credit=0)
 (out/'connected-domain-gap.json').write_text(json.dumps(expected,indent=2)+'\n')
 note='''# MFC1168 connected preparation prerequisites

`5AE3E4` is a new initializer at physical slot `5E0040`, not a callback registration or merely an implementation dependency. In a 131-root extension of the accepted 130 schedule it enters at phase 13, after the thirteen selected slots `5E0004` through `5E0034`, before `4040F0` at `5E0044`. The still unaccepted earlier slots `5E0038/5E003C` remain explicitly omitted until their own closures are integrated.

Both connected root protocols use frame `20001800`. The registration bootstrap research frame `20001860` is separate. The isolated MFC fixture used frame `20008000` and fresh sentinel integer inputs, so its successful 142-row proof does not establish the chronological caller's CPU, stack or floating-point inputs.

The accepted ordinary 46-page scope omits `5F4CB000`, `78037000`, the five cached manager/thread backing roles and the actual codepage lock24. Accepted native guest FS has base `7FFDE000` with its own sentinel, stack bounds and self identity; authentic Windows FS/TEB bytes must not replace those fields. The new typed TLS mirror may be a separately declared guest cell, while the physical Windows TLS slot and native current-thread mirror remain independent owned host resources.

Use only the five explicit role aliases and six typed pointer fields from the genuine BEFORE alias policy. Borrowed role extents are 256/16/12/280/4240 bytes at distinct `3300xxxx` guest addresses. The three consumed pointer reads plus typed TLS return are required, and the other carried manager/TEB pointer cells remain declared. No pointer-like integer scan, no game PE BSS overwrite, and no source AFTER input is admitted.

The next original worker should reuse the exact original130 sparse source/loader/bootstrap and execute only its first13 accepted roots plus `5AE3E4`. Retain each root CPU40/FX512/ENV28, whole source pages and stack, callback vector carry, and immediate BEFORE/AFTER MFC+CRT+TEB/current five backings. Add the seven exact game/provider boundary observations and four actual named API pairs from the current MFC probe. Do not invoke1168 to discover its pointer. One genuine schedule is the smallest discovery run; final connected acceptance still requires the actual finite six caller domains.

After that genuine prefix closes, parameterize the 113 access addresses by actual root frame and the six typed aliases; preserve live incoming State3504/CPU40/FX512 and the imported EH frame/RET geometry. Extend current literal source descriptors and physical owning IAT provenance, not the isolated machine snapshot. `Session::enter` currently requires a registration callback, so this nonregistering root needs an explicit Runtime translation/caller boundary analogous to existing nonregistering roots. The cached codepage25 association needs a distinct owned nativeCS40, typed guestCS24 transport, full TLS lifecycle and poison cleanup. The already tested lazy callbacks and foreign codepages remain denied.

Current bounded source/resource/causal gates passed. No chronological MFC original prefix has been captured, no connected native extension is prepared, and no initializer credit is granted by this planning receipt.
'''
 (out/'next-connected-probe.md').write_text(note);pin(out/'connected-domain-gap.json');pin(out/'next-connected-probe.md');pin(__file__);pin(sys.executable)
 for p,h in pins.items():assert sha(p)==h
 report=dict(passed=True,scope='Read-only exact current130→131 gap audit; physical new slot/order and source/resource boundaries, no archive or predicted credit',facts=str(out/'connected-domain-gap.json'),plan=str(out/'next-connected-probe.md'),files=pins,capture_archive_reader_opened=False,genuine_connected_prefix_pending=True,native_extension_pending=True,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
