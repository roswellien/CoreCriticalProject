#include "../native-overrides/scene_view_references.hpp"
#include <array>
#include <cstdio>
#include <stdexcept>
#include <type_traits>
#include <vector>
struct View{std::array<float,12> camera{};std::array<float,6> projection{};};
unsigned checks{};
void require(bool good){++checks;if(!good)throw std::runtime_error("Atmosphere reference lifetime check failed");}
template<bool Reuse>void check(){
    using Store=mw34::submission::SceneViewReferences<View,Reuse>;
    Store store;std::shared_ptr<const View> source=std::make_shared<View>();
    const auto before=source.use_count();
    std::vector<typename Store::Reference> work;
    for(unsigned i=0;i<10000;++i)work.push_back(store.borrow(source));
    require(source.use_count()==before+(Reuse?0:10000));
    for(const auto& ref:work)require(ref && ref->projection==source->projection && store.shared(ref)==source);
    typename Store::Reference empty;require(!empty && !store.shared(empty));
    std::shared_ptr<const View> null;require(!store.borrow(null));
    std::vector<typename Store::Reference> generated;
    for(unsigned i=0;i<10000;++i){auto value=std::make_shared<View>();value->camera[0]=float(i);generated.push_back(store.own(std::move(value)));require(!value);}
    for(unsigned i=0;i<generated.size();++i)require(generated[i]->camera[0]==float(i));
    auto current=generated.front();current.reset();require(!current && generated.front());
    std::shared_ptr<const View> escaped;
    {Store temporary;auto value=std::make_shared<View>();value->projection[0]=17;auto ref=temporary.own(std::move(value));escaped=temporary.shared(ref);}
    require(escaped->projection[0]==17);
}
int main(){
    static_assert(sizeof(mw34::submission::SceneViewReferences<View,true>::Reference)==sizeof(void*));
    static_assert(!std::is_copy_constructible_v<mw34::submission::SceneViewReferences<View,true>>);
    check<false>();check<true>();std::printf("%u atmosphere view lifetime checks passed\n",checks);
}
