"""Additive109 paired policy, preserving all accepted103 raw relation limits."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];t=(ROOT/'tools/m4-mfc-source/compare_paired_policy_v2.py').read_text()
def change(a,b):
 global t
 assert t.count(a)==1,a
 t=t.replace(a,b)
t=t.replace('selected103','selected109').replace('native103','native109').replace('original103','original109').replace('paired103','paired109')
change("out=ROOT/'reports/m4-mfc-source'/name","out=ROOT/'reports/m4-fs-source'/name")
change("ROOT/'reports/m4-mfc-source/original-run-r3/report.json','a50819520282272712899cb64faedd8d568c08a22d6d25e65fbc18358571faa0'","ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4'")
change("ROOT/'reports/m4-mfc-source/original-game-source-r1/report.json','0759e9c4f7423a8695bc4feb993998734c3c4e2dcea16d079f2e6a84feb6a958'","ROOT/'reports/m4-fs-source/original-game-source-r4/report.json','e81470844c869f8d31d4995a150a3c689990321710010faeff0550a568029001'")
change("ROOT/'reports/m4-mfc-source/connected-native-source-r1/report.json'","ROOT/'reports/m4-fs-source/connected-native-source-r1/report.json'")
change("+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes());roots=","+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots=")
change("ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json'","ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json'")
change("need(len(MFC_IMPORTS)==511,'All physical/authenticated original MFC import slots')","""need(len(MFC_IMPORTS)==511,'All physical/authenticated original MFC import slots')
  fsbindings=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());original_fs_headers=json.loads(pin(ROOT/'reports/m4-fs-source/original-game-source-r4/new-header-derivations.json').read_bytes());native_fs_headers=json.loads(pin(ROOT/'reports/m4-fs-source/connected-native-source-r1/new-header-derivations.json').read_bytes())""")
change("live_mfc_fields={};live_header_fields={}","live_mfc_fields={};live_header_fields={};live_fs_fields={}")
change("need(len(mfc_records)==35,'35 exact native allocation owners')","need(len(mfc_records)==45,'45 exact native allocation owners')")
change("for address,pair in live_mfc_fields.items():","""if side=='after':
        for fi,binding in enumerate(fsbindings):
         address=binding['publication']
         if binding['root']!=entry or not address or address&~4095!=page:continue
         meta=words(ori.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/meta.bin'),0,9);record=next(w for w in mfc_records if w[2]==entry and w[4]==binding['CALL_pc']);need(meta[:5]==(1,fi,entry,binding['CALL_pc'],binding['requested_size'])and meta[7]and meta[8]>=binding['requested_size'],'Original dynamic FS source allocation join');need(record[7]==binding['requested_size']and record[21]and record[16]and record[17]and record[18],'Native dynamic FS source allocation join');live_fs_fields[address]=(meta[7],record[16]);counts['new_FS_static_publication_relations']+=1
        if entry==0x4d4830 and page==0x60b000:
         ar=next(r for r in original_fs_headers if r['sequence']==seq);br=next(r for r in native_fs_headers if r['sequence']==seq and r['level']==level);need(ar['field']==br['field']==0x60b51c and ar['write_pc']==br['write_pc']==0x4d4922 and ar['read_pc']==br['read_pc']==0x4d4914 and ar['read_address']==br['read_address']==0x200017eb,'Exact new literal saved-byte field/source PC/address');equal(original[0x51c],ar['value'],'Exact original header from genuine own BEFORE stack byte');equal(actual[0x51c],br['value'],'Exact native header from persistent source own BEFORE stack byte');live_header_fields[0x60b51c]=(ar['value'],br['value']);field_rows.append(dict(level=level,sequence=seq,address=0x60b51c,original_source=ar,native_source=br,new_FS_local_byte_relation=True));counts['new_FS_header_branch_derivations']+=2
       for address,pair in live_fs_fields.items():
        if address&~4095==page:
         off=address&4095;equal(words(original,off)[0],pair[0],'Original carried shared/private FS static publication');equal(words(actual,off)[0],pair[1],'Native carried shared/private FS static publication');declared.update(range(off,off+4));counts['new_FS_static_publication_carries']+=1
       for address,pair in live_mfc_fields.items():""")
change("struct.pack('<75I',*expected_callbacks)","struct.pack('<81I',*expected_callbacks)")
change("def delta(a,b):return [dict(offset=i,original=x,native=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]","def delta(a,b):\n if a==b:return []\n return [dict(offset=i,original=x,native=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]")
change("new_MFC_source_header_relations=True,","new_MFC_source_header_relations=True,new_FS_source_publication_fields=[r['publication']for r in fsbindings if r['publication']],new_FS_header_relation_address=0x60b51c,new_FS_header_relation_scope='Exact own-branch literal local-byte read/write and carry, from genuine original BEFORE stack or persistent native source BEFORE stack. Raw values retained; whole-game liveness not claimed.',")
p=ROOT/'tools/m4-fs-source/compare_paired_policy.py';assert not p.exists();p.write_text(t)
