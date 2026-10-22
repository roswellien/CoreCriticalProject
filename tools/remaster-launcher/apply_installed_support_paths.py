"""Bind original support images from explicit installed inputs on a fresh native snapshot."""
from pathlib import Path


def apply(path):
    path=Path(path);text=path.read_text()
    old='auto worker=read_file(argv[0]);auto mfc42=read_file(MW34_MFC42_PATH);auto msvcp50=read_file(MW34_MSVCP50_PATH);'
    new='''auto worker=read_file(argv[0]);
 const auto original_provider=[](const char* key,const char* development_path){
  const char* value=std::getenv(key);const char* required=std::getenv("MW34_REQUIRE_USER_PROVIDERS");
  if(required&&std::string(required)=="1")require(value&&*value,"Installed runtime requires explicit user-provided support images");
  const auto path=std::filesystem::path(value&&*value?value:development_path);
  require(std::filesystem::is_regular_file(path),"Required original support image is missing");return path.string();
 };
 const auto mfc_provider_path=original_provider("MW34_MFC42_IMAGE",MW34_MFC42_PATH);
 const auto msvcp_provider_path=original_provider("MW34_MSVCP50_IMAGE",MW34_MSVCP50_PATH);
 auto mfc42=read_file(mfc_provider_path.c_str());auto msvcp50=read_file(msvcp_provider_path.c_str());'''
    if text.count(old)!=1:raise ValueError('Expected exactly one current native provider read boundary')
    text=text.replace(old,new)
    old='{mf::base,MW34_MFC42_PATH},{0x780c0000U,MW34_MSVCP50_PATH}'
    new='{mf::base,mfc_provider_path.c_str()},{0x780c0000U,msvcp_provider_path.c_str()}'
    if text.count(old)!=1:raise ValueError('Expected exactly one current native module-path binding')
    path.write_text(text.replace(old,new))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path)
    apply(parser.parse_args().source)
