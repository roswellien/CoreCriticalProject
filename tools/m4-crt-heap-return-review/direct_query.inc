// Counterfactual host-only failure diagnostics. These are not source query calls
// and provide no coverage of an integrated selector branch.
struct ReviewDirectQuery {
 std::array<std::byte,148>before{};alignas(OSVERSIONINFOA)std::array<std::byte,148>after{};unsigned supplied_size{},incoming{},result{},api_error{},restored{};
};
thread_local ReviewDirectQuery*review_direct{};
void review_direct_query(){auto&w=*review_direct;fn::LastErrorBoundary errors(&w.restored);InvocationHostBoundary host;w.incoming=GetLastError();
 w.result=static_cast<unsigned>(::GetVersionExA(reinterpret_cast<OSVERSIONINFOA*>(w.after.data())));w.api_error=GetLastError();
}
void review_direct_queries(){
 unsigned diagnostic{};for(unsigned size:{147U,0U}){++diagnostic;ReviewDirectQuery w;w.supplied_size=size;w.before.fill(std::byte{0xa5});review_put<unsigned>(w.before.data(),size);w.after=w.before;
  const auto row=review_directory/("direct-query-failure-"+std::to_string(diagnostic));review_need(std::filesystem::create_directory(row),"Fresh bounded independent host-only query diagnostic");
  const auto before=hm::measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));
  Job job;job.unit=&review_direct_query;review_direct=&w;const auto error=0xcada0000U+diagnostic;SetLastError(error);review_boundary(job,row,"query",review_scenarios+diagnostic);review_direct=nullptr;
  const auto after=hm::measured_api("GetVersionExA",reinterpret_cast<std::uintptr_t>(&::GetVersionExA));
  review_need(job.ok&&!job.denied&&w.result==0,"Actual malformed OSVERSIONINFOA size fails in private host scratch");review_need(w.incoming==error&&w.restored==error&&fn::outer_error_before==fn::outer_error_after&&fn::outer_error_before==error,"Actual nonzero host-only diagnostic caller error is restored");review_need(before==after,"Actual host-only named query export identity is unchanged");
  raw_output(row/"scratch-before.bin",w.before);raw_output(row/"scratch-after.bin",w.after);std::array<unsigned,8>status{1,size,148,w.incoming,w.result,w.api_error,w.restored,review_scenarios+diagnostic};raw_output(row/"status.bin",status);raw_output(row/"api-before.bin",review_api(before));raw_output(row/"api-after.bin",review_api(after));
 }
}
