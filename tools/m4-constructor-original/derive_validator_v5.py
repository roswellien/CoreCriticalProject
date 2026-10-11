"""Bind getter publication to the full balanced genuine BEFORE owner graph."""
from pathlib import Path
import ast
h=Path(__file__).resolve().parent;t=(h/'validate_v4.py').read_text();out=h/'validate_v5.py'
if out.exists():raise ValueError('Fresh additive checker required')
a="                    graph(stem+'/BEFORE-constructor',phase_data=raw,side='BEFORE');graph(stem+'/BEFORE-member',True,raw,'BEFORE')"
b="                    graph(stem+'/BEFORE-constructor',phase_data=raw,side='BEFORE');before_shared_graph=graph_rows[-1];graph(stem+'/BEFORE-member',True,raw,'BEFORE')"
if t.count(a)!=1:raise ValueError('Exact own BEFORE graph derivation')
t=t.replace(a,b,1)
a="                            row['whole_receiver_page_sha256']=hashlib.sha256(receiver_page).hexdigest();"
b="""                            published_nodes=[node for node in before_shared_graph['nodes']if node['metadata'][2]!=before_shared_graph['metadata'][2]and node['metadata'][9]==cpu[1]]
                            need(len(published_nodes)==1,'Receiver is one actual source-published non-sentinel node in the complete balanced BEFORE ownership graph')
                            row['source_published_owner_node']=published_nodes[0];counts['whole_published_getter_owner_relations']+=1
                            row['whole_receiver_page_sha256']=hashlib.sha256(receiver_page).hexdigest();"""
if t.count(a)!=1:raise ValueError('Exact complete receiver backing join')
t=t.replace(a,b,1)
a="pin(Path(__file__).with_name('derive_validator_v4.py'));pin(sys.executable);passed=True";b="pin(Path(__file__).with_name('derive_validator_v4.py'));pin(Path(__file__).with_name('validate_v4.py'));pin(Path(__file__).with_name('derive_validator_v5.py'));pin(sys.executable);passed=True"
if t.count(a)!=1:raise ValueError('Exact checker lineage')
t=t.replace(a,b,1);ast.parse(t);out.write_text(t)
