"""Add an explicit private codec resource path to the current native host snapshot.

Apply only to a fresh copy of the selected host, preserving its other fixes.
The codec remains user-derived data consumed by existing translated code.
"""
from pathlib import Path


def apply(source):
    source=Path(source)
    text=source.read_text()
    old='''{const auto iv=(std::filesystem::absolute(argv[1]).parent_path().parent_path()/"local/mw3-staged/derived/Ir50_32.base11000000.dll").make_preferred();'''
    new='''{const char* configured_iv50=std::getenv("MW34_IV50_IMAGE");
  const auto iv=(configured_iv50&&*configured_iv50?std::filesystem::path(configured_iv50):
    std::filesystem::absolute(argv[1]).parent_path().parent_path()/"local/mw3-staged/derived/Ir50_32.base11000000.dll").make_preferred();
  if(configured_iv50&&*configured_iv50)require(std::filesystem::is_regular_file(iv),"Configured original movie decoder is missing");'''
    if text.count(old)!=1:raise ValueError('Expected one current native codec resource path')
    source.write_text(text.replace(old,new))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path)
    apply(parser.parse_args().source)
