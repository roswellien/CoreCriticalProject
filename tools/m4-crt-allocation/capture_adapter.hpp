#pragma once
#include "capture_direct_v3.hpp"
#include <sstream>
namespace {
thread_local capture_direct::Writer*direct_writer{};
thread_local std::filesystem::path direct_root;
thread_local bool direct_failed{};
void direct_append(const std::filesystem::path&p,const void*data,std::size_t bytes)noexcept{
 if(direct_failed)return;
 try{if(!direct_writer){direct_failed=true;return;}
 const auto relative=p.lexically_relative(direct_root);const auto name=relative.generic_string();
 if(relative.empty()||relative.is_absolute()){direct_failed=true;return;}
 if(!direct_writer->try_append(name,data,bytes))direct_failed=true;
 }catch(...){direct_failed=true;}
}
// Text stays in a bounded in-memory stream and joins the same strict archive;
// no file or directory is created for a row, phase, JSON or reason record.
class DirectText {
 std::filesystem::path path_;std::ostringstream text_;
 public:
 explicit DirectText(const std::filesystem::path&p):path_(p){}
 DirectText(const DirectText&)=delete;DirectText&operator=(const DirectText&)=delete;
 ~DirectText()noexcept{try{const auto s=text_.str();direct_append(path_,s.data(),s.size());}catch(...){direct_failed=true;}}
 template<class T>DirectText&operator<<(const T&value){text_<<value;return *this;}
 explicit operator bool()const noexcept{return bool(text_)&&!direct_failed;}
};
}
