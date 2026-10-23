"""Final explicit current providers and full carried registry retry/cleanup dump."""
from pathlib import Path
p=Path(__file__).with_name('prepare_preresource_v1.py');s=p.read_text()
for a,b in [("m4-138-preresource-controls/preparation-r1","m4-138-preresource-controls/preparation-r3"),("MW3/MSVCP60.dll","local/mw3-staged/Shared_DLLs/MSVCP50.DLL"),("MW3/MSVCRT.dll","local/mw3-staged/Shared_DLLs/MSVCRT.DLL"),("MW3/MFC42.dll","local/mw3-staged/Shared_DLLs/MFC42.DLL")]:assert s.count(a)==1;s=s.replace(a,b)
a='ci=c\n'
b='''change(' const std::string why=c.failure_reason();w.append(p+"Context-reason.txt",why.data(),why.size());', ' const std::string why=c.failure_reason();w.append(p+"Context-reason.txt",why.data(),why.size());struct SinkOwner{PreResourceWriter*w;std::string prefix;};SinkOwner sink{&w,p+"Registry/"};c.registry().dump(+[](std::string_view name,std::span<const std::byte>raw,void*o){auto*s=static_cast<SinkOwner*>(o);s->w->append(s->prefix+std::string(name),raw.data(),raw.size());},&sink);')
change('context.registry().finish();need(!context.registry().live_handle()', 'context.registry().finish();struct CleanupSink{PreResourceWriter*w;std::string prefix;};CleanupSink cleanup_sink{&writer,prefix+"cleaned/Registry/"};context.registry().dump(+[](std::string_view name,std::span<const std::byte>raw,void*o){auto*s=static_cast<CleanupSink*>(o);s->w->append(s->prefix+std::string(name),raw.data(),raw.size());},&cleanup_sink);need(!context.registry().live_handle()')
ci=c
'''
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
