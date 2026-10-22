"""Development-time extraction of authored startup lowering, without report I/O."""
import ast


def extract(root):
    def module(path):
        return ast.parse((root / path).read_text())

    def function(tree, name):
        return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

    header = ast.parse('import ctypes as c\nimport re\nfrom pathlib import Path\n'
        'from host_adapter import LLVM, HOST_LAYOUT, FLAG_HELPERS, FUNCTION_INDEX, checked_state_offsets\n'
        'SSA = r"%[A-Za-z0-9_.$]+"\n'
        'def need(value, message):\n    if not value: raise ValueError(message)\n'
        'require = need\n')
    api = module('tools/x87-repair/adapt_control.py')
    header.body.append(next(n for n in api.body if isinstance(n, ast.ClassDef) and n.name == 'ControlLLVM'))
    control = module('tools/m4-crt-control/adapt.py')
    header.body.extend(function(control, name) for name in ('blocks', 'pc_model', 'undef_proof'))
    adapter = function(control, 'adapt')
    adapter.name = 'adapt_provider'
    adapter.args = ast.parse('def f(folder, dll, entries, expected_pcs): pass').body[0].args
    adapter.body = adapter.body[1:]
    # Replace only the old disassembly-file PC list with non-executable metadata.
    proof = next(n for n in adapter.body if isinstance(n, ast.Try))
    index = next(i for i, n in enumerate(proof.body) if isinstance(n, ast.Assign) and
        isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'original')
    proof.body[index:index+2] = ast.parse('original = set(expected_pcs)').body
    for node in ast.walk(adapter):
        if isinstance(node, ast.Name) and node.id == 'ENTRIES':
            node.id = 'entries'
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'api':
            node.value = ast.parse('ControlLLVM(dll)', mode='eval').body
    final = [n for n in adapter.body if isinstance(n, ast.Try)][-1]
    final.body = final.body[:-1]  # historical layout report writer
    header.body.append(adapter)
    game = function(module('tools/m4-crt-control-integration/adapt_game.py'), 'adapt')
    game.name = 'adapt_game'
    game.args = ast.parse('def f(out, dll): pass').body[0].args
    game.body = game.body[1:10]  # through typed lowering/finally; exclude old link/reports
    game.body[0].value = ast.parse('out / "game-guest.ll"', mode='eval').body
    for node in game.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'api':
            node.value = ast.parse('ControlLLVM(dll)', mode='eval').body
    header.body.append(game)
    fdiv = module('tools/m4-crt-fdiv/adapt_native.py')
    header.body.extend(n for n in fdiv.body if isinstance(n, ast.Assign) and
        isinstance(n.targets[0], ast.Name) and n.targets[0].id in ('NEW', 'CONTROL'))
    header.body.extend(function(fdiv, name) for name in ('definition', 'named', 'cfg_model'))
    writer = function(fdiv, 'main')
    writer.name = 'adapt_writer'
    writer.args = ast.parse('def f(folder, dll, control_path): pass').body[0].args
    # Drop only folder restriction and old report-path/hash lookup. The passed
    # control path is generated afresh from the player's CRT by the driver.
    writer.body = [writer.body[2], *writer.body[5:]]
    for node in writer.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'api':
            node.value = ast.parse('LLVM(dll)', mode='eval').body
        if isinstance(node, ast.Try):
            report = next(i for i, n in enumerate(node.body) if isinstance(n, ast.Assign) and
                isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'report')
            node.body = node.body[:report]
    header.body.append(writer)
    result = ast.unparse(ast.fix_missing_locations(header)) + '\n'
    compile(result, 'startup_adapt.py', 'exec')
    if 'ROOT' in result or 'reports/' in result:
        raise ValueError('Historical dependency survived startup extraction')
    return result
