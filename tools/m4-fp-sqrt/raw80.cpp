// Windows x64 normal pointer ABI. No C++ long double or guest-code execution.
#include <cstdint>
struct Raw80 {std::uint8_t bytes[10];};
extern "C" void mw34_sqrt_primitive_admit();
extern "C" void mw34_actual_fsqrt_raw80(const Raw80 *input,Raw80 *output){
    mw34_sqrt_primitive_admit();
    // Both operands are owned LLVM allocas, with exactly ten observed bytes.
    // The scalar FP environment is supplied and restored by the outer scope.
    __asm__ volatile("fldt %1\n\tfsqrt\n\tfstpt %0":"=m"(*output):"m"(*input):"memory","st");
}
