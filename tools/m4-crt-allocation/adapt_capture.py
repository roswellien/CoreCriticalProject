"""Author fresh direct-capture source adapters; never emit a flat capture tree."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'reports/m4-crt-heap-return/preparation-r2'
def main():
 s=(OLD/'observations.hpp').read_text().replace('hr::capture_for(r)','al::capture_for(r)')
 a=s.index('void fresh_output(');b=s.index('\ntemplate<class T>',a)
 s=s[:a]+'''void fresh_output(const std::filesystem::path&path,std::span<const std::byte>bytes){direct_append(path,bytes.data(),bytes.size());}'''+s[b:]
 s='#include "capture_adapter.hpp"\n'+s
 s=s.replace('auto phase=directory/name;require(std::filesystem::create_directory(phase),"Fresh phase directory");','auto phase=directory/name;')
 marker=' fresh_output(phase/"state.bin",r.remill_state());'
 extra='''
 for(auto [address,size,name]:std::array<std::tuple<unsigned,unsigned,const char*>,8>{{{al::caller_cleanup,9,"allocation-caller-source.bin"},{al::malloc_entry,18,"allocation-malloc-source.bin"},{al::size_entry,30,"allocation-size-source.bin"},{al::worker_entry,173,"allocation-worker-source.bin"},{0x7800cc97,21,"allocation-round-source.bin"},{0x7800cc3f,35,"allocation-null-source.bin"},{al::free_entry,177,"allocation-free-source.bin"},{0x7800cc39,6,"allocation-freecold-source.bin"}}}){std::vector<std::byte>b(size);r.memory().read({address},b);fresh_output(phase/name,b);}
 {std::array<std::uint64_t,24>registry{};std::array<std::uint64_t,16>witness{};std::array<unsigned,16>progress{};
  std::array<mg::Access,128>source{};std::array<mg::Access,8>returns{};std::array<mg::Access,16>external{};std::array<std::array<unsigned,8>,8>projections{};
  if(auto*known=al::capture_for(r)){registry=known->allocation_registry;witness=known->allocation_witness;progress=known->allocation_progress();source=known->accesses;returns=known->api_accesses;external=known->external_accesses;projections=known->external_projections;
   fresh_output(phase/"allocation-initial.bin",known->allocation_initial);fresh_output(phase/"allocation-pattern.bin",known->allocation_pattern);fresh_output(phase/"allocation-backing.bin",known->allocation_backing());if(progress[14]){std::array<std::byte,4096>owned{};r.memory().read({al::allocation_address},owned);fresh_output(phase/"allocation-owned-page.bin",owned);}}
  raw_output(phase/"allocation-registry.bin",registry);raw_output(phase/"allocation-witness.bin",witness);raw_output(phase/"allocation-progress.bin",progress);
  raw_output(phase/"allocation-source-accesses.bin",source);raw_output(phase/"allocation-api-return-accesses.bin",returns);raw_output(phase/"allocation-external-accesses.bin",external);raw_output(phase/"allocation-external-projections.bin",projections);}
'''
 assert s.count(marker)==1;s=s.replace(marker,extra+marker)
 (HERE/'observations.hpp').write_text(s)
 s=(OLD/'main_v2.inc').read_text().replace('std::ofstream','DirectText')
 s=s.replace('MW34_CRT_HEAP_RETURN_NO_MAIN','MW34_CRT_ALLOCATION_NO_MAIN')
 marker='namespace mw34::m4_crt_heap_return {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}'
 assert s.count(marker)==1;s=s.replace(marker,marker+'\nnamespace mw34::m4_crt_allocation {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}')
 s=s.replace('require(!std::filesystem::exists(directory)&&std::filesystem::create_directory(directory),"Fresh output directory required");',
  'require(!std::filesystem::exists(directory),"Fresh direct output publication required");capture_direct::Options capture_options;capture_options.reports_root=std::filesystem::current_path()/"reports";auto sink=capture_direct::Writer::try_create(directory,capture_options);require(bool(sink),"Checked direct capture construction");direct_writer=sink.get();direct_root=directory;direct_failed=false;')
 a=s.index(' filename_units_directory=directory/"units";');b=s.index(' for(unsigned scenario=',a)
 s=s[:a]+s[b:]
 s=s.replace('scenario<36','scenario<18').replace('scenario<24?0:scenario+133','scenario<6?0:scenario+163').replace('(scenario<24?scenario:0)','(scenario<6?scenario:0)')
 s=s.replace('require(std::filesystem::create_directory(row),"Fresh scenario");','')
 s=s.replace('auto&heap_return=mainargs.heap_return;','auto&heap_return=mainargs.heap_return;auto&allocation=mainargs.allocation;allocation.configure_request(std::array<unsigned,6>{0,1,24,31,32,4096}[scenario<6?scenario:2]);')
 s=s.replace('hr::admitted_binding=&heap_return;boundary','hr::admitted_binding=&heap_return;al::binding=&allocation;al::admitted_binding=&allocation;boundary')
 a=s.index('  std::array<unsigned,72>heap_return_job');b=s.index('  const auto state_copy=context.state();',a)
 old_gate=s[a:s.index('  require(!heap_return.active',a)]
 s=s[:a]+old_gate+(HERE/'worker_gate.inc').read_text()+s[b:]
 s=s.replace('snapshot(r,row,"retry-after");hr::binding=nullptr;','snapshot(r,row,"retry-after");al::binding=nullptr;al::admitted_binding=nullptr;hr::binding=nullptr;')
 tail=' fresh_output(directory/"COMPLETE",{reinterpret_cast<const std::byte*>("COMPLETE"),8});return 0;'
 assert s.count(tail)==1
 s=s.replace(tail,' require(!direct_failed,"Direct capture failed without publication");fresh_output(directory/"COMPLETE",{reinterpret_cast<const std::byte*>("COMPLETE"),8});require(!direct_failed,"Direct completion append failed");const auto*closed=sink->try_finish();require(closed!=nullptr,"Checked strict bundle finalization");direct_writer=nullptr;return 0;')
 (HERE/'main_v2.inc').write_text(s)
if __name__=='__main__':main()
