// Optional, launcher-verified movie replacements. Used only by the AVI read service.
std::string cinematic_path(const std::string& original) {
 static const auto paths=[](){std::map<std::string,std::string> result;
  const char* p=std::getenv("MW34_CINEMATIC_PATHS");if(!p||!*p)return result;
  std::ifstream f(p,std::ios::binary);
  auto read=[&](void* out,size_t n){if(!f.read(static_cast<char*>(out),std::streamsize(n)))throw std::runtime_error("Cinematic map incomplete");};
  char magic[8];read(magic,8);if(std::memcmp(magic,"MWCINE1\0",8))throw std::runtime_error("Cinematic map format mismatch");
  unsigned count;read(&count,4);if(!count||count>64)throw std::runtime_error("Cinematic map count invalid");
  for(unsigned i=0;i<count;++i){unsigned a,b;read(&a,4);read(&b,4);
   if(!a||a>64||!b||b>2048)throw std::runtime_error("Cinematic map path length invalid");
   std::string key(a,'\0'),value(b,'\0');read(key.data(),a);read(value.data(),b);
   if(key.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_")!=std::string::npos||value.find('\0')!=std::string::npos||
      !std::filesystem::path(value).is_absolute()||!std::filesystem::is_regular_file(value)||!result.emplace(key,value).second)
    throw std::runtime_error("Cinematic map path invalid");
  }
  if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Cinematic map trailing data");return result;
 }();
 auto path=std::filesystem::path(original);auto ext=path.extension().string(),key=path.stem().string();
 for(char& c:ext)c=char(std::tolower(static_cast<unsigned char>(c)));
 for(char& c:key)c=char(std::tolower(static_cast<unsigned char>(c)));
 auto it=paths.find(key);return ext==".avi"&&it!=paths.end()?it->second:original;
}
