"""Retain the independently derived first API prefix and actual operand joins."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_connected_fixture_v3.py';wrapper=parent.read_text()
needle="exec(compile(wrapper,str(parent),'exec'),globals())"
addition="""old=\"assert text.count(old)==1;text=text.replace(old,new)\"
# Insert into the innermost source, after the fixed-page mapping adaptation.
marker=\"need(api_index<4,'Finite named API frontier');a=api_rows[api_index];\"
audit=\"(out/(level+'-first-API-prefix.json')).write_text(json.dumps(dict(source_PCs=m.PCs,source_accesses=m.accesses,source_CPU=m.cpu_now(),actual_accesses=list(struct.iter_unpack('<IIQII',records.data(stem+'after/accesses.bin'))),actual_API_words=api_rows[api_index]['words']),indent=2)+'\\\\n');need(api_index<4,'Finite named API frontier');a=api_rows[api_index];\"
# The v3 wrapper's generated body still owns the variable text.
wrapper=wrapper.replace(\"exec(compile(text,str(parent),'exec'),globals())\",\"assert text.count(\"+repr(marker)+\")==1;text=text.replace(\"+repr(marker)+\",\"+repr(audit)+\");exec(compile(text,str(parent),'exec'),globals())\")
exec(compile(wrapper,str(parent),'exec'),globals())"""
assert wrapper.count(needle)==1;wrapper=wrapper.replace(needle,addition)
exec(compile(wrapper,str(parent),'exec'),globals())
