"""Correct Runtime evidence to whole contiguous PE spans; preserve executable code."""
from pathlib import Path
import hashlib, json, struct
R=Path(__file__).resolve().parents[2]
previous=R/'tools/m4-widget-native/prepare_fixture_v8.py'
s=previous.read_text()
for old,new in [('reports/m4-widget-native/preparation-r2','reports/m4-widget-native/preparation-r3'),('775828a192f57bf6e8fcf75fe629461402c7b8c367220f76ed9883c76c6f75b8','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5'),('reports/m4-widget-native/build-r4','reports/m4-widget-native/build-r5'),('ad9d4d5345d01429ff749bfabb9cce1e9cb6ff1d0b87716601083fa1a0c7d56c','9c053306dbf44a3a65ac1945dd4c2b0949ef064842004e05bf2e6cc29a22fada')]:s=s.replace(old,new)
s=s.replace('import hashlib,json,shutil,sys','import hashlib,json,shutil,sys,struct')
s=s.replace('Path(__file__).resolve()]:bind(p)',"previous,R/'tools/m4-widget-native/prepare_fixture_v9.py',Path(__file__).resolve()]:bind(p)")
old=''' for root in component['roots']:
  key=f'f_{root:x}';row=widget['source_bodies'].get(key,remaining['source_bodies'].get(key));need(row and row['entry']==root,'Exact six literal source root spans');h.append('{%d,%d,"%s",mw34::m4_widget_native::Component::entry_%x},'%(root,row['source_bytes'],row['source_sha256'],root))
'''
new=''' game=bind('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');raw=game.read_bytes()
 contract_path=bind('reports/m4-widget-native/preparation-r3/contracts.json',component['files'][str((R/'reports/m4-widget-native/preparation-r3/contracts.json').resolve())]);contracts=json.loads(contract_path.read_bytes())
 pe=struct.unpack_from('<I',raw,0x3c)[0];need(raw[pe:pe+4]==b'PE\\0\\0','Physical PE signature');nsec=struct.unpack_from('<H',raw,pe+6)[0];optlen=struct.unpack_from('<H',raw,pe+20)[0];base=struct.unpack_from('<I',raw,pe+24+28)[0];section_start=pe+24+optlen
 sections=[]
 for i in range(nsec):
  off=section_start+40*i;name=raw[off:off+8].split(b'\\0')[0].decode('ascii');vs,rva,size,fo=struct.unpack_from('<4I',raw,off+8);flags=struct.unpack_from('<I',raw,off+36)[0];sections.append((name,base+rva,size,fo,flags))
 def physical(pc,size):
  owners=[q for q in sections if q[1]<=pc and pc+size<=q[1]+q[2]];need(len(owners)==1,'One file-backed physical PE span');q=owners[0];off=q[3]+pc-q[1];data=raw[off:off+size];need(len(data)==size and q[4]&0x20000000,'Complete executable file-backed source');return data,off,q[0]
 instruction_proofs=[]
 for row in contracts['instructions']:
  expected=bytes.fromhex(row['bytes_hex']);need(len(expected)==row['width'],'Exact declared instruction width');actual,fo,sec=physical(row['pc'],len(expected));need(actual==expected,'Every lifted instruction remains physical source');instruction_proofs.append(dict(pc=row['pc'],bytes_hex=actual.hex(),file_offset=fo,section=sec))
 need(len(instruction_proofs)==1093 and len({q['pc']for q in instruction_proofs})==1093,'All 1093 unique lifted physical instructions')
 spans=[]
 for root in component['roots']:
  rows=[q for q in contracts['roots']if q['root']==root];need(len(rows)==1,'One exact root contract');reg=rows[0]['registration'];ret=reg['return_PC']+3;need(reg['return_PC']==reg['CALL_pc']+5 and reg['push_PC']+5==reg['CALL_pc'],'Literal registration sequence addresses')
  tail,_,_=physical(reg['return_PC'],4);need(tail==bytes.fromhex('83c404c3'),'Literal source final ADD ESP,4; RET');size=ret+1-root;data,fo,sec=physical(root,size);digest=hashlib.sha256(data).hexdigest();key=f'f_{root:x}';prior=widget['source_bodies'].get(key,remaining['source_bodies'].get(key));need(prior and prior['entry']==root,'One original lifted root body')
  spans.append(dict(root=root,begin=root,end_exclusive=root+size,bytes=size,sha256=digest,bytes_hex=data.hex(),file_offset=fo,section=sec,final_RET=ret,registration_CALL=reg['CALL_pc'],recovered_collection_bytes=prior['source_bytes'],recovered_collection_sha256=prior['source_sha256'],Runtime_evidence_domain='whole contiguous source span including original padding'))
  h.append('{%d,%d,"%s",mw34::m4_widget_native::Component::entry_%x},'%(root,size,digest,root))
 (out/'contiguous-registration-spans.json').write_text(json.dumps(dict(game_path=str(game),game_sha256=sha(game),spans=spans,instruction_proofs=instruction_proofs,whole_contiguous_spans=6,lifted_physical_instructions=1093,no_source_bytes_changed=True),indent=2)+'\\n')
'''
if s.count(old)!=1:raise RuntimeError('One exact failed binding generation block')
s=s.replace(old,new)
s=s.replace("'native_executed':False,'initializer_credit':0}","'native_executed':False,'initializer_credit':0,'Runtime_evidence_whole_contiguous_spans':6,'all_lifted_physical_instructions_checked':1093,'fixture_code_changed':False,'component_code_changed':False}")
exec(compile(s,str(previous),'exec'),globals())
