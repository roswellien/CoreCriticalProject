"""Read-only physical scope correction for a retained prior FDIV proof archive.

The current Ninja link graph, all actual linked COFF undefined symbols, and the
current reached Session bootstrap are inspected. No build, replay or mutation.
"""
from pathlib import Path
import hashlib, json, re, subprocess, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main(name):
    out = ROOT/'reports/m4-mfc-control-audit'/name
    need(not out.exists(), 'Fresh read-only correction receipt')
    out.mkdir(parents=True)
    pins, levels, symbols, passed = {}, [], {}, False
    def pin(path, digest=None):
        path = Path(path).resolve()
        actual = sha(path)
        need(digest is None or actual == digest, 'Physical exact input '+str(path))
        pins[str(path)] = actual
        return path
    def read(path, digest=None):
        return json.loads(pin(path,digest).read_bytes())
    def run(argv, label):
        result = subprocess.run(list(map(str,argv)), capture_output=True, timeout=45,
                                creationflags=0x08000000)
        (out/(label+'.stdout')).write_bytes(result.stdout)
        (out/(label+'.stderr')).write_bytes(result.stderr)
        need(result.returncode == 0, 'Actual bounded physical symbol enumeration '+label)
        return result.stdout.decode().splitlines()
    try:
        pin(__file__); pin(sys.executable)
        prior = pin(ROOT/'reports/m4-mfc-control-audit/audit-r3/report.json',
                    '813a1ee12d09fccec264230f021650bc6ae44c56d3f0fb99b75bd7f3dd96f132')
        need(json.loads(prior.read_bytes())['passed'], 'Prior measured causal/hardware/ownership audit passed')
        nm = pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-nm.exe')
        build_rows = [
            ('normal',ROOT/'reports/m4-joint-startup103/build-r1/build.json',
             '75e233397c59e42ac11f86eef7195181c17d9c02aae4f5cf16fd4566585e4531'),
            ('controls',ROOT/'reports/m4-mfc-review/controls-build-r2/build.json',
             '0664820d6ed94ec6d28024f1f0571b26d581f723e824b53777491d75c20e436c')]
        actual_objects = set()
        for kind,buildpath,digest in build_rows:
            build = read(buildpath,digest)
            need(build['passed'], 'Actual immutable successful build')
            for level,worker in build['workers'].items():
                executable = pin(worker['path'],worker['sha256'])
                folder = executable.parent
                graph = pin(folder/'build.ninja').read_text()
                link = next(line for line in graph.splitlines()
                            if line.startswith('build '+executable.name+': CXX_EXECUTABLE_LINKER'))
                encoded = link.split(' ',3)[3].split(' |')[0]
                tokens = encoded.split(' ')
                actual = {str((folder/Path(token.replace('$:',':').replace('$ ',' '))).resolve())
                          for token in tokens if token.endswith(('.obj','.lib'))}
                declared = set(worker['objects'])
                absent = declared-actual
                archive = ROOT/f'build/m4-fdiv-native-build-r3-{level}/fdiv_registry.lib'
                need(absent == {str(archive)} and len(declared) == 296
                     and len(declared & actual) == 295 and str(archive) not in graph,
                     'Exactly295 listed source COFFs linked; one retained FDIV proof archive absent from actual graph')
                need(not any(p.endswith('.lib') for p in actual),
                     'No unlisted substitute static archive provides FDIV registry implementation')
                for path in actual: pin(path)
                actual_objects.update(actual)
                archive = pin(archive)
                lines = run([nm,'--format=posix','--print-file-name','--defined-only',archive],
                            kind+'-'+level+'-archive-definitions')
                unique = set()
                for line in lines:
                    match = re.search(r': (\S+) T ',line)
                    if not match: continue
                    symbol = match.group(1)
                    if ('Registry@m4_crt_fdiv@' in symbol
                            or 'HostServices@m4_crt_fdiv@' in symbol
                            or symbol.startswith('mw34_fdiv_sub_')):
                        unique.add(symbol)
                need(unique and any('initialize@Registry@m4_crt_fdiv@' in s for s in unique)
                     and 'mw34_fdiv_sub_78004254' in unique,
                     'Actual retained archive defines standalone Registry lifecycle and original FDIV writer')
                symbols[level] = sorted(unique)
                levels.append(dict(kind=kind,level=level,declared_source_dependencies=296,
                                   actually_linked_declared_source_COFFs=295,
                                   retained_unlinked_proof_archive=str(archive),
                                   total_actual_linked_COFFs=len(actual),worker_sha256=worker['sha256']))
        ordered = sorted(actual_objects)
        # Two batches stay inside the Windows CreateProcess command-line bound.
        undefined = set()
        for start in range(0,len(ordered),90):
            lines = run([nm,'--format=posix','--print-file-name','--undefined-only',
                         *ordered[start:start+90]], 'actual-undefined-'+str(start//90))
            for line in lines:
                match = re.search(r': (\S+) U ',line)
                if match: undefined.add(match.group(1))
        for level,unique in symbols.items():
            need(not set(unique) & undefined,
                 'None of the actually linked COFFs references an archive-specific Registry/HostServices/FDIV-writer symbol')
        need(not any('Registry@m4_crt_fdiv@' in s or 'HostServices@m4_crt_fdiv@' in s
                     or s.startswith('mw34_fdiv_sub_') for s in undefined),
             'No unresolved old FDIV class/writer symbol is requested anywhere in four actual link graphs')
        production = pin(ROOT/'reports/m4-mfc-native/preparation-r1/registry_library.cpp').read_text()
        session = production[production.index('struct SessionImpl {'):production.index(' void enter(unsigned root){',production.index('struct SessionImpl {'))]
        need('std::make_unique<mg::Context>(r,provider)' in session
             and 'std::make_unique<lb::Binding>(*parent,provider,0)' in session
             and 'binding->start(*parent)' in session
             and 'binding->external_source_call(0x78004482,0xffffff90)' in session
             and 'fd::Registry' not in session and 'mw34_fdiv_sub_' not in session,
             'Reached Session bootstrap uses current heap/locale/sentinel/onexit owner and never old FDIV Registry')
        native_main = pin(ROOT/'reports/m4-joint-startup103/preparation-r1/native_main.cpp').read_text()
        need('std::make_unique<m4_onexit::Session>(r_,crt,mfc)' in native_main
             and 'registry_->bootstrap()' in native_main and 'fd::Registry' not in native_main,
             'Actual selected103 entry uses this Session bootstrap exclusively')
        need('fd::Registry&fdiv_' in production[:production.index('struct SessionImpl {')],
             'Retained archived Context text is disclosed rather than incorrectly claimed absent')
        (out/'archive-specific-symbols.json').write_text(json.dumps(symbols,indent=2)+'\n')
        passed = True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        for path in out.iterdir():
            if path.is_file(): pin(path)
        result = dict(passed=passed,schema='mw34-mfc-FDIV-retained-proof-link-scope-v1',
                      scope='Corrects prior audit-r3 linked-object wording only:296 metadata dependencies include295 genuinely linked source COFFs plus one inherited unlinked standalone FDIV proof archive. The measured actual controls and native executions are unchanged.',
                      levels=levels,physically_inspected_actual_COFFs=len(actual_objects) if 'actual_objects' in locals() else 0,
                      archive_specific_undefined_symbols_reached=0 if passed else None,
                      source_scope='Unused archived Context declaration remains in registry_library.cpp; no corresponding old Registry/HostServices/writer reference is emitted in any actual linked COFF. Reached SessionImpl uses mg::Context/lb::Binding bootstrap.',
                      correction_required=True,candidate_rebuild_required=False,candidate_replay_required=False,
                      candidate_or_capture_modified=False,prior_audit_measurements_superseded=False,
                      linked_object_metadata_claim_superseded=True,files=pins,physical_closure=verify_manifest(pins),
                      initializer_credit=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        pins[str(out/'report.json')] = sha(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))


if __name__ == '__main__':
    main(sys.argv[1])
