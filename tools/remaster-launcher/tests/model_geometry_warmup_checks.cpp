#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <vector>

// Exercise the actual stage include with size-only geometry fixtures. No GPU
// calls are replaced in production; native captures verify the upload path.
namespace mw34::vkscene {
struct ModelVertex { unsigned char bytes[32]; };
struct SizeOnlyVertices { std::size_t count; std::size_t size() const { return count; } };
struct ModelGeometry { SizeOnlyVertices vertices; };
struct Scene {
    bool frontend_canvas{}, hud{}, world_eye_valid{true};
    std::vector<std::shared_ptr<const ModelGeometry>> model_warmup;
};
struct Renderer { inline static bool enabled=true; static bool gpu_models(){return enabled;} };
}
struct Batch { std::shared_ptr<const mw34::vkscene::ModelGeometry> geometry; };
struct Models { bool loaded{}; std::vector<Batch> batches; };
Models models;
Models& override_state(){return models;}
struct Stage {
#include "../native-overrides/model_geometry_warmup.inc"
};
unsigned checks;
void require(bool condition){++checks;if(!condition)throw std::runtime_error("Model warmup check failed");}
int main(int argc,char**argv){
    const char* mode=argc>1?argv[1]:"1";
    _putenv_s("MW34_MODEL_GEOMETRY_PREWARM",mode);
    Stage stage;mw34::vkscene::Scene scene;
    if(!std::strcmp(mode,"invalid")){
        try{stage.model_geometry_prewarm(scene);}catch(const std::runtime_error&){return 0;}
        return 1;
    }
    auto geometry=std::make_shared<const mw34::vkscene::ModelGeometry>(mw34::vkscene::ModelGeometry{{32768}});
    models.batches.push_back({geometry});
    stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());
    models.loaded=true;
    if(!std::strcmp(mode,"0")){
        stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());require(!stage.model_geometry_prewarmed);
    }else{
        scene.frontend_canvas=true;stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());
        scene.frontend_canvas=false;scene.hud=true;stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());
        scene.hud=false;scene.world_eye_valid=false;stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());
        scene.world_eye_valid=true;mw34::vkscene::Renderer::enabled=false;
        stage.model_geometry_prewarm(scene);require(scene.model_warmup.empty());
        mw34::vkscene::Renderer::enabled=true;
        // 65 distinct MiB entries exceed the exact 64 MiB payload budget.
        models.batches.clear();models.batches.push_back({nullptr});
        for(unsigned i=0;i<65;++i)
            models.batches.push_back({std::make_shared<const mw34::vkscene::ModelGeometry>(mw34::vkscene::ModelGeometry{{32768}})});
        stage.model_geometry_prewarm(scene);require(scene.model_warmup.size()==64);require(stage.model_geometry_prewarmed);
        for(unsigned i=0;i<64;++i)require(scene.model_warmup[i]==models.batches[i+1].geometry);
        auto saved=scene.model_warmup;
        stage.model_geometry_prewarm(scene);require(scene.model_warmup==saved);
        mw34::vkscene::Scene next;stage.model_geometry_prewarm(next);require(next.model_warmup.empty());
    }
    std::printf("%u actual model warmup ownership, load-phase and budget checks passed (%s)\n",checks,mode);
}
