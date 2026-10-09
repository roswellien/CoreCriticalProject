"""Original game operands and bounded page inventory; no expected AFTER values."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];REC=ROOT/'reports/m4-onexit-batch-recovery/recovery-r3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh interface');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Pinned interfaceinput');files[str(p)]=v;return p
 pin(REC/'report.json','7195aa825cde0c1d47279f285f66604b2fcd0eb66e1d88419d9eb4e7360170ee')
 graphs=json.loads(pin(REC/'game-normal-graphs.json').read_bytes());inputs=json.loads(pin(REC/'registry-inputs.json').read_bytes());roots=json.loads(pin(REC/'registration-roots.json').read_bytes())
 spec=importlib.util.spec_from_file_location('original_operand_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 rows={r['pc']:r for g in graphs.values()for r in g['instructions']};rows.update({r['pc']:r for r in inputs['game_sentinel_rows']});contracts=[]
 for pc in sorted(rows):
  r=rows[pc];ops=r['operands'].split(' <')[0];plain=dict(pc=pc,width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=ops)
  if not r['mnemonic'].startswith('f'):contracts.append(mod.instruction_contract(plain));continue
  args=[];reads=[];writes=[]
  for i,t in enumerate(ops.split(',')if ops else[]):
   t=t.strip();st=re.fullmatch(r'st(?:\((\d)\))?',t)
   if st:args.append(dict(kind='x87_register',index=int(st[1]or 0),bits=80))
   else:
    a=mod.operand(t);args.append(a)
    if a['kind']=='memory':(writes if r['mnemonic']in('fst','fstp') else reads).append(i)
  contracts.append(dict(**plain,decoded_operands=args,explicit_memory_reads=reads,explicit_memory_writes=writes,implicit_memory=[],flags='Integer flags retained; original x87 state/status effects require finite hardware observations',original_FP=True))
 literals=[dict(pc=r['pc'],address=int(m[1],16))for r in rows.values()if r['mnemonic']=='mov'and(m:=re.fullmatch(r'ecx, (0x[0-9a-f]+)',r['operands']))]
 absolute=[dict(pc=x['pc'],address=x['address'],width=x['width'],operation=x['operation'])for g in graphs.values()for x in g['absolute_memory_references']]
 pages=sorted({x['address']&~4095 for x in absolute+literals}|{0x9a1000})
 objects=[dict(address=x['address'],page=x['address']&~4095,initial_source_pc=x['pc'],observed_extent='Entire containing page; source accesses and exact dynamic extents checked by independent interpreter')for x in literals]
 old=json.loads(pin(ROOT/'reports/m4-joint-startup28-original/preparation-r3/report.json').read_bytes());selected=sorted(old['order']+[dict(slot=x['slot'],entry=x['entry'])for x in roots],key=lambda x:x['slot']);need(len(selected)==54 and len({x['slot']for x in selected})==54,'54uniqueactualtablecells')
 report=dict(passed=True,scope='Source-only game operand interface and bounded page inventory',instructions=contracts,unique_instructions=len(contracts),registration_roots=roots,selected_order=selected,source_data_pages=pages,source_code_pages=sorted({r['pc']&~4095 for r in rows.values()}),source_ECX_objects=objects,absolute_references=absolute,sentinel_fragment=dict(entry=0x5ac3d8,end=0x5ac3ec,rows=inputs['game_sentinel_rows'],research_invocation=True),full_game_BSS_snapshot=False,AFTER_machine_seed=False,native_executed=False,original_executed=False,files=files)
 pin(Path(__file__));(out/'instruction-contracts.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'instruction-contracts.json');(out/'report.json').write_text(json.dumps(dict(passed=True,instruction_contracts_sha256=sha(out/'instruction-contracts.json'),selected_order=selected,data_pages=pages,code_pages=report['source_code_pages'],files=files,execution=False),indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),instructions=len(contracts),pages=pages)))
if __name__=='__main__':main(sys.argv[1])
