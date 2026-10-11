"""Additive preparation of the literal124 persistent native source comparer."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True)
 old=ROOT/'tools/m4-next-source/compare_connected_v7.py';s=old.read_text()
 s=one(s,'selected120 native roots.','selected124 native roots.')
 s=one(s,"import provider_capture as C","import capture as C\nimport responses as R\n# Reuse the frozen bootstrap implementation with the additive typed API class.\nB.R=R")
 s=one(s,'0x5fc000)','0x5fc000,0x7810a000,0x78145000,0x78146000)')
 s=s.replace("reports/m4-next-source'/name","reports/m4-lockit-source'/name")
 s=s.replace('native120','native124').replace('persistent120_sequences','persistent124_sequences')
 s=one(s,"ROOT/'tools/m4-next-source/game_model.py');D=", "ROOT/'tools/m4-lockit-source/game_model.py');D=")
 anchor="mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())"
 s=one(s,anchor,anchor+"\n  cp=PE.PEImage(provider);prep=pin(ROOT/'reports/m4-lockit-native/preparation-r3/report.json','4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d');prep_data=json.loads(prep.read_bytes());loaded_RW=pin(prep_data['loaded_input_page'],prep_data['loaded_input_page_sha256']).read_bytes();loaded_IAT=pin(prep_data['loaded_IAT_page'],prep_data['loaded_IAT_page_sha256']).read_bytes();pin(prep_data['loaded_original_bootstrap_report'],prep_data['loaded_original_bootstrap_sha256']);need(len(loaded_RW)==len(loaded_IAT)==4096 and int.from_bytes(loaded_RW[0x658:0x65c],'little')==2,'Complete actual original postDllMain input domain')")
 s=one(s,"   if p==0x5f4cc000:","   if p==0x78145000:return loaded_RW\n   if p==0x78146000:return loaded_IAT\n   if p==0x7810a000:\n    result=bytearray(4096)\n    for sec in cp.sections:\n     lo=max(p,cp.image_base+sec['virtual_address']);hi=min(p+4096,cp.image_base+sec['virtual_address']+sec['raw_size'])\n     if hi>lo:offset=sec['raw_offset']+lo-cp.image_base-sec['virtual_address'];result[lo-p:hi-p]=provider[offset:offset+hi-lo]\n    return bytes(result)\n   if p==0x5f4cc000:")
 s=one(s,"ROOT/'reports/m4-vtable-original/validation-r1/report.json'","ROOT/'reports/m4-lockit-original/original-validation-r2/report.json','4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3'")
 s=one(s,"fixed-roots.json').read_bytes());roots=","fixed-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/lockit-roots.json').read_bytes());roots=")
 s=one(s,"  order=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order']","  order=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==124,'Exact selected124 rooted table order')")
 s=one(s,"  for level in ('O0','O2'):","  for f in json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/FS-frame-contracts.json').read_bytes()):\n   for k,kind in(('read',0),('install',1),('restore',2)):FS_SPECS[f[k]]=(kind,f['entry'],f['handler'])\n  FS_READ_BIAS={0x4125a0:0,0x500cd0:0}\n  for level in ('O0','O2'):")
 s=one(s,"entry_ESP=model.reg('esp')+8 if kind==0 else None","entry_ESP=model.reg('esp')+FS_READ_BIAS.get(pc,8) if kind==0 else None")
 anchor="     machine,responses=B.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp)"
 s=one(s,anchor,anchor+"\n     resource=a.words(stem+'lockit-resource.bin',8,'Q');image_raw=a.data(stem+'lockit-native-images.bin');need(len(image_raw)==320,'Exactly eight genuine native CS40 images');images=[image_raw[n:n+40]for n in range(0,len(image_raw),40)];responses.associate_lockit(machine,resource,images,loaded_RW[0x640:0x658]);counts['actual_native_CS_resource_associations']+=1\n     for suffix in ('before','after'):\n      association=C.checkpoint(a,checkpoint_index,'lockit-resource-association-'+suffix);equal(bytes(machine.state),association['state'],'Explicit resource association preserves whole guest State');equal(machine.cpu,association['cpu'],'Explicit resource association preserves whole guest CPU');equal(machine.fx,association['fx'],'Explicit resource association preserves whole guest FX')\n      for page in PAGES:\n       if page in association['memory']:equal(machine.bytes(page,4096),association['memory'][page],'Explicit resource association preserves entire source page'+hex(page))")
 s=one(s,'oracle=o[166116:329956]','oracle=o[178404:354532]')
 s=one(s,'original_before=o[2276:166116]','original_before=o[2276:178404]')
 s=one(s,"need(len(expected_callbacks)==92,'All92 actual callback registrations carried');need(len(fs_observations)==45,'All45 normal game FS source accesses from one bootstrap BEFORE')","need(len(expected_callbacks)==96,'All96 actual callback registrations carried');responses.lockit_complete();need(len(machine.lockit_import_proofs)==8 and len(machine.lockit_state_reads)==8,'All eight literal owning imports and authentic state reads');lockit_rows.append(dict(level=level,sequence=seq,imports=machine.lockit_import_proofs,state_reads=machine.lockit_state_reads,API_relations=responses.lockit_relations));counts['literal_Lockit_CALL_RET_pairs']+=8;counts['actual_native_CS40_source_API_relations']+=8;need(len(fs_observations)==57,'All57 normal game FS source accesses from one bootstrap BEFORE')")
 s=one(s,"len(fsframes)==15 and len(rawrecords)==30,'Actual15 normal game frames and30 complete12B snapshots'","len(fsframes)==19 and len(rawrecords)==38,'Actual19 normal game frames and38 complete12B snapshots'")
 s=one(s,"index==15,'All normal nested game frames close'","index==19,'All normal nested game frames close'")
 s=one(s,'indirect_rows=[]','indirect_rows=[];lockit_rows=[]')
 s=one(s,'finally:a.close();del a','finally:a.close();a.entries.clear();a.bundles.clear();del a')
 s=one(s,'ori.close();pin(__file__)','ori.close();ori.entries.clear();ori.bundles.clear();pin(__file__)')
 s=one(s,"('indirect-source-derivations.json',indirect_rows)","('indirect-source-derivations.json',indirect_rows),('Lockit-source-derivations.json',lockit_rows)")
 s=one(s,'entire40pages','entire43pages')
 s=one(s,"initializer_credit=False,whole_M4_complete=False,files=PINS","initializer_credit=False,whole_M4_complete=False,loaded_state2_source_input=True,native_CS40_opaque_copy=False,guest_CS24_semantic_output=True,native_DllMain_credit=False,files=PINS")
 target=ROOT/'tools/m4-lockit-source/compare_connected.py';assert not target.exists();target.write_text(s)
 files={str(p.resolve()):sha(p)for p in(old,target,Path(__file__),ROOT/'tools/m4-lockit-source/capture.py',ROOT/'tools/m4-lockit-source/responses.py',ROOT/'tools/m4-lockit-source/game_model.py')}
 report=dict(passed=True,scope='Unexecuted additive comparer preparation; frozen source computation remains independent of candidate State/pages/guards',comparer=str(target),files=files,native_compared=False,initializer_credit=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),comparer=str(target))))
if __name__=='__main__':main(sys.argv[1])
