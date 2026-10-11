"""Derive VOID Lockit return EAX from literal state, not LastError metadata."""
from pathlib import Path
p=Path(__file__).with_name('formatting_derivations.py');s=p.read_text()
a="source_access_start=start,API_index=responses.index,";assert s.count(a)==1;s=s.replace(a,"source_access_start=start,API_index=responses.index,mixed_Lockit_source_calls=list(observer.mixed_source_calls)if root==0x4e1ca0 else [],")
a="scratch if ctor else api['actual_API_words'][9]";assert s.count(a)==1;s=s.replace(a,"source_call['EAX_after']")
a="api=api[0];scratch=p[1]+48";assert s.count(a)==1;s=s.replace(a,"api=api[0];scratch=p[1]+48\n  source_calls=[v for v in result['mixed_Lockit_source_calls']if v['PC']==site and v['frame']==p[1]and v['returned']];need(len(source_calls)==1,'Literal mixed source CALL/RET state owns this exact invocation');source_call=source_calls[0];need(source_call['scratch']==scratch and source_call['source_access_entered_index']==pi+1 and source_call['source_access_returned_index']==ei+1 and source_call['API_index']==api['API_index']and source_call['API_after']==api['API_index']+1,'Complete source-derived mixed CALL/API/RET chronology');need(not ctor or source_call['EAX_after']==scratch,'Literal constructor MOV EAX,EDI returns scratch')")
exec(compile(s,str(p),'exec'),globals())
