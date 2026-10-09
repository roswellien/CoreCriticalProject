#pragma once
#include "runtime.hpp"
#include <optional>

namespace mw34::m4_crt_data {
// This is an explicitly declared reference/projection fixture. It does not
// implement GetCommandLineA or run a native initialization writer.
struct ReferenceProjection {
    std::uint32_t observed_original_pointer{};
    GuestAddress owned_guest_pointer;
    std::vector<std::byte> observed_buffer;
    std::string original_measurement_sha256, original_buffer_sha256;
};
enum class DataFaultReason { unresolved_data, invalid_admission, changed_identity, memory_fault, poisoned };
class DataFault : public std::runtime_error {
  public:
    DataFault(DataFaultReason r,GuestAddress a,const std::string&w):std::runtime_error(w),reason(r),address(a){}
    DataFaultReason reason;GuestAddress address;
};
struct DataRecord {
    GuestAddress iat_slot,provider_global,owned_guest_pointer;
    std::uint32_t original_iat_value{},observed_original_pointer{},buffer_bytes{};
    std::string original_measurement_sha256,buffer_sha256;
    bool reference_projection_only=true;
    bool reference_projection_ready=false;
    bool production_initialized_service=false;
};

class DataImportRegistry {
  public:
    explicit DataImportRegistry(m4_runtime::Runtime&r):runtime_(r){}
    ~DataImportRegistry();
    DataImportRegistry(const DataImportRegistry&)=delete;DataImportRegistry&operator=(const DataImportRegistry&)=delete;
    DataImportRegistry(DataImportRegistry&&)=delete;DataImportRegistry&operator=(DataImportRegistry&&)=delete;
    void admit_reference_projection(std::span<const std::byte>exact_provider,ReferenceProjection projection);
    [[nodiscard]] std::uint32_t resolve_reference_load32(GuestAddress address);
    [[nodiscard]] const std::optional<DataRecord>&record()const noexcept{return record_;}
    [[nodiscard]] bool poisoned()const noexcept{return fault_.has_value();}
    [[nodiscard]] const std::optional<DataFault>&first_fault()const noexcept{return fault_;}
    static constexpr bool production_initialized_service=false;
  private:
    m4_runtime::Runtime&runtime_;std::optional<DataRecord>record_;std::vector<std::byte>owned_reference_;
    std::optional<DataFault>fault_;bool owns_global_{},owns_buffer_{};
    void integrity();
    [[noreturn]]void fail(DataFaultReason,GuestAddress,const char*);
    [[nodiscard]] const m4::ImportSymbol&named(const char*,GuestAddress);
};
} // namespace mw34::m4_crt_data
