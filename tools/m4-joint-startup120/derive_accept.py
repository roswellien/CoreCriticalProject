"""Derive bounded120 acceptance. New causal dispatch gate is mandatory."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent;ROOT=HERE.parents[1]
s=(ROOT/'tools/m4-joint-startup116/accept.py').read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one('Accept seven container roots','Accept four finite-vtable roots')
one("'continuity','loader_page_review'}","'continuity','loader_page_review','indirect_interface','indirect_source'}")
one('selected_roots=116,new_roots=7,original_sequences=6,original_phases=696,native_sequences=12,native_phases=1392','selected_roots=120,new_roots=4,original_sequences=6,original_phases=720,native_sequences=12,native_phases=1440')
one('ordered_callbacks_per_sequence=88,observed_source_pages=37,linked_literal_COFFs_per_level=336','ordered_callbacks_per_sequence=92,observed_source_pages=40,linked_literal_COFFs_per_level=351')
one('actual_linked_inputs_per_level=365','actual_linked_inputs_per_level=380')
one('normal_game_FS_records_per_sequence=14,native_game_FS_record_snapshots_per_sequence=28','normal_game_FS_records_per_sequence=15,native_game_FS_record_snapshots_per_sequence=30')
one("reports/m4-joint-startup116-root","reports/m4-joint-startup120-root")
one('Complete exact116 gate set and extent','Complete exact120 gate set and extent')
s=s.replace('Accepted109','Accepted116').replace("rows['parent']['connected_roots']==109","rows['parent']['connected_roots']==116")
one("'source','provider','paired','paired_FS','paired_owned','continuity','loader_page_review'","'source','provider','paired','paired_FS','paired_owned','continuity','loader_page_review','indirect_source'")
one("rows['native_preparation']['normal_new_allocations']==8","rows['native_preparation']['normal_new_allocations']==0")
one("c['persistent_phases']==1392 and c['persistent116_sequences']==12 and c['literal_registration_roots']==1056 and c['whole_page_BEFORE']==c['whole_page_AFTER']==51504","c['persistent_phases']==1440 and c['persistent120_sequences']==12 and c['literal_registration_roots']==1104 and c['whole_page_BEFORE']==c['whole_page_AFTER']==57600")
one('Complete persistent source116 extent','Complete persistent source120 extent')
one("c['complete116_provider_sequences']==12 and c['selected_registration_closures']==1056","c['complete120_provider_sequences']==12 and c['selected_registration_closures']==1104")
one("r['selected_used_bytes']==352","r['selected_used_bytes']==368")
one("r['first_replay_msize_capacity']==r['selected_used_bytes']==368","r['first_replay_msize_capacity']==r['selected_used_bytes']==368")
one("paired['counts']['paired_phases']==1392 and paired['counts']['whole_nonstack_page_relations']==97440 and paired['counts']['paired116_sequences']==12","paired['counts']['paired_phases']==1440 and paired['counts']['whole_nonstack_page_relations']==109440 and paired['counts']['paired120_sequences']==12")
one('complete35ordinary nonstack pages','complete38ordinary nonstack pages')
one("rows['link']['literal_COFF_links']==672 and rows['link']['actual_linked_inputs']==730","rows['link']['literal_COFF_links']==702 and rows['link']['actual_linked_inputs']==760")
one('Connected selected116 in original relative table order: seven new container constructors','Connected selected120 in original relative table order: four new finite-vtable constructors')
one('connected_roots=116 if passed else 109,new_roots=7 if passed else 0','connected_roots=120 if passed else 116,new_roots=4 if passed else 0')
one('remaining_inventory_roots=28 if passed else 35','remaining_inventory_roots=24 if passed else 28')
one('initializer_inventory_fraction=116/144 if passed else 109/144','initializer_inventory_fraction=120/144 if passed else 116/144')
p=HERE/'accept.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
print('Generated additive120 acceptance.py; capacity predicate must be checked against fresh proof before freeze')
