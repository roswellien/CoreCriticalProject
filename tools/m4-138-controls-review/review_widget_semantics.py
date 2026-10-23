"""Independent current widget whole program/State/CPU/FX contract review.

This inspects the accepted interpreter and current semantic adapters. It does
not claim another interpreter execution; the producing source6 consumer owns
the independent semantic prediction from its single genuine bootstrap.
"""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary-only review');v=sha(p);need(h is None or v==h,'Whole physical semantic dependency '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable semantic dependency');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=Path(sys.argv[1]).resolve();out=R/'reports/m4-138-controls-review'/sys.argv[3];need(not out.exists(),'Fresh semantics review');out.mkdir(parents=True);passed=False;counts=collections.Counter();joins=[];readers=[]
 try:
  source=read(p,sys.argv[2]);need(sha(p)=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'and source['passed']and source['reader_closed'],'Exact complete source6')
  memory_path=Path(sys.argv[4]).resolve();memory=read(memory_path,sys.argv[5]);need(memory['passed']and memory['source_provider_sha256']==sha(p)and memory['independent_component_memory_byteflow']and memory['independent_raw_identity_equality']and memory['reader_closed'],'Exact independent84 memory/raw-owner review')
  need(memory['counts']['independent_widget_memory_byteflows']==84 and memory['counts']['independently_authenticated_raw_GDI_calls']==1968 and memory['counts']['physically_discriminated_growth_intervals']==24,'Entire independent current widget coverage')
  for q,h in memory['files'].items():pin(q,h)
  parent_path=R/'reports/m4-joint-startup131-root/acceptance-r1/report.json';parent=read(parent_path,'aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061');need(parent['passed']and parent['connected_roots']==131 and parent['explicit_measured_predicates']==841,'Exact accepted131 whole semantic parent')
  def input_path(relative):
   q=(R/relative).resolve();return pin(q,source['files'][str(q)])
  def output(name):
   q=p.parent/name;return read(q,source['files'][str(q.resolve())])
  rows=output('Widget-source-derivations.json');flags=output('Literal-defined-flag-consumers.json')
  gp=input_path('reports/m4-fps-original/source-preparation-r4/game_model.py');GM=load('independent_current_widget_semantics',gp);program,callbacks=GM.source_program()
  contract=read(input_path('reports/m4-onexit-review/interface-r1/instruction-contracts.json'))
  for row in contract['instructions']:
   pc=row['pc']
   if pc in program:need(program[pc]['bytes_hex']==row['bytes_hex']and program[pc]['width']==row['width'],'Identical retained/additive provider bytes and width')
   else:program[pc]=row
  need(GM.I.REG==dict(eax=2216,ecx=2248,edx=2264,ebx=2232,esp=2312,ebp=2328,esi=2280,edi=2296)and GM.I.FLAGS==dict(CF=2065,PF=2067,AF=2069,ZF=2071,SF=2073,DF=2075,OF=2077),'Whole accepted Remill State register/flag offset identity')
  for cls in GM.Machine.__mro__:
   method=cls.__dict__.get('step')
   if method is None:continue
   q=Path(method.__code__.co_filename).resolve();pin(q,source['files'][str(q)])
   if q!=gp:need(parent['files'].get(str(q).casefold())==sha(q),'Whole inherited accepted interpreter semantics byte-identical');counts['whole_unchanged_inherited_interpreter_layers']+=1
  pin(Path(GM.I.__file__).resolve(),source['files'][str(Path(GM.I.__file__).resolve())])
  model=gp.read_text();adapter=input_path('tools/m4-widget-growth-review/persistent_gdi.py');api_code=adapter.read_text();flag_code=input_path('tools/m4-formatting-source/flag_domain.py').read_text();producer=input_path('reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').read_text();association=input_path('tools/m4-joint-startup138/persistent_widgets_v5.py').read_text()
  for marker in ("Any overlapping store invalidates","Same current instance most recent root-specific literal source vptr store","Whole actual vector argument frame","Actual helper frame and ordered bounded source iteration","Actual current zero font registry input","Exact source forward zero REP STOSD extent","Reverse unwind and CreateFont failure/error branches"):
   need(marker in model,'Current root/instance/iteration/source-error domain guard '+marker)
  for marker in ("Whole defined source API-entry CPU40","Whole genuine source API frame64","All literal source API argument DWORDs","machine.api_return(site,w[7],result)","machine.reg('ecx',after_native[1]);machine.reg('edx',after_native[2])","machine.flag(flag,(after_native[3]>>bit)&1)","Every guest FX512 byte unchanged","Full literal formatter cdecl RET context"):
   need(marker in api_code,'Exact finite native scalar/volatile/flags/cdecl/guestFX semantic contract '+marker)
  need("len(roots)==101"in association or "Only exact literal widget CALL enters"in association,'Literal borrowed caller source contract')
  need(producer.count('B2.bootstrap(')==1 and 'root_access_start=len(machine.accesses)'in producer and "PW.JournalAssociation(machine"in producer and "program,callbacks=G.source_program()"in producer,'Current producer single bootstrap and actual current literal program/journal adapters')
  for field in('per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','native_CS40_opaque_copy','canonical_reader_changed'):need(source[field]is False,'Persistent semantic prediction boundary '+field)
  need('out=dict(prior)'in flag_code and "elif op in('and','or','xor','test')"in flag_code and "result[8]&=~mask(domain)"in flag_code,'Finite source-derived undefined flag projection closes after definition')
  unique={pc for row in rows for pc in row['source_PCs']};need(len(unique)==1016 and sum(len(row['source_PCs'])for row in rows)==263580,'Every actual reached literal source instruction')
  PE=load('independent_widget_program_PE',input_path('tools/analysis/pe.py'));images={}
  for label,path in(('game','MW3/Mech3.exe'),('CRT','local/mw3-staged/Shared_DLLs/MSVCRT.DLL')):images[label]=PE.PEImage(input_path(path).read_bytes())
  for pc in sorted(unique):
   need(pc in program,'Reached PC belongs to whole current literal program');d=program[pc];raw=bytes.fromhex(d['bytes_hex']);need(len(raw)==d['width']and raw,'Whole instruction byte/width contract');pe=images['CRT'if pc>=0x78000000 else'game'];offset=pe.rva_range(pc-pe.image_base,len(raw))[0];need(pe.read(offset,len(raw))==raw,'Every byte of reached physical source instruction');counts['whole_reached_physical_instruction_rows']+=1
  active={pc:offsets for pc,offsets in callbacks.items()if pc in unique};need(len(active)==31 and {o for values in active.values()for o in values}=={2069,2077},'Every actual undefined callback belongs to exact AF/OF State offsets')
  for pc,offsets in active.items():
   need(len(set(offsets))==len(offsets)and pc in program,'Unique literal callback attribution');d=program[pc]
   if offsets==(2069,):need(d['mnemonic']in('test','xor','or'),'Exact architecturally undefined logical AF callback')
   else:need(offsets==(2077,2069)and d['mnemonic']=='sar'and d['decoded_operands'][1]['kind']=='immediate'and d['decoded_operands'][1]['value']==4,'Exact four-bit SAR undefined OF/AF callback')
   counts['whole_reached_callback_offset_rows']+=1
  need([(x['level'],x['sequence'])for x in flags]==[(l,s)for l in('O0','O2')for s in range(6)],'Every current finite flag ledger')
  for ledger in flags:
   for consumer in ledger['consumers']:
    need(consumer['all_consumers_defined']is True and not set(consumer['flags'])&set(consumer['undefined_before']),'Every actual flag consumer is defined by its source chronology')
    if consumer['PC']in unique:need(program[consumer['PC']]['mnemonic']==consumer['mnemonic'],'Reached physical source consumer mnemonic')
    counts['whole_source_defined_flag_consumers']+=1
  need(counts['whole_source_defined_flag_consumers']==45924,'Entire source6 defined-flag coverage')
  paired_path=input_path('reports/m4-joint-startup138-source/preparation-r11/paired_exports.py');EX=load('independent_widget_State_CPU_FX_raw',paired_path)
  for level in('O0','O2'):
   facade=EX.Facade(next(x for x in source['paired_exports']if x['branch']==level),pin);readers.append(facade)
   for row in rows:
    if row['level']!=level:continue
    g=row['GDI_source'];entry=g['source_entry_context'];record=dict(level=level,sequence=row['sequence'],root=row['root'])
    for side in('before','after'):
     prefix=row['whole_carried_'+side]['prefix'];state=facade.data(prefix+'State.bin');cpu=facade.data(prefix+'CPU.bin');fx=facade.data(prefix+'FX.bin')
     need(len(state)==3504 and len(cpu)==40 and len(fx)==512,'Whole current source-computed State3504/CPU40/FX512 raw boundary')
     want_state=entry['State_sha256']if side=='before'else g['computed_final_State_sha256'];want_fx=entry['FX_sha256']if side=='before'else g['computed_final_FX_sha256'];need(hashlib.sha256(state).hexdigest()==want_state and hashlib.sha256(fx).hexdigest()==want_fx,'Entire raw boundary joins exact producer-computed source State/FX')
     words=struct.unpack('<10I',cpu);need(words[:8]==tuple(struct.unpack_from('<I',state,GM.I.REG[n])[0]for n in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))and words[9]==struct.unpack_from('<I',state,2472)[0],'Every full CPU register/PC maps exact source State offsets')
     for name,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):need((words[8]>>bit)&1==int(bool(state[GM.I.FLAGS[name]])),'Every full CPU flag maps exact source State byte')
     if side=='before':need(list(words)==entry['CPU'],'Entire entry CPU40 independently joins producer source entry context')
     else:need(words[4]==0x20001804 and words[9]==0x410a80,'Actual literal complete scheduler RET frame and PC')
     record[side]=dict(State_sha256=hashlib.sha256(state).hexdigest(),CPU_sha256=hashlib.sha256(cpu).hexdigest(),FX_sha256=hashlib.sha256(fx).hexdigest());counts['whole_State_CPU_FX_raw_boundaries']+=1
    joins.append(record)
   facade.close();readers.remove(facade)
  need(len(joins)==84 and counts['whole_State_CPU_FX_raw_boundaries']==168,'All84 complete source entry/return machine correspondence')
  artifact=out/'whole-widget-semantic-correspondence.json';artifact.write_text(json.dumps(joins,indent=2)+'\n');pin(artifact);pin(__file__);pin(sys.executable)
  for q,h in list(PINS.items()):pin(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for reader in readers:reader.close()
  report=dict(passed=passed,source_provider_path=str(p),source_provider_sha256=sha(p),scope='Independent whole reached physical program, accepted unchanged interpreter layers/State callback offsets/current API/flag domains and168 complete State/CPU/FX raw producer-source correspondences, combined with current independent84 whole memory/raw GDI proof. Producing source6 owns independent single-bootstrap semantic prediction; no redundant interpreter execution claimed.',counts=dict(counts),independent_semantic_code_and_physical_program_review=passed,independent_whole_State_CPU_FX_source_correspondence=passed,second_interpreter_execution=False,source_equivalence_prediction_owned_by_current_consumer=True,reader_closed=True,capture_archives_opened=0,worker_executed=False,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main()
