"""Current source-record terminal writer joins and bounded adverse policy checks."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def artifact(report,label):
  p=report.parent/label;return json.loads(pin(p,json.loads(report.read_bytes())['files'][str(p.resolve())]).read_bytes())
 original_report=pin(R/'reports/m4-startup138-original/widget-complete-source-r1/report.json','4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684');native_report=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052')
 originals=artifact(original_report,'source-derivations.json');natives=artifact(native_report,'Widget-source-derivations.json');assert len(originals)==42 and len(natives)==84
 pc=pin(R/'reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json','7e1095cb13aef3450991ef577b23de0b6daed874e85e02d2b375543b607e21e7');instruction=next(v for v in json.loads(pc.read_bytes())['instructions']if v['pc']==0x5a0645);assert instruction['bytes_hex']=='c7865802000000000000'and instruction['operands']=='dword ptr [esi + 0x258], 0x0'
 helper=pin(R/'tools/m4-startup138-paired/widget_relations_v8.py','7f9a38687815fd5e74330a2fb04d2dce1d4d3933912cd20c00aa21b882f3caff');spec=importlib.util.spec_from_file_location('widget_terminal_definition',helper);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 relations=[];adverses=[];fields=clears=births=0
 for native in natives:
  original=next(v for v in originals if v['sequence']==native['sequence']and v['root']==native['root']);row=M.compare_root(original,native);relations.append(row);fields+=len(row['terminal_handle_field_source_writers']);clears+=sum(v['source_zero_clear']for v in row['terminal_handle_field_source_writers']);births+=len(row['typed_handle_source_stores'])
  phase=original['phase'];policy=M.HandleFieldPolicy();policy.activate(row,phase)
  for terminal in row['terminal_handle_field_source_writers']:
   page=terminal['address']&~4095;offset=terminal['address']&4095;a=bytearray(4096);b=bytearray(4096)
   for t in row['terminal_handle_field_source_writers']:
    if t['address']&~4095==page:
     o=t['address']&4095;a[o:o+4]=t['original'].to_bytes(4,'little');b[o:o+4]=t['native'].to_bytes(4,'little')
   assert offset in policy.page(phase,'after',page,a,b)
   for branch in('original','native'):
    aa=bytearray(a);bb=bytearray(b);(aa if branch=='original'else bb)[offset]^=1
    try:policy.page(phase,'after',page,aa,bb)
    except ValueError:adverses.append(dict(root=row['root'],level=row['level'],sequence=row['sequence'],address=terminal['address'],kind=branch+'-endpoint-byte'))
    else:raise AssertionError('Corrupt own terminal field admitted')
  clear=next((v for v in row['terminal_handle_field_source_writers']if v['source_zero_clear']),None)
  if clear:
   for label in('clear-value','clear-PC','partial-width'):
    oa=copy.deepcopy(original);na=copy.deepcopy(native);i=clear['source_access_index']
    for x in(oa,na):
     if label=='clear-value':x['source_accesses'][i][2]=1
     elif label=='clear-PC':x['source_accesses'][i][0]^=1
     else:x['source_accesses'][i][3]=1
    try:M.compare_root(oa,na)
    except ValueError:adverses.append(dict(root=row['root'],level=row['level'],sequence=row['sequence'],kind=label))
    else:raise AssertionError('Invalid clear source admitted')
 assert fields and clears and len(relations)==84
 p=out/'source-terminal-relations.json';p.write_text(json.dumps(relations,indent=2)+'\n');pin(p);pin(__file__)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All84 current source-derived terminal handle writer joins; synthetic exact endpoint/clear adverses only',source_cases=84,terminal_fields=fields,source_zero_terminal_fields=clears,API_birth_store_joins=births,adverses=adverses,literal_zero_clear_instruction=instruction,full_raw_endpoints_reviewed=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,independent_admission=False,files=pins),indent=2)+'\n');print(json.dumps(dict(sha256=sha(q),fields=fields,clears=clears,adverses=len(adverses))))
if __name__=='__main__':main(sys.argv[1])
