"""Additively match the authentic broker's fixed DWORD reservation table."""
from pathlib import Path
source=Path(__file__).resolve().with_name('prepare_chronological.py')
target=source.with_name('prepare_chronological_v2.py')
assert not target.exists()
text=source.read_text()
old="r'constexpr std::array<std::uintptr_t,(\\d+)> bases\\{([^;]+)\\};'"
new="r'inline constexpr std::array<std::uint32_t,(\\d+)> bases\\{([^;]+)\\};'"
assert text.count(old)==1
text=text.replace(old,new,1)
text=text.replace("f'constexpr std::array<std::uintptr_t,{len(allbases)}> bases{{'","f'inline constexpr std::array<std::uint32_t,{len(allbases)}> bases{{'",1)
target.write_text(text)
