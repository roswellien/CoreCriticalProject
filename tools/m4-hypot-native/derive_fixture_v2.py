"""Add reached source-PC bridge guards without altering the linked bodies."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('fixture.cpp')
SHA='7caea494f8610968c70256f6a3f287c1dfe3060ed3e678afa3cb994aa9b0cc79'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
text=BASE.read_text()
before='        need(active == this && GetCurrentThreadId() == thread, "Exact active numeric context and host thread");'
assert text.count(before)==1
text=text.replace(before,before+'\n        if (entered && !complete) {\n            const bool final_return = s.gpr.rip.dword == Runtime::external_return && frames.size() == 1 && frames.back().ret == Runtime::external_return;\n            need(final_return || hf::reached_PC(s.gpr.rip.dword), "Unobserved numeric source PC at a native bridge denied");\n        }')
out=BASE.with_name('fixture_v2.cpp')
assert not out.exists()
out.write_text(text)
print(hashlib.sha256(out.read_bytes()).hexdigest())
