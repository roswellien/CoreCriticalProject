from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];old=ROOT/'tools/m4-container-source/recover_v2.py';new=ROOT/'tools/m4-container-source/recover_v3.py';assert not new.exists()
s=old.read_text();a="normal={e:g for e,g in normal.items()if e in plan['game_local_entry_union']};tails={e for e in tails if e in normal};need(set(normal)==set(plan['game_local_entry_union']),'Exact chosen canonical game entries; no redundant loop-entry bodies')"
b="required=set(plan['game_local_entry_union'])|{f['helper_entry']for f in plan['normal_frames']if f['helper_entry']in normal};normal={e:g for e,g in normal.items()if e in required};tails={e for e in tails if e in normal};need(set(normal)==required,'Chosen canonical game entries plus genuine lower FS tail helpers, no redundant loop-entry bodies')"
assert s.count(a)==1;s=s.replace(a,b);compile(s,str(new),'exec');new.write_text(s)
