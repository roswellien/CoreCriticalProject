from pathlib import Path
import hashlib
p=Path(__file__).parent
s=(p/'fixture_resource_v2.cpp').read_text()
old='c.CS_depth,c.CS.RecursionCount,reinterpret_cast<std::uintptr_t>(c.CS.OwningThread)'
assert s.count(old)==1
s=s.replace(old,'c.CS_depth,std::uint64_t(c.CS.RecursionCount),reinterpret_cast<std::uintptr_t>(c.CS.OwningThread)')
(p/'fixture_resource_v3.cpp').write_text(s)
print(hashlib.sha256((p/'fixture_resource_v3.cpp').read_bytes()).hexdigest())
