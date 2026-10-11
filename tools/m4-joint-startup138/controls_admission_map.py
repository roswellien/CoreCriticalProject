"""Enumerate the actual controls4 linked inputs; no worker or capture reader."""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
BUILD_SHA = 'e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'
PREP_SHA = 'f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'
TOOLS_SHA = '8d7e86bba387f5935f5114354f7e4e26972da5efba6ad67e597293f2677e4c43'

def main(name):
    out = R / 'reports/m4-joint-startup138' / name
    assert not out.exists()
    out.mkdir()
    pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.zip')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected is None or digest == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == digest
        pins[str(path)] = digest
        return path
    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())
    build_path = pin(R / 'reports/m4-joint-startup138/controls-build-r2/build.json', BUILD_SHA)
    build = read(build_path, BUILD_SHA)
    prep_path = pin(build['preparation'], PREP_SHA)
    prep = read(prep_path, PREP_SHA)
    assert build['passed'] and prep['passed'] and not build['worker_executed']
    assert (prep['control_target'], prep['control_phase'], prep['completed_prefix_roots'],
            prep['source_owned_font_create_calls'], prep['source_GDI_calls_before_fault']) == (0x5a3ff0, 135, 135, 15, 149)
    for path, digest in build['files'].items():
        pin(path, digest)
    tools = read(R / 'reports/m4-joint-startup138/controls-tools-preparation-r3/report.json', TOOLS_SHA)
    assert tools['passed']
    component = read(prep['widget_component_preparation'], prep['widget_component_preparation_sha256'])
    component_build = read(prep['widget_component_build'], prep['widget_component_build_sha256'])
    service = read(prep['borrowed_service_preparation'], prep['borrowed_service_preparation_sha256'])
    rootdir = prep_path.parent
    phase_map = read(rootdir / 'widget-phase-map.json')
    page_map = read(rootdir / 'source-page-union.json')
    integration = read(rootdir / 'integration-contracts.json')
    levels = {}
    header_total = 0
    for level, worker in build['workers'].items():
        tree = Path(worker['path']).parent
        worker_path = pin(worker['path'], worker['sha256'])
        objects = [str(pin(path)) for path in sorted(tree.rglob('*.obj'))]
        literals = [str(pin(path)) for path in prep['objects'][level]]
        assert len(literals) == 410
        widget_objects = [dict(path=str(pin(row['path'], row['sha256'])), sha256=row['sha256'])
                          for row in component_build['levels'][level]['objects']]
        assert len(widget_objects) == 60
        headers = [str(pin(path, build['files'][str(Path(path).resolve())]))
                   for path in worker['compiler_dependencies']]
        header_total += len(headers)
        forced = rootdir / level / 'registry_build_bindings.hpp'
        widget_header = rootdir / level / 'widget_build_bindings.hpp'
        assert str(forced.resolve()) in headers and str(widget_header.resolve()) in headers
        ninja = pin(tree / 'build.ninja')
        levels[level] = dict(
            worker=str(worker_path), worker_sha256=worker['sha256'],
            actual_CMake_objects=objects, parent_literal_objects=literals,
            widget_library=component_build['levels'][level]['library'],
            widget_library_sha256=component_build['levels'][level]['library_sha256'],
            widget_objects=widget_objects, actual_compiler_headers=headers,
            forced_registry_header=str(pin(forced)), widget_binding_header=str(pin(widget_header)),
            actual_ninja_link_commands=str(ninja))
    pin(__file__); pin(sys.executable)
    report = dict(
        passed=True,
        scope='Current controls4 linked-input map only; root independently attributes whole linked functions and targets before execution',
        preparation_path=str(prep_path), preparation_sha256=PREP_SHA,
        build_path=str(build_path), build_sha256=BUILD_SHA,
        controller_preparation_sha256=TOOLS_SHA,
        controller_path=str(pin(R/'tools/m4-joint-startup138/run_context_controls_v3.py')),
        semantic_checker_path=str(pin(R/'tools/m4-joint-startup138/check_context_controls_v4.py')),
        primary_source=str(pin(rootdir/'controls_main.cpp')),
        included_positive_source=str(pin(rootdir/'native_main.cpp')),
        helper_source=str(pin(rootdir/'widget_services.hpp')),
        primary_source_symbols=['main', 'context_control::before_phase', 'context_control::Writer::sink',
            'context_controls_guarded', 'context_controls_hardware_call',
            'mw34_context_controls_unused_positive_main',
            'mw34::m4_mixed::Context::Context', 'mw34::m4_mixed::Context::widget_entry',
            'mw34::m4_mixed::Context::setup_widgets', 'mw34::m4_mixed::Context::invoke_selected_body',
            'mw34::m4_mixed::Context::invoke_selected_table', 'mw34::m4_mixed::Context::control_snapshot',
            'mw34::m4_mixed::Context::cleanup_widgets', 'AcceptedWidgetServices::authority',
            'AcceptedWidgetServices::cleanup_authority', 'AcceptedWidgetServices::invoke',
            'map_current_formatter_sources', 'widget_whole_checkpoint'],
        component_preparation=prep['widget_component_preparation'],
        component_preparation_sha256=prep['widget_component_preparation_sha256'],
        component_build_sha256=prep['widget_component_build_sha256'],
        component_source=str(pin(Path(prep['widget_component_preparation']).parent/'component.cpp')),
        component_source_symbols=['mw34::m4_widget_native::Component::Impl::invoke',
            'mw34::m4_widget_native::Component::Impl::cleanup', 'mw34::m4_widget_native::Component::context_fault',
            'mw34::m4_widget_native::Component::Impl::observe_gdi_identity',
            'mw34::m4_widget_native::Component::Impl::provider_identity', 'mw34::m4_widget_native::entry',
            'mw34_widget_native_api', 'mw34_widget_hardware_call'],
        source_service=service['native_library'],
        source_service_preparation_sha256=prep['borrowed_service_preparation_sha256'],
        source_service_symbols=['mw34::m4_onexit::SessionImpl::borrow_widget_onexit'],
        root_phase_map=phase_map, source_page_map=page_map, integration=integration,
        levels=levels, actual_compiler_header_relations=header_total,
        control_target=0x5a3ff0, control_phase=135, completed_prefix_roots=135,
        source_GDI_calls_before_fault=149, source_owned_font_create_calls=15,
        current_fault_modes=8, planned_actual_worker_cases=16,
        hardware_scope='Actual invocation, poisoned same Context retry, and actual cleanup, each complete FX512/ENV28 boundary',
        manual_cleanup_scope='Fifteen fonts actually created by prior source5A3C30; current Context fault mark precedes same-thread reverse native DeleteObject; no seeded handles',
        nonREL32_relocation_review_pending=True, initializer_credit=0,
        writer_executed=False, capture_archive_reader_opened=False, files=pins)
    path = out/'report.json'
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True, path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         compiler_header_relations=header_total, files=len(pins))))

if __name__ == '__main__':
    main(sys.argv[1])
