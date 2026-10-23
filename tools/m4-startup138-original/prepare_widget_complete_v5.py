"""Parameterize exact current ordinary observations for literal 42-root replay."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2];OLD='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(validation_path,validation_hash,name):
 validation_path=Path(validation_path).resolve();assert validation_path.parent.parent==R/'reports/m4-startup138-original';assert sha(validation_path)==validation_hash
 validation=json.loads(validation_path.read_text());assert validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['counts']['phases']==828 and validation['callbacks']==108 and validation['combined_pages']==69 and validation['counts']['actual_HeapReAlloc_initial_full_backing_witnesses']>=12
 assert validation['build_sha256']=='da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'
 base=Path(__file__).with_name('compare_widget_source_v4.py');text=base.read_text();changes=[]
 def one(old,new,count=1):
  nonlocal text
  assert text.count(old)==count,(old[:90],text.count(old));start=0
  for _ in range(count):
   pos=text.index(old,start);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):];start=pos+len(new)
 one('original-validation-r2',validation_path.parent.name);one(OLD,validation_hash,2)
 one("F=load(R/'tools/m4-formatting-source/flag_domain.py','widget_flag_definedness')", "F=load(R/'tools/m4-formatting-source/flag_domain.py','widget_flag_definedness');FONT=load(R/'tools/m4-startup138-original/font_source_generations.py','current_source_font_generations');font_generation=None")
 one("(0x780012ab,0x7802e048):(6,1)}", "(0x780012ab,0x7802e048):(6,1),(0x78011c27,0x7802e0b4):(3,4)}")
 one("stem=f'phase/{seq}/{phase}/';record=", "if phase==15:font_generation=FONT.Generations(seq)\n            stem=f'phase/{seq}/{phase}/';record=")
 one("memory[registry[0]]=bytearray(backing)", "memory[registry[0]]=bytearray(backing);registry_capacity=[registry[2]];reallocation_inputs=[]")
 one("                def step(self):", "                def write(self,address,value,size=4,domain='source',pc=None):\n                    original_pc=self.word(2472)if pc is None else pc;result=super().write(address,value,size,domain,pc);font_generation.store(self,original_pc,address,value,size,domain);return result\n                def step(self):")
 one("'stosd':('DF',)", "'stosd':('DF',),'jb':('CF',),'jae':('CF',),'ja':('CF','ZF'),'jbe':('CF','ZF'), 'jg':('ZF','SF','OF'), 'jo':('OF',), 'jno':('OF',)")
 one("need(kind in(2,5,6)and target==provider_targets[kind],'Finite warm registrar APIs only; allocation/growth requires independent owned witnesses');n=3 if kind==2 else 1", "need(kind in(2,3,5,6)and target==provider_targets[kind],'Exact finite named registrar APIs including measured realloc birth');n=4 if kind==3 else 3 if kind==2 else 1")
 one("{2:0x7802e1dc,5:0x7802e044,6:0x7802e048}", "{2:0x7802e1dc,3:0x7802e0b4,5:0x7802e044,6:0x7802e048}")
 one("and w[10]==registry[2],'Own current registry bounded HeapSize witness')", "and w[10]==registry_capacity[0],'Own current registry bounded HeapSize witness')")
 anchor="                    model.api_return(site,n,w[10]);model.reg('ecx',w[11]);model.reg('edx',w[12])"
 new="""                    if kind==3:
                        old_begin=u(model.bytes(0x7803788c,4))[0];old_next=u(model.bytes(0x78037888,4))[0];old_owned=model.bytes(old_begin,registry_capacity[0]);need(w[20]==u(model.bytes(0x78035000,4))[0]and w[21]==0 and w[22]==old_begin and old_begin<=old_next<=old_begin+registry_capacity[0]and w[23]==((registry_capacity[0]+16+15)&~15),'Literal own registry realloc request, heap, pointer and source mode1 rounding');need(w[10]and w[25]==0x78011c2d,'Current observed successful exact realloc source return')
                        ai=provider_index[0];birth_size=u(capture(stem+f'api-initial/{ai}/size.bin'))[0];birth=capture(stem+f'api-initial/{ai}/bytes.bin');need(len(birth)==birth_size and w[23]<=birth_size<=1024 and birth[:len(old_owned)]==old_owned,'Full actual API-produced reallocation backing, exact complete source-owned old prefix; tail exclusively API-return witness')
                        need(old_begin in model.memory and bytes(model.memory[old_begin])==old_owned,'One complete privately mapped old registry region');del model.memory[old_begin];need(w[10]not in model.memory,'Fresh or same-address registry allocation does not alias a different source region');model.memory[w[10]]=bytearray(birth);registry_capacity[0]=birth_size
                        reallocation_inputs.append(dict(API_index=ai,source_CALL_pc=site,source_frame=w[4],source_return_word=w[25],old_begin=old_begin,old_next=old_next,requested=w[23],actual_pointer=w[10],API_return_capacity=birth_size,API_initial_backing_sha256=hashlib.sha256(birth).hexdigest(),complete_old_prefix_source_derived=True,AFTER_endpoint_seed=False));counts['literal_registry_reallocation_births']+=1
"""
 one(anchor,new+anchor)
 one("model.api_return(site,argc[api],ac[0]);model.reg('ecx',ac[1]);model.reg('edx',ac[2])", "font_generation.gdi(model,before,after,phase,root['entry']);model.api_return(site,argc[api],ac[0]);model.reg('ecx',ac[1]);model.reg('edx',ac[2])")
 old="actual_registry=u(record,356464,4);need(actual_registry==(registry[0],registry[1]+4,registry[2],registry[3]),'Actual warm one-callback registry endpoint');eq(machine.bytes(registry[0],registry[2]),record[356480:356480+registry[2]],'Whole source-derived own registry backing AFTER');need(u(machine.bytes(registry[1],4))[0]==root['registration']['callback'],'Own literal ordered callback appended')"
 new="actual_registry=u(record,356464,4);source_begin=u(machine.bytes(0x7803788c,4))[0];source_next=u(machine.bytes(0x78037888,4))[0];source_mode=u(machine.bytes(0x78035004,4))[0];need(actual_registry==(source_begin,source_next,registry_capacity[0],source_mode)and source_next-source_begin==registry[1]-registry[0]+4 and source_mode==registry[3],'Actual full registry metadata equals source-derived begin/next/capacity/mode');eq(machine.bytes(source_begin,registry_capacity[0]),record[356480:356480+registry_capacity[0]],'Whole source-derived own registry backing AFTER');need(u(machine.bytes(source_next-4,4))[0]==root['registration']['callback'],'Own literal ordered callback appended');font_generation.phase(capture(stem+'widget-resources.bin'));counts['source_font_resource_phase_joins']+=1"
 one(old,new)
 one("machine.end_widget();results.append", "machine.end_widget()\n            if phase==136:\n                resource_result=font_generation.cleanup(capture(f'cleanup/{seq}/resources.bin'),lambda i:capture(f'cleanup/{seq}/owned-font/{i}.bin'),lifetimes);source_fonts.extend(font_generation.created);cleanup_rows.append(dict(sequence=seq,**resource_result));counts['source_owned_font_generations']+=resource_result['source_generations'];counts['source_owned_font_stores']+=resource_result['source_owned_stores'];counts['source_font_cleanup_sequence_joins']+=1\n            results.append")
 one("provider_API_joins=provider_joins", "provider_API_joins=provider_joins,source_registry_reallocation_inputs=reallocation_inputs")
 one("'Exact complete observed normal prefix extent');passed=True", "'Exact complete observed normal prefix extent');need(counts['literal_registry_reallocation_births']==12 and counts['literal_complete_registrar_root_endpoints']==42 and counts['source_font_resource_phase_joins']==42 and counts['source_owned_font_generations']==counts['source_owned_font_stores']==90 and counts['source_font_cleanup_sequence_joins']==6,'Complete current finite source birth/font/root extent');passed=True")
 one("('literal-FPS-joins.json',FPS_joins)", "('source-font-generations.json',source_fonts),('source-font-cleanup-joins.json',cleanup_rows),('literal-FPS-joins.json',FPS_joins)")
 one("scope='Current138 six-sequence literal seven-root widget/font/fps registration prefixes", "scope='Current138 six-sequence literal seven-root complete registrar endpoints with typed actual realloc birth backing and source font generation/store/resource/manualcleanup joins")
 one("complete_current_widget_gate=False,registration_provider69_endpoint_frontier=not passed", "complete_current_widget_gate=False,finite_current42_widget_source_relations_passed=passed,full_acceptance_requires_independent_policy_review=True,registration_provider69_endpoint_frontier=not passed")
 reverse=text
 for d in reversed(changes):
  p=d['position'];assert reverse[p:p+len(d['new'])]==d['new'];reverse=reverse[:p]+d['old']+reverse[p+len(d['new']):]
 assert reverse==base.read_text();ast.parse(text);target=base.with_name('compare_widget_complete_v5.py');assert not target.exists();target.write_text(text)
 out=R/'reports/m4-startup138-original'/name;assert not out.exists();out.mkdir();pins=[base,target,Path(__file__),validation_path,R/'tools/m4-startup138-original/font_source_generations.py',R/'reports/m4-startup138-original/font-source-generation-preparation-r1/report.json']
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Unexecuted exact current42-root ordinary-export-only source adapter',exact_reverse_restores_parent_v4=True,changes=changes,validation_path=str(validation_path),validation_sha256=validation_hash,entrypoint=str(target),archive_reader_opened=False,source_executed=False,AFTER_seed=False,complete_current_widget_gate=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in pins}),indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
