"""Create independent fixtures from unchanged prior setup and new ownership tests."""
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
HERE=Path(__file__).absolute().parent
OLD=ROOT/'tools/m4-crt-heap-init-review'

def change(s,a,b):
    if a not in s: raise ValueError('Required unchanged fixture fragment: '+a)
    return s.replace(a,b)

s=(OLD/'controls.cpp').read_text()
s=s[:s.index(' void verify(bool clean)')]
s=change(s,'MW34_CRT_HEAP_INIT_NO_MAIN','MW34_CRT_HEAP_CREATE_NO_MAIN')
s=change(s,'hi::','hc::')
s=change(s,'mainargs->heap','mainargs->heap_create')
s=change(s,'17*4096','18*4096')
s=change(s,'/17 pages','/18 pages')
s=change(s,'which>=109','which>=121')
s=change(s,'which>=85?which:0','0')
s=change(s,'std::filesystem::path row;unsigned mode{},trigger_count{};','std::filesystem::path row;unsigned mode{},trigger_count{};std::uint64_t private_handle{};bool live_membership{},released_membership{},duplicate_cleanup{};')
s=change(s,'  fdiv=std::make_unique<fd::Registry>(r);','  {const auto page=provider_raw_page(review_provider,0x78035000);r.memory().map({0x78035000},4096,Permissions::read|Permissions::write);r.memory().write({0x78035000},page);}\n  fdiv=std::make_unique<fd::Registry>(r);')
s=change(s,'auto&h=mainargs->heap_create;raw_output(row/"heap-accesses.bin",h.accesses);','auto&h=mainargs->heap_create;raw_output(row/"heap-accesses.bin",h.accesses);raw_output(row/"heap-api-accesses.bin",h.api_accesses);raw_output(row/"heap-witness.bin",h.witness);raw_output(row/"heap-registry.bin",h.registry);raw_output(row/"heap-create-api-before.bin",api(h.create_before));raw_output(row/"heap-create-api-after.bin",api(h.create_after));raw_output(row/"heap-destroy-api-before.bin",api(h.destroy_before));raw_output(row/"heap-destroy-api-after.bin",api(h.destroy_after));std::array<std::uint64_t,8>own{private_handle,unsigned(live_membership),unsigned(released_membership),h.actual_create_calls(),h.actual_destroy_calls(),h.successful_destroy_calls(),unsigned(duplicate_cleanup),unsigned(h.live_handle())};raw_output(row/"independent-ownership.bin",own);')
s=change(s,'std::array<unsigned,26>hs{mode,h.control,h.frame,h.parent_frame,h.access_count,h.event_count,h.undefined_count,h.stage,h.depth,h.fault_pc,h.fault_address,unsigned(h.used),unsigned(h.active),unsigned(h.failed),unsigned(h.api_reached),h.caller_error,h.restored_error,hc::fragment,hc::entry,hc::site,hc::ret,hc::api_site,hc::iat,hc::api_ret,hc::raw_import,84};','std::array<unsigned,32>hs{mode,h.control,h.frame,h.parent_frame,h.access_count,h.api_access_count,h.event_count,h.undefined_count,h.stage,h.depth,h.fault_pc,h.fault_address,unsigned(h.used),unsigned(h.active),unsigned(h.failed),unsigned(h.api_reached),unsigned(h.api_called),unsigned(h.registered),unsigned(h.api_returned),unsigned(h.published),unsigned(h.mode_reached),unsigned(h.zero_reached),unsigned(h.cleanup_succeeded),h.caller_error,h.restored_error,hc::fragment,hc::entry,hc::site,hc::ret,hc::api_site,hc::iat,hc::api_ret};')
s=change(s,'last_job=job;','last_job=job;auto&owned=mainargs->heap_create;review_need(!owned.live_handle()&&owned.cleanup_succeeded&&!owned.token_valid(hc::token),"Closed heap has no private live handle or guest lookup");review_need(owned.actual_create_calls()==owned.actual_destroy_calls()&&owned.actual_destroy_calls()==owned.successful_destroy_calls(),"Every actual created heap is released exactly once with actual success");if(owned.actual_create_calls()){review_need(private_handle==owned.known_handle()&&private_handle&&live_membership,"Independent private acquired full HANDLE was observed live");review_need(!review_heap_member(private_handle),"Actual released full HANDLE disappears from process heap inventory");released_membership=true;review_need(owned.registry[16]==private_handle,"Cleanup actual input is the original private full HANDLE");}review_need(duplicate_cleanup||mode==131,"Terminal duplicate cleanup checked except injected author throw before independent callback");')
# Declare membership helper before ReviewFixture, then leave unchanged old retry checks.
s=change(s,'struct ReviewFixture;thread_local', 'bool review_heap_member(std::uint64_t);\nstruct ReviewFixture;thread_local')
s=s.replace('api(h.create_before)','review_api(h.create_before)').replace('api(h.create_after)','review_api(h.create_after)').replace('api(h.destroy_before)','review_api(h.destroy_before)').replace('api(h.destroy_after)','review_api(h.destroy_after)')
s=change(s,'bool review_heap_member(std::uint64_t);','Api review_api(const m4_cmd_native::ApiIdentity&identity){return identity.target?commandline_api(identity):Api{};}\nbool review_heap_member(std::uint64_t);')
(HERE/'controls.cpp').write_text(s+(HERE/'controls_tail.inc').read_text(),encoding='utf-8')

build=(OLD/'build_controls.ps1').read_text()
build=change(build,'reports/m4-crt-heap-init-review','reports/m4-crt-heap-create-review')
build=change(build,'tools/m4-crt-heap-init-review/','tools/m4-crt-heap-create-review/')
build=change(build,"'tools/m4-crt-heap-create-review/prepare_tools.py',",'')
build=change(build,'generate_fixture.py','generate.py')
build=change(build,'fixture_tail.inc','controls_tail.inc')
build=change(build,'$o=Join-Path $reviewPrep "$kind-$level.obj";$reviewHeapObjects','$o=Join-Path $reviewRoot "reports/m4-crt-heap-init/preparation-r2/$kind-$level.obj";$reviewHeapObjects')
build=change(build,"@('tools/m4-crt-heap-init',","@('tools/m4-crt-heap-create','tools/m4-crt-heap-init',")
build=change(build,"Join-Path $reviewPrep 'heap.hpp'","Join-Path $reviewPrep 'heap_create.hpp'")
build=change(build,'heap prefix at first HeapCreate import refusal','heap prefix with actual HeapCreate ownership and bounded source mode-selector refusal')
(HERE/'build_controls.ps1').write_text(build,encoding='utf-8')
launcher=(OLD/'launch_fixture.py').read_text().replace('reports/m4-crt-heap-init-review','reports/m4-crt-heap-create-review')
(HERE/'launch_fixture.py').write_text(launcher,encoding='utf-8')
run=(OLD/'run.py').read_text().replace('reports/m4-crt-heap-init-review','reports/m4-crt-heap-create-review')
run=change(run,"result['malformed_token_denials'] != 25","result['malformed_token_denials'] != 18")
run=change(run,"'HeapCreate_executed': False, 'heap_initialized': False, 'heap_handle_published': False,","'HeapCreate_executed': True, 'genuine_source_token_published': True, 'full_heap_initialization_complete': False,")
run=change(run,"'table_initialization_proved': False,", "'full_causal_source_model_oracle': False, 'table_initialization_proved': False,")
(HERE/'run.py').write_text(run,encoding='utf-8')
