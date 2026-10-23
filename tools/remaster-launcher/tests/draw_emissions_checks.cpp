#include "../native-overrides/draw_emissions.hpp"
#include <bit>
#include <cstring>
#include <iostream>
#include <utility>

namespace {
unsigned checks{};
void require(bool value) { ++checks;if(!value)throw std::runtime_error("Draw emission fixture failed"); }
using Store=mw34::submission::DrawEmissions;
struct Uniform { Store::Float4 emission_params{};std::array<Store::Float4,32> emission_regions{}; };
}
int main() {
 try {
  Store store;std::vector<Uniform> original;std::vector<std::uint32_t> indices;
  for(unsigned n=0;n<1000;++n) {
   Uniform value;const unsigned count=n%33;
   value.emission_params={float(count),std::bit_cast<float>(0x80000000U|n),0,0};
   for(unsigned i=0;i<count;++i)for(unsigned j=0;j<4;++j)
    value.emission_regions[i][j]=std::bit_cast<float>(0x7fc00001U+n*128+i*4+j);
   const auto index=store.capture(value.emission_params,{value.emission_regions.data(),count});
   indices.push_back(index);original.push_back(value);
   // The scene must own a copy, including unused zero tails.
   value.emission_regions={};value.emission_params={};
  }
  Store moved=std::move(store);
  require(moved.size()==1000);
  for(unsigned n=1000;n--;) {
   Uniform actual;moved.apply(indices[n],actual);
   require(!std::memcmp(&actual,&original[n],sizeof(actual)));
   moved.apply(Store::none,actual);Uniform empty;
   require(!std::memcmp(&actual,&empty,sizeof(actual)));
  }
  bool rejected=false;Uniform output;
  try {moved.apply(1000,output);}catch(const std::out_of_range&) {rejected=true;}
  require(rejected);
  std::array<Store::Float4,33> oversized{};rejected=false;
  try {moved.capture({},oversized);}catch(const std::runtime_error&) {rejected=true;}
  require(rejected&&moved.size()==1000);
  std::cout<<"Draw emission checks="<<checks<<" failures=0\n";
 }catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
