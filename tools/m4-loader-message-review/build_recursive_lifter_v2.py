"""Place clang-cl showIncludes before retained '-- source' terminator."""
from pathlib import Path
p=Path(__file__).with_name('build_recursive_lifter.py');s=p.read_text();a="compiler+=' /showIncludes'";b="need(compiler.count(' -c -- ')==1,'Exact compiler source-option boundary');compiler=compiler.replace(' -c -- ',' /showIncludes -c -- ')";assert s.count(a)==1;s=s.replace(a,b);assert s.count('recursive-lifter-build-r1')==1;s=s.replace('recursive-lifter-build-r1','recursive-lifter-build-r2');exec(compile(s,str(p),'exec'))
