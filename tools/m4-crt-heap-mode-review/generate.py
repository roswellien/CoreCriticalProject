"""Generate fresh independent probe fixtures from the frozen prior setup."""
from pathlib import Path
ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent
OLD = ROOT / 'tools/m4-crt-heap-create-review'

def change(s, a, b):
    if a not in s:
        raise ValueError('Required frozen fixture fragment: ' + a)
    return s.replace(a, b)

s = (OLD / 'controls.cpp').read_text()
s = s[:s.index(' void verify(bool clean)')]
s = change(s, 'MW34_CRT_HEAP_CREATE_NO_MAIN', 'MW34_CRT_HEAP_MODE_NO_MAIN')
s = change(s, 'hc::', 'hm::')
s = change(s, 'mainargs->heap_create', 'mainargs->heap_mode')
s = change(s, '18*4096', '20*4096')
s = change(s, '/18 pages', '/20 pages')
s = change(s, 'which>=121', 'which>=133')
s = change(s, 'duplicate_cleanup{};Job', 'duplicate_cleanup{};unsigned pattern{};std::array<std::byte,4096>lower_initial{};Job')
s = change(s, '  fdiv=std::make_unique<fd::Registry>(r);', '''  {const auto page=provider_raw_page(review_provider,0x78005000);r.memory().map({0x78005000},4096,Permissions::read|Permissions::write);r.memory().write({0x78005000},page);r.memory().protect({0x78005000},Permissions::read|Permissions::execute);}
  {const unsigned indices[]{0,5,11,12,17,23};for(unsigned i=0;i<6;++i)if(index==indices[i])pattern=i;
   const unsigned first[]{0,4,12,1,0x200,0xffffffff},last[]{0,8,0x48,0x80000000,0x20000000,0xffffffff};review_put<unsigned>(lower_initial.data()+0x850,first[pattern]);review_put<unsigned>(lower_initial.data()+0x624,last[pattern]);
   const auto expected=read_file((std::filesystem::path("D:/Projects/MW34Recomp/reports/m4-crt-heap-mode-review/source-r1")/("declared-lower-input-"+std::to_string(pattern)+".bin")).string().c_str());review_need(expected.size()==4096&&!std::memcmp(expected.data(),lower_initial.data(),4096),"Declared independent lower-stack input matches separately pinned source artifact");
   r.memory().map({hm::lower_stack},4096,Permissions::read|Permissions::write);r.memory().write({hm::lower_stack},lower_initial);fresh_output(row/"declared-lower-input.bin",lower_initial);std::array<unsigned,3>input{pattern,first[pattern],last[pattern]};raw_output(row/"lower-input-status.bin",input);}
  fdiv=std::make_unique<fd::Registry>(r);''')
s = change(s, 'duplicate_cleanup||mode==131', 'duplicate_cleanup||mode==144')
s = change(s, 'std::array<unsigned,32>hs{', 'std::array<unsigned,36>hs{')
s = change(s, 'hm::api_site,hm::iat,hm::api_ret};', 'hm::api_site,hm::iat,hm::api_ret,unsigned(h.probe_reached),unsigned(h.probe_returned),unsigned(h.query_reached),h.probe_frame};')
s = change(s, 'std::array<std::byte,sizeof(ld::Binding)>unused_locale{};', 'std::array<std::byte,sizeof(hc::Binding)>unused_heap_create{};std::memcpy(unused_heap_create.data(),&mainargs->heap_create,unused_heap_create.size());std::array<std::byte,sizeof(ld::Binding)>unused_locale{};')
s = change(s, '"Unused accepted locale object remains intact during poisoned retry");', '"Unused accepted locale object remains intact during poisoned retry");review_need(!std::memcmp(unused_heap_create.data(),&mainargs->heap_create,unused_heap_create.size()),"Frozen unused heap-create Binding remains intact during poisoned retry");')
(HERE / 'controls.cpp').write_text(s + (HERE / 'controls_tail.inc').read_text(), encoding='utf-8')

b = (OLD / 'build_controls.ps1').read_text().replace('m4-crt-heap-create-review', 'm4-crt-heap-mode-review')
b = change(b, "$reviewHeapObjects=[ordered]@{}", "$reviewHeapObjects=[ordered]@{};$reviewModeObjects=[ordered]@{}")
b = change(b, "'heap_objects','compiler_read_headers'", "'heap_objects','heap_mode_objects','compiler_read_headers'")
b = change(b, "'tools/m4-crt-heap-mode-review/controls_tail.inc',", "'tools/m4-crt-heap-mode-review/controls_tail.inc','tools/m4-crt-heap-create-review/controls.cpp','tools/m4-crt-heap-create-review/build_controls.ps1','tools/m4-crt-heap-create-review/run.py','tools/m4-crt-heap-create-review/launch_fixture.py',")
b = change(b, "$reviewSources[$reviewCandidate]=Hash $reviewCandidate", "foreach($file in Get-ChildItem -LiteralPath (Join-Path $reviewBase 'source-r1') -File){$reviewSources[$file.FullName]=Hash $file.FullName}\n$reviewSources[$reviewCandidate]=Hash $reviewCandidate")
b = change(b, "  $capture=Join-Path $dir 'capture.obj';", "  $modeList=@();foreach($kind in @('selector','probe')){$o=Join-Path $reviewPrep \"$kind-$level.obj\";$reviewModeObjects[$o]=Hash $o;$modeList+=$o}\n  $capture=Join-Path $dir 'capture.obj';")
b = change(b, "@('tools/m4-crt-heap-create',", "@('tools/m4-crt-heap-mode','tools/m4-crt-heap-create',")
b = change(b, '+$localeList+$heapList+@', '+$localeList+$heapList+$modeList+@')
b = change(b, "Join-Path $reviewPrep 'heap_create.hpp'", "Join-Path $reviewPrep 'heap_mode.hpp'")
b = change(b, '$reviewHeapObjects,$reviewHeaders', '$reviewHeapObjects,$reviewModeObjects,$reviewHeaders')
b = change(b, 'heap_objects=$reviewHeapObjects;compiler_read_headers', 'heap_objects=$reviewHeapObjects;heap_mode_objects=$reviewModeObjects;compiler_read_headers')
b = change(b, 'bounded source mode-selector refusal', 'genuine mode-selector/stack-probe/relocated RET and bounded first GetVersionExA CALL refusal with declared initial owned lower-stack inputs')
(HERE / 'build_controls.ps1').write_text(b, encoding='utf-8')
(HERE / 'launch_fixture.py').write_text((OLD / 'launch_fixture.py').read_text().replace('m4-crt-heap-create-review', 'm4-crt-heap-mode-review'), encoding='utf-8')
r = (OLD / 'run.py').read_text().replace('m4-crt-heap-create-review', 'm4-crt-heap-mode-review')
r = change(r, "'heap_objects', 'compiler_read_headers'", "'heap_objects', 'heap_mode_objects', 'compiler_read_headers'")
r = change(r, "result['malformed_token_denials'] != 18", "result['malformed_token_denials'] != 19")
r = change(r, "'full_causal_source_model_oracle': False", "'GetVersionExA_executed': False, 'declared_lower_stack_inputs': 6, 'probe_return_proved': True, 'full_causal_source_model_oracle': False")
(HERE / 'run.py').write_text(r, encoding='utf-8')
