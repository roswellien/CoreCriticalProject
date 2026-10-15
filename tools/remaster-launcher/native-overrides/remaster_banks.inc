// Closed, launcher-verified texture bank map. Only named media reads are redirected.
std::string remaster_bank(const std::filesystem::path&path,const std::filesystem::path&game){
 static const auto banks=[](){std::map<std::string,std::string>result;const char*p=std::getenv("MW34_REMASTER_BANKS");if(!p)return result;std::ifstream f(p,std::ios::binary);
  auto bytes=[&](void*p,size_t n){if(!f.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Remaster bank map incomplete");};char magic[8];bytes(magic,8);if(std::memcmp(magic,"MWBANK1\0",8))throw std::runtime_error("Remaster bank map format mismatch");unsigned count;bytes(&count,4);if(!count||count>256)throw std::runtime_error("Remaster bank map count invalid");
  for(unsigned i=0;i<count;++i){unsigned a,b;bytes(&a,4);bytes(&b,4);if(!a||a>1024||!b||b>2048)throw std::runtime_error("Remaster bank path length invalid");std::string key(a,'\0'),value(b,'\0');bytes(key.data(),a);bytes(value.data(),b);
   if(key.find('\0')!=std::string::npos||value.find('\0')!=std::string::npos||key.find("..")!=std::string::npos||key.rfind("zbd/",0)!=0||!std::filesystem::is_regular_file(value)||!result.emplace(key,value).second)throw std::runtime_error("Remaster bank map path invalid");}
  if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Remaster bank map trailing data");return result;}();
 auto key=path.lexically_relative(game).generic_string();std::transform(key.begin(),key.end(),key.begin(),[](unsigned char c){return char(std::tolower(c));});auto it=banks.find(key);return it==banks.end()?path.string():it->second;
}
