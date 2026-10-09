#pragma once
#include "runtime.hpp"
#include <string_view>
namespace mw34::m4_initializer_chain {
// Evidence identities identify the exact linked compiled object and reviewed
// component gate. Registration is separate from running the initializer ledger.
void register_component(mw34::m4_runtime::Runtime &,std::string_view object_sha256,std::string_view gate_report_sha256);
} // namespace mw34::m4_initializer_chain
