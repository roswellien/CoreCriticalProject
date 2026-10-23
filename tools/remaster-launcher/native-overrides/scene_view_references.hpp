#pragma once
#include <deque>
#include <memory>
#include <utility>

namespace mw34::submission {
template<class Value,bool Reuse> class SceneViewReferences;

// The disabled path retains the original per-entry shared ownership operations.
template<class Value> class SceneViewReferences<Value,false> {
  public:
    using Reference=std::shared_ptr<const Value>;
    Reference borrow(const Reference& value){return value;}
    template<class Source> Reference own(std::shared_ptr<Source>&& value){return Reference(std::move(value));}
    const Reference& shared(const Reference& value)const{return value;}
};

// Borrow existing scene-owned shared_ptr objects only while the atmosphere pass
// keeps its Draw vector and those source fields unchanged. Newly synthesized
// model-camera views need ownership here; deque insertion preserves references.
// Only shared() copies ownership into an output draw. References never escape
// the pass, while an output shared_ptr remains valid independently of this pool.
template<class Value> class SceneViewReferences<Value,true> {
    using Owner=std::shared_ptr<const Value>;
    std::deque<Owner> synthesized;
  public:
    struct Reference {
        const Owner* owner{};
        explicit operator bool()const{return owner && bool(*owner);}
        const Value* operator->()const{return owner->get();}
        void reset(){owner=nullptr;}
    };
    SceneViewReferences()=default;
    SceneViewReferences(const SceneViewReferences&)=delete;
    SceneViewReferences& operator=(const SceneViewReferences&)=delete;
    Reference borrow(const Owner& value)const{return value?Reference{&value}:Reference{};}
    template<class Source> Reference own(std::shared_ptr<Source>&& value){
        if(!value)return {};
        synthesized.emplace_back(std::move(value));return {&synthesized.back()};
    }
    const Owner& shared(Reference value)const{
        static const Owner empty;
        return value.owner?*value.owner:empty;
    }
};
}
