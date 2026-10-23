"""ROOT pure extracted owner-input guard controls; no reader or source model."""
from pathlib import Path
import ast,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 specs={'tools/m4-startup141-paired/constructor_native_input141_v3.py':'83d49374d56b96466ceda8833aa714e5a90db450ef6978673fd728a5ee06a281','tools/m4-startup141-paired/constructor_native36_source141_v5.py':'de64b2aba09c0004f6f10c68e123b80c4384c5acca2d34a0ab47edf35895dd45','tools/m4-startup141-paired/native_owner_cut_controls_v2.py':'1726e09a8e4ea4d70502571d5d87ce2190e82104b8019ecc76c88096f269e2da'}
 texts={};files={}
 for rel,h in specs.items():
  p=(R/rel).resolve();b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h;texts[rel]=b.decode();files[str(p)]=h
 def audit(event,args):
  if event=='open'and args and isinstance(args[0],(str,bytes)):
   mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
   if isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3):raise AssertionError('Pure controls require no further file read')
 sys.addaudithook(audit)
 ns={};exec(compile(texts['tools/m4-startup141-paired/native_owner_cut_controls_v2.py'],'physically-reviewed-owner-controls','exec'),ns)
 result=ns['controls'](texts['tools/m4-startup141-paired/constructor_native_input141_v3.py'],texts['tools/m4-startup141-paired/constructor_native36_source141_v5.py'])
 assert result['passed']and result['negative_controls']==28 and len(set(result['refused']))==28 and result['positive_static_prefix_write_retained']and result['positive_whole_owner_bytes_retained']and not result['source_execution']and not result['reader_opened']
 out=R/'reports/m4-startup141-paired/root-owner-controls-r1';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(**result,independent_review=True,canonical_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(str(q))
if __name__=='__main__':main()
