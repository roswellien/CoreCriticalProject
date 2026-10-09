"""Create new fixture build/launch wrappers from frozen proven machinery."""
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
OLD = ROOT / 'tools/m4-crt-parser-prefix-review'
launcher = (OLD / 'launch_fixture.py').read_text()
launcher = launcher.replace('.parents[2]', '.parents[3]')
launcher = launcher.replace("'reports/m4-crt-parser-prefix'", "'reports/m4-crt-locale-default-contract/review'")
launcher = launcher.replace("'independent-compiled-'", "'compiled-'")
(HERE / 'launch_fixture.py').write_text(launcher, encoding='utf-8')
build = (OLD / 'build_controls.ps1').read_text()
build = build.replace('[string]$CandidateBuild)', '[string]$CandidateBuild,[switch]$CompileOnly)')
build = build.replace("$PSScriptRoot '../..'", "$PSScriptRoot '../../..'")
build = build.replace("'reports/m4-crt-parser-prefix'", "'reports/m4-crt-locale-default-contract/review'")
build = build.replace("'independent-compiled-*'", "'compiled-*'")
build = build.replace('$reviewParserObjects=[ordered]@{}', '$reviewParserObjects=[ordered]@{};$reviewLocaleObjects=[ordered]@{}')
start = build.index("foreach($rel in @('tools/m4-crt-parser-prefix-review/controls.cpp'")
end = build.index("foreach($rel in @('MW3/Mech3.exe'", start)
build = build[:start] + "foreach($rel in @('tools/m4-crt-locale-default-contract/review/controls.cpp','tools/m4-crt-locale-default-contract/review/launch_fixture.py','tools/m4-crt-locale-default-contract/review/prepare_tools.py','tools/m4-crt-locale-default-contract/review/build_controls.ps1','tools/m4-crt-locale-default-contract/review/generate_fixture.py','tools/m4-crt-locale-default-contract/review/fixture_tail.inc','tools/m4-crt-entry-mainargs/capture.s','tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-guest-cw/guest_cw.cpp','tools/m4-guest-cw/guest_cw.hpp')){$p=Join-Path $reviewRoot $rel;$reviewSources[$p]=Hash $p}\n" + build[end:]
build = build.replace("  $capture=Join-Path $dir 'capture.obj';", "  $localeList=@();foreach($kind in @('mbinit','setmbcp','lock')){$o=Join-Path $reviewPrep \"$kind-$level.obj\";$reviewLocaleObjects[$o]=Hash $o;$localeList+=$o}\n  $capture=Join-Path $dir 'capture.obj';")
build = build.replace("@('tools/m4-crt-parser-prefix','tools/m4-crt-commandline-carry'", "@('tools/m4-crt-locale-default','tools/m4-crt-parser-prefix','tools/m4-crt-commandline-carry'")
build = build.replace('$argv,$producer,$parser,$capture,$library', '$argv,$producer,$parser)+$localeList+@($capture,$library')
build = build.replace("Join-Path $reviewPrep 'parser.hpp'", "Join-Path $reviewPrep 'locale.hpp'")
build = build.replace('exact prepared parser prefix header', 'exact prepared locale header')
build = build.replace('$reviewParserObjects,$reviewHeaders)', '$reviewParserObjects,$reviewLocaleObjects,$reviewHeaders)')
build = build.replace('parser_objects=$reviewParserObjects;', 'parser_objects=$reviewParserObjects;locale_objects=$reviewLocaleObjects;')
build = build.replace("  Run 'C:/Python314/python.exe' (@($reviewNativeLauncher,$exe)+$inputs) (Join-Path $dir 'native-launch.log')", "  if(-not$CompileOnly){Run 'C:/Python314/python.exe' (@($reviewNativeLauncher,$exe)+$inputs) (Join-Path $dir 'native-launch.log')}")
build = build.replace('passed=$reviewPassed;scope=', 'passed=$reviewPassed;compiled_only=[bool]$CompileOnly;scope=')
build = build[:build.index('\nif($reviewPassed){')]
build = build.replace('and parser prefix before first locale read', 'and three literal default-locale bodies in explicit source bootstrap before real malloc body')
(HERE / 'build_controls.ps1').write_text(build, encoding='utf-8')
