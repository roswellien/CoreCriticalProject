from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];old=ROOT/'tools/m4-container-source/recover.py';new=ROOT/'tools/m4-container-source/recover_v2.py';assert not new.exists()
s=old.read_text();anchor='normal.update(tailgraphs)';assert s.count(anchor)==1
s=s.replace(anchor,anchor+";normal={e:g for e,g in normal.items()if e in plan['game_local_entry_union']};tails={e for e in tails if e in normal};need(set(normal)==set(plan['game_local_entry_union']),'Exact chosen canonical game entries; no redundant loop-entry bodies')")
anchor="new={str(entry):graph for entry,graph in normal.items()if entry not in priorentries}";assert s.count(anchor)==1
s=s.replace(anchor,"priorentries.update(b['entry']for b in json.loads(pin(ROOT/'reports/m4-strings-source/lifts-r1/report.json').read_bytes())['source_bodies'].values());"+anchor)
compile(s,str(new),'exec');new.write_text(s)
