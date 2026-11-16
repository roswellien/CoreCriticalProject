#pragma once

#include <cstdint>
#include <cstdio>

#if !defined(_WIN32)
#include <sys/types.h>
#endif

namespace platform::file_position {

inline int seek(std::FILE *file, std::int64_t offset, int origin) {
#if defined(_WIN32)
  return _fseeki64(file, offset, origin);
#else
  return ::fseeko(file, static_cast<off_t>(offset), origin);
#endif
}

inline std::int64_t tell(std::FILE *file) {
#if defined(_WIN32)
  return _ftelli64(file);
#else
  return static_cast<std::int64_t>(::ftello(file));
#endif
}

} // namespace platform::file_position
