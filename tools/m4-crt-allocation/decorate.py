"""Add functional ownership observers in the fresh, mutable candidate only."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 p=HERE/'allocation_binding.inc';s=p.read_text()
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a[:90],s.count(a));s=s.replace(a,b)
 rep(' if(extra)extra(*this,point);', '''
 if(point==27&&control==169)throw std::runtime_error("Injected observer fault after provisional full HeapAlloc ownership");
 if(point==27&&control==170)allocation_registry[4]^=1;
 if(point==32&&control==171)m.protect({allocation_address},Permissions::read);
 if(point==34&&control==172)m.store<unsigned>({allocator_frame_-60},allocation_address+4);
 if(point==25&&control==173)m.protect(runtime.fs_base(),Permissions::read);
 if(point==2&&control==174&&state.gpr.rip.dword==0x780012f9)throw std::runtime_error("Injected fault after genuine FS chain registration store");
 if(point==30&&control==175)m.store<unsigned>(runtime.fs_base(),fs_expected_^1);
 if(point==35&&control==176)throw std::runtime_error("Injected fault after actual successful HeapFree");
 if(point==31&&control==177)throw std::runtime_error("Injected fault after genuine malloc export RET with live pointer");
 if(point==36&&control==178&&allocation_phase_private_==4)free_api();
 if(point==34&&control==179)owner=nullptr;
 if(point==10&&control==180)throw std::runtime_error("Injected terminal fault after allocation and heap cleanup");
 if(extra)extra(*this,point);''')
 rep('const auto old_create_before=create_before;',
 '''const auto old_alloc_registry=allocation_registry;const auto old_alloc_witness=allocation_witness;const auto old_external_accesses=external_accesses;const auto old_external_projections=external_projections;
 const auto old_alloc_initial=allocation_initial;const auto old_alloc_pattern=allocation_pattern;const auto old_alloc_before=alloc_before;const auto old_alloc_after=alloc_after;const auto old_free_before=free_before;const auto old_free_after=free_after;
 const auto old_alloc_public=std::array<unsigned,12>{requested_size,allocation_phase,allocation_guest,allocation_extent,allocation_output_count,external_count,unsigned(caller_cleaned),unsigned(malloc_returned),unsigned(client_verified),unsigned(free_returned),unsigned(null_free_returned),unsigned(batch_complete)};
 const auto old_create_before=create_before;''')
 rep(' if(!terminal&&!cleaning){guard();source_identity();}', '''
 if(old_alloc_registry!=allocation_registry||old_alloc_witness!=allocation_witness||old_alloc_initial!=allocation_initial||old_alloc_pattern!=allocation_pattern||
  std::memcmp(old_external_accesses.data(),external_accesses.data(),sizeof(external_accesses))||old_external_projections!=external_projections||
  old_alloc_before!=alloc_before||old_alloc_after!=alloc_after||old_free_before!=free_before||old_free_after!=free_after||
  old_alloc_public!=std::array<unsigned,12>{requested_size,allocation_phase,allocation_guest,allocation_extent,allocation_output_count,external_count,unsigned(caller_cleaned),unsigned(malloc_returned),unsigned(client_verified),unsigned(free_returned),unsigned(null_free_returned),unsigned(batch_complete)})
  deny("Allocation observer changed actual API identity, private ownership mirrors, external frame ledger or progress",allocation_address);
 if(!terminal&&!cleaning){guard();source_identity();}''')
 # Validate import name/hint as well as raw thunk values using a fresh generic
 # copy of the already strict PE parser, not a host resolver for guest IATs.
 a=s.index(' unsigned original_query_import(');b=s.index('\nBinding::Binding(',a)
 helper=s[a:b].replace('original_query_import(std::span<const std::byte>b)',
  'original_allocation_import(std::span<const std::byte>b,const char*requested,unsigned slot,unsigned hint)')
 helper=helper.replace('text(value+2)=="GetVersionExA"','text(value+2)==requested')
 helper=helper.replace('mw34::m4_crt_allocation::query_iat','slot').replace('!=373','!=hint')
 s=s[:b]+helper+s[b:]
 rep('if(p.dword({alloc_iat})!=alloc_raw||p.dword({free_iat})!=free_raw)',
     'if(original_allocation_import(provider,"HeapAlloc",alloc_iat,409)!=alloc_raw||original_allocation_import(provider,"HeapFree",free_iat,415)!=free_raw||p.dword({alloc_iat})!=alloc_raw||p.dword({free_iat})!=free_raw)')
 p.write_text(s)
if __name__=='__main__':main()
