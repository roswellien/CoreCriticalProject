"""Connected14 admission with physical caller-derived tail-thunk identity."""
from pathlib import Path
import ast
SCRIPTS=Path(__file__).parent
def literal(file,name):
 nodes=ast.parse(file.read_text()).body
 found=[ast.literal_eval(n.value)for n in nodes if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
 assert len(found)==1;return found[0]
BASE=SCRIPTS/'review_mfc1168_connected_native_prefix.py'
V2=SCRIPTS/'review_mfc1168_connected_native_prefix_v2.py'
V3=SCRIPTS/'review_mfc1168_connected_native_prefix_v3.py'
V4=SCRIPTS/'review_mfc1168_connected_native_prefix_v4.py'
text=BASE.read_text()
replacement=literal(V2,'replacement')
replacement=replacement.replace(literal(V3,'old'),literal(V3,'new'))
for n in('mw34_mfc1168_read8','mw34_mfc1168_read16','mw34_mfc1168_read64','mw34_mfc1168_write16','mw34_mfc1168_write64','mw34_mfc1168_missing'):
 assert replacement.count(repr(n)+',')==1;replacement=replacement.replace(repr(n)+',','')
replacement=replacement.replace("    bridge_targets[symbol]=matches_c[0][0]","    TLS_relations(image,raw_c,matches_c[0][1],relocs_c,sections_c)\n    bridge_targets[symbol]=matches_c[0][0]")
missing=r'''
   missing_symbol='mw34_mfc1168_missing';raw_m,rel_m=C.function(symbols_c,sections_c,missing_symbol);thunks=linked_candidates(image,raw_m,rel_m);source_targets=[]
   for body in lift['source_bodies'].values():
    sy,se=C.parse(blob(body['objects'][level]['path'],body['objects'][level]['sha256']));rr,rl=C.function(sy,se,body['symbol']+'_body')
    calls=[r for r in rl if r['symbol']['name']==missing_symbol]
    if not calls:continue
    partial=current_body_matches(rr,rl);assert len(partial)==1
    a,b=partial[0]
    source_targets.extend(a+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',b,r['offset'])[0]for r in calls)
   assert len(source_targets)==6 and len(set(source_targets))==1
   target=source_targets[0];physical=[(a,b)for a,b in thunks if a==target];assert len(physical)==1
   a,b=physical[0];assert len(rel_m)==1 and rel_m[0]['symbol']['name']=='mw34_mfc1168_jump' and a+rel_m[0]['offset']+4+struct.unpack_from('<i',b,rel_m[0]['offset'])[0]==bridge_targets['mw34_mfc1168_jump']
   bridge_targets[missing_symbol]=a;counts['whole_current_typed_bridge_functions']+=1;counts['actual_missing_thunk_source_CALL_targets']+=6
'''
anchor="   for j in lift['source_bodies'].values():"
assert replacement.count(anchor)==1
replacement=replacement.replace(anchor,missing+anchor)
assert text.count(anchor)==1;text=text.replace(anchor,replacement)
text=text.replace("matches=C.linked_candidates(image,raw,relocs);assert len(matches)==1,j['symbol']","matches=current_body_matches(raw,relocs);assert len(matches)==1,j['symbol']")
text=text.replace('C.linked_candidates(', 'linked_candidates(')
text=text.replace("a+r['offset']+4+struct.unpack_from","a+r['offset']+4+(r['type']-4)+struct.unpack_from")
helper=literal(V4,'helper').replace("TLS_names={'?observation","TLS_names={'?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA','?observation")
helper=helper.replace("assert sym['value']==0 and sections[sym['section']]['bytes']==bytes(8)","storage=sections[sym['section']]['bytes'];assert sym['value']==0 and len(storage)in(8,24) and storage==bytes(len(storage)) and storage[:8]==bytes(8)")
extra=literal(V4,'extra').replace("boundary=pin(folder/'connected_hardware_boundary.obj')","boundary=pin(Path(build['workers']['O0']['path']).parent.parent/'connected_hardware_boundary.obj')")
extra=extra.replace("br,brels=C.function(bs,bsec,'mfc_connected_hardware_call')","labels=[s for s in bs.values()if s['name']=='mfc_connected_hardware_call'];assert len(labels)==1 and labels[0]['section']==1 and labels[0]['value']==0 and bsec[1]['flags']&0x20000000;br,brels=bsec[1]['bytes'],bsec[1]['relocations']")
inside=literal(V4,'inside')
changes=[
 ("'1f8fac0b491ee99e39a966bf2c03e5059e7f541d2d5ed862c9310b8be1b304ba'","'7f426089ae1c974d4e2b5c3e5500efe283d8634a54e6d934a428710fe078d309'"),
 ("'278be74db3998e7396ba46696a59f5e6fbd9acc43f71e0ca1eaedd272822ce4f'","'a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924'"),
 ('connected-fixture-build-r1/build.json','connected-fixture-build-r2/build.json'),
 ("  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')","  N=module(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','mfc_prefix_boundary')\n"+helper+extra+"  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')"),
 ("   db=pin(bf/'.ninja_deps')",inside+"   db=pin(bf/'.ninja_deps')"),
 ("     links.append(dict(level=level,symbol=candidates[0]","     TLS_relations(image,raw,matches[0][1],relocs,sections)\n     links.append(dict(level=level,symbol=candidates[0]"),
 ("  pin(R/'tools/m4-mfc1168-native/run_connected_fixture.py')","  pin(BASE);pin(V2);pin(V3);pin(V4);pin(R/'tools/m4-mfc1168-native/run_connected_fixture.py')"),
 ('whole_new_manager_CRT_TIB_endpoint_observations=False','whole_new_manager_CRT_TIB_endpoint_observations_declared=True')
]
for a,b in changes:assert text.count(a)==1,a;text=text.replace(a,b)
exec(compile(text,str(BASE),'exec'),globals())
