"""Fresh independently authored fixtures retain the immutable earlier setup."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent;OLD=ROOT/'tools/m4-crt-heap-mode-review'
def exact(path,digest):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Frozen fixture input changed '+str(path))
    return data.decode()
def change(s,a,b):
    if a not in s:raise ValueError('Required frozen fixture fragment '+a)
    return s.replace(a,b)
def main():
    s=exact(OLD/'controls.cpp','a6447a247776716a51f3f1014578572c927c9ac0de17e13c1f935a2597c6d040');s=s[:s.index(' void verify(bool clean)')]
    s=change(s,'MW34_CRT_HEAP_MODE_NO_MAIN','MW34_CRT_HEAP_VERSION_NO_MAIN');s=change(s,'hm::','hv::');s=change(s,'mainargs->heap_mode','mainargs->heap_version');s=change(s,'20*4096','21*4096');s=change(s,'/20 pages','/21 pages');s=change(s,'which>=133','which>=145')
    s=change(s,'duplicate_cleanup||mode==144','duplicate_cleanup||mode==156')
    s=change(s,'  fdiv=std::make_unique<fd::Registry>(r);','  {const auto page=provider_raw_page(review_provider,0x7800c000);r.memory().map({0x7800c000},4096,Permissions::read|Permissions::write);r.memory().write({0x7800c000},page);r.memory().protect({0x7800c000},Permissions::read|Permissions::execute);}\n  fdiv=std::make_unique<fd::Registry>(r);')
    s=change(s,'std::array<std::byte,sizeof(hc::Binding)>unused_heap_create{};','std::array<std::byte,sizeof(hm::Binding)>unused_heap_mode{};std::memcpy(unused_heap_mode.data(),&mainargs->heap_mode,unused_heap_mode.size());std::array<std::byte,sizeof(hc::Binding)>unused_heap_create{};')
    s=change(s,'"Frozen unused heap-create Binding remains intact during poisoned retry");','"Frozen unused heap-create Binding remains intact during poisoned retry");review_need(!std::memcmp(unused_heap_mode.data(),&mainargs->heap_mode,unused_heap_mode.size()),"Frozen unused heap-mode Binding remains intact during poisoned retry");')
    s=change(s,'raw_output(row/"heap-status.bin",hs);return job;', 'raw_output(row/"heap-status.bin",hs);raw_output(row/"query-witness.bin",h.query_witness);raw_output(row/"query-input.bin",h.query_input);raw_output(row/"query-output.bin",h.query_output);raw_output(row/"query-output-accesses.bin",h.output_accesses);raw_output(row/"query-api-before.bin",review_api(h.query_before));raw_output(row/"query-api-after.bin",review_api(h.query_after));std::array<unsigned,10>qs{h.query_frame,h.query_pointer,h.query_result,h.output_count,unsigned(h.query_called),unsigned(h.query_preflight),unsigned(h.query_output_complete),unsigned(h.query_returned),unsigned(h.selector_returned),unsigned(h.environment_reached)};raw_output(row/"query-status.bin",qs);return job;')
    (HERE/'controls.cpp').write_text(s+(HERE/'controls_tail.inc').read_text(),encoding='utf-8')
    b=exact(OLD/'build_controls.ps1','5e36240f3b7bdaba0387593bf71d054a01e1670157369877756c99c66d854b41').replace('m4-crt-heap-mode-review','m4-crt-heap-version-review')
    b=change(b,'$reviewModeObjects=[ordered]@{}','$reviewModeObjects=[ordered]@{};$reviewVersionObjects=[ordered]@{}')
    b=change(b,"'heap_mode_objects','compiler_read_headers'","'heap_mode_objects','heap_version_objects','compiler_read_headers'")
    b=change(b,"'tools/m4-crt-heap-version-review/controls_tail.inc',","'tools/m4-crt-heap-version-review/controls_tail.inc','tools/m4-crt-heap-version-review/direct_query.inc','tools/m4-crt-heap-mode-review/controls.cpp','tools/m4-crt-heap-mode-review/build_controls.ps1',")
    b=change(b,"$reviewSources[$reviewCandidate]=Hash $reviewCandidate","foreach($file in Get-ChildItem -LiteralPath (Join-Path $reviewRoot 'reports/m4-crt-heap-mode-review/source-r1') -File){$reviewSources[$file.FullName]=Hash $file.FullName}\n$reviewSources[$reviewCandidate]=Hash $reviewCandidate")
    b=change(b,'$o=Join-Path $reviewPrep "$kind-$level.obj"','$o=Join-Path $reviewRoot "reports/m4-crt-heap-mode/preparation-r2/$kind-$level.obj"')
    b=change(b,"  $capture=Join-Path $dir 'capture.obj';","  $versionList=@();foreach($kind in @('branch','environment','mode1','epilogue')){$o=Join-Path $reviewPrep \"$kind-$level.obj\";$reviewVersionObjects[$o]=Hash $o;$versionList+=$o}\n  $capture=Join-Path $dir 'capture.obj';")
    b=change(b,"@('tools/m4-crt-heap-mode',","@('tools/m4-crt-heap-version','tools/m4-crt-heap-mode',")
    b=change(b,'+$heapList+$modeList+@','+$heapList+$modeList+$versionList+@')
    b=change(b,"Join-Path $reviewPrep 'heap_mode.hpp'","Join-Path $reviewPrep 'heap_version.hpp'")
    b=change(b,'$reviewHeapObjects,$reviewModeObjects,$reviewHeaders','$reviewHeapObjects,$reviewModeObjects,$reviewVersionObjects,$reviewHeaders')
    b=change(b,'heap_mode_objects=$reviewModeObjects;compiler_read_headers','heap_mode_objects=$reviewModeObjects;heap_version_objects=$reviewVersionObjects;compiler_read_headers')
    b=change(b,'bounded first GetVersionExA CALL refusal','private actual GetVersionExA witness, finite guest output copy, real source selector continuation/RET and bounded post-selector or ENV frontier')
    (HERE/'build_controls.ps1').write_text(b,encoding='utf-8')
    (HERE/'launch_fixture.py').write_text(exact(OLD/'launch_fixture.py','855f217054277b0676356972ffcffdadba4b0921703ca15f4146176fc395325e').replace('m4-crt-heap-mode-review','m4-crt-heap-version-review'),encoding='utf-8')
if __name__=='__main__':main()
