"""Emit complete retry State/CPU/FX/routes for independent byte comparison."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
driver = Path(__file__).with_name('prepare_runtime_fixture_v3.py')
generator = driver.read_text()
terminal = "exec(compile(text, str(parent), 'exec'), globals())"
assert generator.count(terminal) == 1
generator = generator.replace(terminal, r'''
before = '  const auto calls=c.runtime().calls().size();'
after = before + r'\n  auto retry_dump=[&](const std::string&prefix){t.w->append(prefix+"State.bin",&c.state(),3504);t.w->append(prefix+"CPU.bin",&c.runtime().cpu(),40);t.w->append(prefix+"FX.bin",c.runtime().fx().data(),512);std::vector<unsigned>routes;for(const auto&call:c.runtime().calls()){routes.insert(routes.end(),{call.site.value,call.target.value,call.return_pc.value,unsigned(call.import),unsigned(call.completed)});}t.w->append(prefix+"routes.bin",routes.data(),routes.size()*4);};'
assert text.count(before) == 1
text = text.replace(before, after.replace('\\n', '\n'))
text = text.replace('  dump(c,*t.w,"actual-retry-before/",t.aliases);', '  retry_dump("actual-retry-before/");dump(c,*t.w,"actual-retry-before/",t.aliases);')
text = text.replace('  dump(c,*t.w,"actual-retry-after/",t.aliases);', '  retry_dump("actual-retry-after/");dump(c,*t.w,"actual-retry-after/",t.aliases);')
text = text.replace('    pin(__file__)', "    pin(__file__)\n    pin(Path(__file__).with_name('prepare_runtime_fixture_v3.py'))")
exec(compile(text, str(parent), 'exec'), globals())
''')
exec(compile(generator, str(driver), 'exec'), globals())
