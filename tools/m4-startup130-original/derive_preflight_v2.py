from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'preflight.py').read_text()
a="for page in oldprep['observed_pages']:need(records[page][1]==oldrecords[page][1],'Every complete inherited raw data/stack input page unchanged')"
b="""loader_pages=[page for page in oldprep['observed_pages']if page not in oldrecords]
  need(loader_pages==[0x780c1000,0x78115000,0x5f498000,0x5f4cc000,0x7810a000,0x78145000,0x78146000],'Seven authentic DLL-loaded pages are not sparse authored input records')
  for page in oldprep['observed_pages']:
   if page in oldrecords:need(records[page][1]==oldrecords[page][1],'Every complete inherited sparse raw data/stack input page unchanged')"""
assert a in s;s=s.replace(a,b).replace('inherited_whole_input_pages_checked=43','inherited_whole_sparse_input_pages_checked=36,authentic_loaded_provider_pages=7')
(p/'preflight_v2.py').write_text(s)
