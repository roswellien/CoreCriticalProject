"""Move kind3 gate from Lockit branch to every chronological phase."""
from pathlib import Path
import ast,hashlib,json,textwrap
R=Path(__file__).resolve().parents[2];base=Path(__file__).with_name('validate_realloc_v1.py');text=base.read_text();changes=[]
def one(old,new):
 global text
 assert text.count(old)==1;pos=text.index(old);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):]
start=text.index("      registry_before=struct.unpack('<4I'");end=text.index("      for a in[s for s in allocspec",start);block=text[start:end];one(block,'')
common="     realloc_ledger=records.data(f'phase/{seq}/{phase}/api-ledger.bin');realloc_count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];need(realloc_count<=256 and len(realloc_ledger)==realloc_count*104,'Every phase complete bounded provider API ledger for kind3 gate')\n"
moved='\n'.join(line[1:]for line in block.rstrip().splitlines())+'\n';moved=moved.replace('range(apicount)','range(realloc_count)').replace("'<26I',ledger,ri*104","'<26I',realloc_ledger,ri*104")
anchor='     observe_family(records,data,seq,phase,entry,page,formats,mixed,family_artifacts,counts,tid,targets,format_byentry)';one(anchor,common+moved+anchor)
reverse=text
for d in reversed(changes):
 p=d['position'];assert reverse[p:p+len(d['new'])]==d['new'];reverse=reverse[:p]+d['old']+reverse[p+len(d['new']):]
assert reverse==base.read_text();tree=ast.parse(text);parents={child:node for node in ast.walk(tree)for child in ast.iter_child_nodes(node)}
loop=next(n for n in ast.walk(tree)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='ri');chain=[];n=loop
while n in parents:n=parents[n];chain.append(n)
assert not any(isinstance(n,ast.If)and isinstance(n.test,ast.Compare)and ast.unparse(n.test)=='entry in roots'for n in chain)
assert any(isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)and 'phase'in ast.unparse(n.target)for n in chain)
target=base.with_name('validate_realloc_v2.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-startup138-original/realloc-validator-preparation-r2';assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,changes=changes,exact_reverse_restores_frozen_v1=True,kind3_gate_in_common_phase_scope=True,AST_proves_not_Lockit_conditioned=True,parent_existing_Lockit_ledger_reads_retained=True,validator_path=str(target),validator_sha256=sha(target),archive_reader_opened=False,validation_executed=False,initializer_credit=0,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))}),indent=2)+'\n');print(q,sha(q))
