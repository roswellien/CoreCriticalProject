"""Adapt frozen build/transport machinery for new heap fixtures only."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
HERE=Path(__file__).absolute().parent
OLD=ROOT/'tools/m4-crt-locale-default-contract/review'

def replace(text,old,new):
    if old not in text: raise ValueError('Expected frozen machinery fragment: '+old)
    return text.replace(old,new)

launcher=(OLD/'launch_fixture.py').read_text()
launcher=replace(launcher,'.parents[3]','.parents[2]')
launcher=replace(launcher,'reports/m4-crt-locale-default-contract/review','reports/m4-crt-heap-init-review')
(HERE/'launch_fixture.py').write_text(launcher,encoding='utf-8')
build=(OLD/'build_controls.ps1').read_text()
build=replace(build,"$PSScriptRoot '../../..'","$PSScriptRoot '../..'")
build=replace(build,'reports/m4-crt-locale-default-contract/review','reports/m4-crt-heap-init-review')
build=replace(build,'tools/m4-crt-locale-default-contract/review/','tools/m4-crt-heap-init-review/')
build=replace(build,'$reviewLocaleObjects=[ordered]@{}','$reviewLocaleObjects=[ordered]@{};$reviewHeapObjects=[ordered]@{}')
build=replace(build,'$o=Join-Path $reviewPrep "$kind-$level.obj";$reviewLocaleObjects', '$o=Join-Path $reviewRoot "reports/m4-crt-locale-default/preparation-r4/$kind-$level.obj";$reviewLocaleObjects')
build=replace(build,"'parser_objects','compiler_read_headers'","'parser_objects','locale_objects','heap_objects','compiler_read_headers'")
build=replace(build,"  $capture=Join-Path $dir 'capture.obj';","  $heapList=@();foreach($kind in @('fragment','provider')){$o=Join-Path $reviewPrep \"$kind-$level.obj\";$reviewHeapObjects[$o]=Hash $o;$heapList+=$o}\n  $capture=Join-Path $dir 'capture.obj';")
build=replace(build,"@('tools/m4-crt-locale-default','tools/m4-crt-parser-prefix'","@('tools/m4-crt-heap-init','tools/m4-crt-locale-default','tools/m4-crt-parser-prefix'")
build=replace(build,')+$localeList+@($capture',')+$localeList+$heapList+@($capture')
build=replace(build,"Join-Path $reviewPrep 'locale.hpp'","Join-Path $reviewPrep 'heap.hpp'")
build=replace(build,'exact prepared locale header','exact prepared heap header')
build=replace(build,'$reviewLocaleObjects,$reviewHeaders)','$reviewLocaleObjects,$reviewHeapObjects,$reviewHeaders)')
build=replace(build,'locale_objects=$reviewLocaleObjects;','locale_objects=$reviewLocaleObjects;heap_objects=$reviewHeapObjects;')
build=replace(build,'and three literal default-locale bodies in explicit source bootstrap before real malloc body','and retained locale objects plus literal attach fragment/heap prefix at first HeapCreate import refusal')
(HERE/'build_controls.ps1').write_text(build,encoding='utf-8')
run=(OLD/'run.py').read_text()
run=replace(run,'.parents[3]','.parents[2]')
run=replace(run,'reports/m4-crt-locale-default-contract/review','reports/m4-crt-heap-init-review')
run=replace(run,"'parser_objects', 'locale_objects', 'compiler_read_headers'","'parser_objects', 'locale_objects', 'heap_objects', 'compiler_read_headers'")
run=replace(run,'with explicit default-locale prefix seam','with explicit State-PC-only attach fragment/heap prefix seam')
run=replace(run,"'malloc_body_executed': False,","'HeapCreate_executed': False, 'heap_initialized': False, 'heap_handle_published': False,")
(HERE/'run.py').write_text(run,encoding='utf-8')
