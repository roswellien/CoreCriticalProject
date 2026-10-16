#pragma once
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <vector>

namespace mw34::world {
// The caller supplies a freshly read source snapshot. Addresses are lookup
// hints only; exact source bytes establish whether a decoded mesh can be reused.
template<class T> class SnapshotCache {
    struct Entry { std::vector<unsigned char> bytes;std::shared_ptr<const T> value; };
    std::map<std::uint32_t,Entry> entries_;
    std::size_t maximum_entries_,maximum_bytes_,bytes_{};
public:
    SnapshotCache(std::size_t entries,std::size_t bytes):maximum_entries_(entries),maximum_bytes_(bytes){}
    std::shared_ptr<const T> find(std::uint32_t key,const std::vector<unsigned char>& bytes)const {
        const auto found=entries_.find(key);
        return found!=entries_.end()&&found->second.bytes==bytes?found->second.value:nullptr;
    }
    void put(std::uint32_t key,std::vector<unsigned char> bytes,std::shared_ptr<const T> value) {
        if(!value)throw std::runtime_error("World snapshot cache cannot store an empty value");
        const auto previous=entries_.find(key);
        const std::size_t old_bytes=previous==entries_.end()?0:previous->second.bytes.size();
        if((previous==entries_.end()&&entries_.size()>=maximum_entries_)||bytes.size()>maximum_bytes_-(bytes_-old_bytes))
            throw std::runtime_error("World snapshot cache capacity exceeded");
        const auto total=bytes_-old_bytes+bytes.size();
        entries_.insert_or_assign(key,Entry{std::move(bytes),std::move(value)});
        bytes_=total;
    }
    std::size_t size()const{return entries_.size();}
    std::size_t bytes()const{return bytes_;}
};

inline std::optional<std::size_t> polygon_slot(std::uint32_t base,std::size_t count,std::uint32_t address) {
    if(address<base)return {};
    const auto distance=std::uint64_t(address)-base;
    if(distance%36||distance/36>=count)return {};
    return std::size_t(distance/36);
}
}
