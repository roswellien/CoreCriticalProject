"""All48 actual source-record partitions with physical PE ownership and adverses."""
from pathlib import Path
import copy,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def artifact(report,leaf):
  p=report.parent/leaf;return read(p,json.loads(report.read_bytes())['files'][str(p.resolve())])
 def load(n,p):
  p=pin(p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 M=load('format_static_definition',R/'tools/m4-startup138-paired/format_relations_v4.py');PE=load('actual_PE_definition',R/'tools/analysis/pe.py');game_path=pin(R/'MW3/Mech3.exe',M.GAME_IMAGE_SHA256);game=PE.PEImage(game_path.read_bytes());ranges=tuple((game.image_base+s['virtual_address'],game.image_base+s['virtual_address']+max(s['virtual_size'],s['raw_size']))for s in game.sections);assert ranges==M.GAME_SECTION_RANGES
 crt_path=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');crt=PE.PEImage(crt_path.read_bytes());off=crt.rva_range(0x78004a69-crt.image_base,7)[0];assert crt.data[off:off+7]==bytes.fromhex('83058878037804')
 for pc,raw in [(0x7801e2aa,'a38c780378'),(0x7801e2b5,'890d88780378'),(0x78011c27,'ff15b4e00278')]:
  off=crt.rva_range(pc-crt.image_base,len(bytes.fromhex(raw)))[0];assert crt.data[off:off+len(bytes.fromhex(raw))]==bytes.fromhex(raw)
 off=crt.rva_range(0x7802e0b4-crt.image_base,4)[0];assert struct.unpack_from('<I',crt.data,off)[0]==0x3464a
 cp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r11/policy-preparation.json');policy=json.loads(cp.read_bytes());domains=read(policy['CRT_page_source_domains_path'],policy['CRT_page_source_domains_sha256']);pages=set(policy['additional_whole_page_addresses'])|{0x60b000,0x20001000,0x78037000,0x78145000};callbacks=dict(zip(M.ROOTS,(0x4df680,0x4e07b0,0x4e0850,0x4e1ce0)))
 combined=pin(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4');native=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');originals=artifact(combined,'original-Formatting-source-derivations.json');natives=artifact(native,'Formatting-source-derivations.json');assert len(originals)==24 and len(natives)==48
 # Actual policy69 page order, not a test-specific approximation.
 import ast
 comparer=pin(R/'reports/m4-startup138-paired/comparer-preparation-r11/paired138.py');tree=ast.parse(comparer.read_text());fixed=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PAGES'for t in n.targets));pages=fixed+tuple(policy['additional_whole_page_addresses']);assert len(pages)==69
 rows=[];adverses=[]
 for source in natives:
  original=next(v for v in originals if v['sequence']==source['sequence']and v['root']==source['root']);case=next(v for v in domains if v['sequence']==source['sequence']and v['level']==source['level']);domain=dict(case['registry_fields'][source['phase']],callback=callbacks[source['root']]);oa=[M.original_owner(original['owner'])]+[M.original_owner(v)for v in original.get('mixed_owners',[])];na=[M.native_owner(source['owner'])]+[M.native_owner(v)for v in source.get('mixed_owners',[])];aw,ap=M.partition_static(original,oa,pages);bw,bp=M.partition_static(source,na,pages,domain);assert not ap and len(bp)==(3 if source['root']==0x4e1ca0 else 1) and [(r[0],r[1],r[3])for r in aw]==[(r[0],r[1],r[3])for r in bw]
  # Bind actual callback source PUSH to physical immediate bytes, not output-only metadata.
  pushes=[v for v in source['source_accesses']if v[4]and v[3]==4 and v[2]==domain['callback']and 0x20001000<=v[1]<0x20002000 and any(begin<=v[0]<end for begin,end in ranges)];literal=pushes[0];off=game.rva_range(literal[0]-game.image_base,5)[0];assert game.data[off:off+5]==b'\x68'+struct.pack('<I',domain['callback'])
  rows.append(dict(level=source['level'],sequence=source['sequence'],phase=source['phase'],root=source['root'],game_static_source_rows=len(aw),separate_registrar_source_joins=bp,physical_callback_PUSH_PC=literal[0],current_own_registry_source_domain=domain))
  index=bp[-1]['source_access_index']
  for label in('wrong-PC','wrong-address','wrong-width','wrong-value','nonprovider-outside-game','missing-provider','wrong-callback','wrong-phase'):
   wrong=copy.deepcopy(source);wd=dict(domain)
   if label=='wrong-PC':wrong['source_accesses'][index][0]^=1
   elif label=='wrong-address':wrong['source_accesses'][index][1]+=4
   elif label=='wrong-width':wrong['source_accesses'][index][3]=1
   elif label=='wrong-value':wrong['source_accesses'][index][2]^=1
   elif label=='nonprovider-outside-game':wrong['source_accesses'].append([source['root'],0x78145004,0,4,1])
   elif label=='missing-provider':wrong['source_accesses'].pop(index)
   elif label=='wrong-callback':wd['callback']^=1
   else:wd['phase']+=1
   try:M.partition_static(wrong,na,pages,wd)
   except ValueError:adverses.append(dict(level=source['level'],sequence=source['sequence'],root=source['root'],kind=label))
   else:raise AssertionError(label)
  if source['root']==0x4e1ca0:
   for provider in bp[:2]:
    for label in('growth-PC','growth-address','growth-width','growth-value'):
     wrong=copy.deepcopy(source);i=provider['source_access_index']
     if label=='growth-PC':wrong['source_accesses'][i][0]^=1
     elif label=='growth-address':wrong['source_accesses'][i][1]+=4
     elif label=='growth-width':wrong['source_accesses'][i][3]=1
     else:wrong['source_accesses'][i][2]^=1
     try:M.partition_static(wrong,na,pages,domain)
     except ValueError:adverses.append(dict(level=source['level'],sequence=source['sequence'],root=source['root'],kind=label))
     else:raise AssertionError(label)
   ci=next(i for i,r in enumerate(source['source_accesses'])if r[0]==0x78011c27 and r[4]);
   for label in('growth-IAT','growth-return'):
    wrong=copy.deepcopy(source);wrong['source_accesses'][ci-1 if label=='growth-IAT'else ci][2]^=1
    try:M.partition_static(wrong,na,pages,domain)
    except ValueError:adverses.append(dict(level=source['level'],sequence=source['sequence'],root=source['root'],kind=label))
    else:raise AssertionError(label)
 assert len(rows)==48 and len(adverses)==504;pin(__file__);p=out/'relations.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current physical Game static module partition; all72 native provider end/growth source rows separately exact typed against own registry source domain',original_source_cases=24,native_source_cases=48,typed_registrar_rows=72,all_game_static_rows_retained=True,all_game_static_order_pairs_equal=True,actual_physical_callback_PUSHes=48,provider_PC=0x78004a69,provider_instruction_hex='83058878037804',physical_Game_ranges=ranges,adverses=adverses,archive_reader_opened=False,raw_export_reader_opened=False,source_interpreter_executed=False,full_CRT_source_execution_reproved=False,whole_pair_run=False,independent_admission=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
