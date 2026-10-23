namespace {
thread_local std::filesystem::path filename_units_directory;
void filename_units(){
 const auto named=GetModuleHandleW(L"kernel32.dll");const auto procedure=GetProcAddress(named,"GetModuleFileNameA");
 const auto before=fd::host_identity(procedure,named,"GetModuleFileNameA");const auto worker=fd::module_identity(GetModuleHandleW(nullptr));
 std::array<std::byte,260>seed{};for(unsigned n=0;n<seed.size();++n)seed[n]=std::byte((n*31+17)&255);
 for(unsigned size:std::array<unsigned,4>{0,1,8,260}){
  const auto witness=fn::native_filename(size,0xface0123,seed,procedure);raw_output(filename_units_directory/("capacity-"+std::to_string(size)+".bin"),witness);
  require(std::equal(witness.after.begin()+size,witness.after.end(),witness.before.begin()+size),"Actual API leaves bytes beyond declared capacity untouched");
  if(size==260){require(witness.result>0&&witness.result<size&&witness.after[witness.result]==std::byte{},"Actual native worker filename fits measured service capacity");require(std::equal(witness.after.begin()+witness.result+1,witness.after.end(),witness.before.begin()+witness.result+1),"Actual success retains complete buffer tail");}
  else if(size){require(witness.result==size&&witness.last_error==ERROR_INSUFFICIENT_BUFFER&&witness.after[size-1]==std::byte{},"Actual modern Windows filename truncation result/error/NUL contract");}
  else require(witness.result==0,"Actual zero capacity produces zero result; error separately witnessed");
 }
 const auto after=fd::host_identity(procedure,named,"GetModuleFileNameA");const auto worker_after=fd::module_identity(GetModuleHandleW(nullptr));require(before==after&&worker==worker_after,"Actual unit API/worker identity retained");
 raw_output(filename_units_directory/"api-before.bin",api(before));raw_output(filename_units_directory/"api-after.bin",api(after));raw_output(filename_units_directory/"module-before.bin",module(worker));raw_output(filename_units_directory/"module-after.bin",module(worker_after));
}
}
