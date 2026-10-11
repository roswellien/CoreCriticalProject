"""Isolate external Runtime poison cleanup and protect diagnostic catches.

Normal library/source behavior is unchanged. A poisoned external callback
requires owned resource release rather than more source execution.
"""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('prepare_runtime_fixture.py')
text = parent.read_text()
text = text.replace("'runtime-preparation-r1/report.json'", "'runtime-preparation-r2/report.json'")
text = text.replace('d6c804c83b1f9a00fb026a27d0df1d6982d93d63f133d214956354d8bcf7c506',
                    '6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e')
text = text.replace('  const auto retry_cpu=c.runtime().cpu(),retry_fx=c.runtime().fx();',
                    '  const auto retry_cpu=c.runtime().cpu();std::array<std::byte,512>retry_fx{};std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),retry_fx.begin());')
text = text.replace('retry_fx==c.runtime().fx()', '!std::memcmp(retry_fx.data(),c.runtime().fx().data(),512)')
marker = "    for path, digest in prior['generated_sources'].items():"
assert text.count(marker) == 1
text = text.replace(marker, '''    fault_include = out / 'registry'
    fault_include.mkdir()
    old_include = Path(prior['native_include'])
    for source in old_include.rglob('*'):
        if source.is_file() and source.suffix in ('.cpp', '.hpp', '.inc'):
            pin(source)
            target = fault_include / source.relative_to(old_include)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    implementation = fault_include / 'session_impl.inc'
    source_text = implementation.read_text()
    original = '  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();'
    assert source_text.count(original) == 1
    source_text = source_text.replace(original, '  if(r.poisoned()&&!failed)poison();\\n' + original)
    implementation.write_text(source_text)
    prior['native_include'] = str(fault_include)
    prior['native_library'] = str(fault_include / 'registry_library.cpp')
''' + marker)
marker = "    (out / 'fixture.cpp').write_text("
assert text.count(marker) == 1
text = text.replace(marker, '''    text = one(text, 'extern "C" unsigned data_boundary_initialize(void*p)noexcept{',
        'extern "C" unsigned data_boundary_initialize(void*p)noexcept{\\n m4_spi_connected::ErrorBoundary outer_error;ni::NumericHostBoundary diagnostic_boundary(0x37f);')
    text = one(text, ' (void)invoke(t);',
        ' Hardware invocation_before{},invocation_after{};hardware(invocation_before);(void)invoke(t);hardware(invocation_after);t.w->append("actual-invocation-hardware-before.bin",&invocation_before,sizeof(invocation_before));t.w->append("actual-invocation-hardware-after.bin",&invocation_after,sizeof(invocation_after));need(hardware_equal(invocation_before,invocation_after),"Actual Context invocation preserves caller numerical environment before diagnostics");')
''' + marker)
text = text.replace('    pin(__file__)', "    pin(__file__)\n    pin(Path(__file__).with_name('prepare_runtime_fixture.py'))")
exec(compile(text, str(parent), 'exec'), globals())
