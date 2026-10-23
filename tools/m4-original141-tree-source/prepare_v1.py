"""Finite current141 tree adaptation; preparation only, no input reader."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/preparation-r1';out.mkdir(parents=True);files={};deltas=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;files[str(p)]=v;return p
 parent=pin(R/'tools/m4-startup138-original/tree_source_r5.py');s=parent.read_text(encoding='utf-8')
 def edit(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);deltas.append(dict(old=a,new=b))
 edit('def main(name,model_path,sequence):','def main(name,model_path,sequence,validation_path,validation_sha256):')
 edit("out=ROOT/'reports/m4-startup138-original'/name","out=ROOT/'reports/m4-original141-tree-source'/name")
 edit("validation=read(ROOT/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');need(validation['passed'],'Genuine independently measured prefix')", "validation_path=Path(validation_path).resolve();need(validation_path.parent.parent==ROOT/'reports/m4-original141','Exact original141 strict report namespace');validation=read(validation_path,validation_sha256);need(validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['callbacks']==111,'Genuine independently measured original141 prefix and closed export');need(0<=sequence<6,'Exact six measured original141 cases')")
 old="pages=preparation['observed_pages'];need(len(pages)==43,'Complete accepted page scope')"
 new="need(preparation['root_count']==141 and preparation['phases']==846 and preparation['callback_count']==111 and build['preparation_sha256']=='a54ece9c861485fb2e121bc1733550e0d0ab462199d85de83a2894fc72702b6c','Exact physically compiled current141 source');current_order=read(Path(build['preparation'])/'selected-order.json');retained_pages=read(ROOT/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161');preparation=dict(preparation,selected_order=current_order,observed_pages=retained_pages['observed_pages'],extra_whole_source_pages=retained_pages['extra_whole_source_pages']);pages=preparation['observed_pages'];need(len(pages)==43 and len(set(pages+preparation['extra_whole_source_pages']))==69,'Complete unchanged fixed43/external26 page scope');compiled=read(ROOT/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c');need(compiled['passed'],'Current whole linked observer proof');links=read(ROOT/'reports/m4-original141/root-compiled-review-r2/physical-links.json');resolved={}\n        for row in links:\n            for rel in row['relocations']:\n                if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':\n                    symbol,value=rel['symbol'],rel['actual_symbol_address'];need(symbol not in resolved or resolved[symbol]==value,'Unique current linked symbol');resolved[symbol]=value\n        exact_CS_shims={0x78146198:resolved['_lockit_api_Enter'],0x78146184:resolved['_lockit_api_Leave']}\n        for gate in (validation,preparation,compiled):\n            for dependency,identity in gate['files'].items():pin(dependency,identity)"
 edit(old,new)
 edit("'One authenticated shared current-original138 session'","'One authenticated shared current-original141 ordinary-export session'") if "'One authenticated shared current-original138 session'" in s else edit("'One authenticated shared current-original138 session'".replace('shared ','shared '),"'One authenticated shared current-original141 ordinary-export session'")
 edit("reader=SHARED_READER;need(reader is not None", "reader=SHARED_READER;need(reader is not None and type(reader).__name__=='ExportReader'")
 edit("need(0x18000000<=current<0x19000000,'Authentic x86 API observer cell')","need(current==exact_CS_shims[slot],'Exact current wholly compiled x86 API observer cell')")
 edit("need(tree_phase==83,'Current physical tree slot after FCOS')","need(tree_phase==86 and [preparation['selected_order'][i]['entry']for i in (13,14,39)]==[0x4103f0,0x410440,0x459b40],'Current physical tree slot after exact three constructor insertions')")
 edit("geometry_path=ROOT/'reports/m4-startup138-original/original-validation-r3/allocation-geometry.json'","geometry_path=validation_path.parent/'allocation-geometry.json'")
 edit("current-original138", "current-original141") if s.count("current-original138")==1 else None
 edit("report=dict(passed=passed,scope=", "report=dict(passed=passed,original_validation_sha256=validation_sha256,original_validation_path=str(validation_path),source_case_extent=1,source_AFTER_seed=False,canonical_reader_opened=False,sequence=sequence,scope=")
 old="if __name__=='__main__':main(sys.argv[1],ROOT/(sys.argv[2]if len(sys.argv)>2 else'tools/m4-tree-source/game_model_v4.py'),int(sys.argv[3]))"
 edit(old,"if __name__=='__main__':main(sys.argv[1],ROOT/sys.argv[2],int(sys.argv[3]),Path(sys.argv[4]),sys.argv[5])")
 rev=s
 for d in reversed(deltas):assert rev.count(d['new'])==1;rev=rev.replace(d['new'],d['old'])
 assert rev==parent.read_text(encoding='utf-8');ast.parse(s)
 q=R/'tools/m4-original141-tree-source/tree_source_v1.py';assert not q.exists();q.write_text(s,encoding='utf-8');pin(q)
 pin(R/'tools/m4-tree-source/game_model_v4.py');pin(R/'tools/m4-startup138-original/registry_suffix_v1.py');pin(R/'reports/m4-original141/source-preparation-r6/selected-order.json');pin(__file__)
 p=out/'deltas.json';p.write_text(json.dumps(deltas,indent=2)+'\n',encoding='utf-8');pin(p)
 report=dict(passed=True,prepared_only=True,exact_inverse=True,delta_count=len(deltas),source_instruction_model_unchanged=True,current_tree_phase=86,source_case_extent_required=6,current_strict_export_pass_pending=True,canonical_reader_opened=False,worker_launched=False,accepted_function_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
