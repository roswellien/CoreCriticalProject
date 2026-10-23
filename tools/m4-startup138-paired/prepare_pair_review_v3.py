from pathlib import Path
p=Path(__file__).with_name('review_pair_receipt_v2.py');s=p.read_text()
a='2ef8e701d9f2307991d07fa1024b5a741d083534798a7174b02ad81d96a88b50';b='a7047c9a755c1e989ef1a6b15fd0072c5e7b6a7e99d5efff64391937dab217bc'
assert s.count(a)==1;s=s.replace(a,b)
a=" 'paired_phases':1656,'paired131_sequences':12,"
b=a+"\n 'typed_format_registrar_end_source_joins':72,"
assert s.count(a)==1;s=s.replace(a,b)
a=" fonts=artifact('Font-paired-cleanup-relations.json');"
b=" formats=artifact('Formatting-paired-source-relations.json');need(len(formats)==48,'Four formatter roots x12 actual cases');need(len({(r['level'],r['sequence'],r['root'])for r in formats})==48,'Unique complete formatter matrix');typed=[r for f in formats for r in f['typed_registrar_end_source_joins']];need(len(typed)==72 and all(r['separate_whole_CRT_source_relation_required']is True and r['game_byte_difference_authorization']is False for r in typed),'Exact72 separately typed provider publications grant no game byte allowance')\n"+a
assert s.count(a)==1;s=s.replace(a,b)
q=p.with_name('review_pair_receipt_v3.py');assert not q.exists();q.write_text(s)
