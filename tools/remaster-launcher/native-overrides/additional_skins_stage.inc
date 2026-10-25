struct AdditionalSkinState {
    bool loaded{};
    std::vector<mw34::skins::Addition> records;
    std::map<std::string,unsigned> selected;
    std::wstring preferences;
    std::set<std::pair<unsigned,unsigned>> announced,verified;
};
AdditionalSkinState additional_skins;
std::wstring additional_skin_wide(const std::string& text) {
    const int size=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),int(text.size()),nullptr,0);
    if(size<=0)throw std::runtime_error("Additional skins: invalid UTF-8");
    std::wstring out(size,L'\0');MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),int(text.size()),out.data(),size);return out;
}
void additional_skins_read() {
    auto& a=additional_skins;if(a.loaded)return;a.loaded=true;
    const char* path=std::getenv("MW34_ADDITIONAL_SKINS");if(!path||!*path)return;
    std::ifstream file(std::filesystem::path(additional_skin_wide(path)),std::ios::binary);
    a.records=mw34::skins::read_additions(file);
    if(const char* p=std::getenv("MW34_SKIN_PREFERENCES");p&&*p)a.preferences=additional_skin_wide(p);
    for(unsigned i=0;i<a.records.size();++i){const auto& r=a.records[i];bool supported=false;
        for(const auto& model:override_models)if(r.chassis==model.id && override_mesh_env(model))supported=true;
        if(!supported)throw std::runtime_error("Additional skin requires an enabled model: "+r.name);
        additional_skin_wide(r.name);additional_skin_wide(r.id);
        if(!a.preferences.empty()){wchar_t saved[256]{};
            GetPrivateProfileStringW(L"MW3",additional_skin_wide(r.chassis).c_str(),L"",saved,256,a.preferences.c_str());
            if(additional_skin_wide(r.id)==saved)a.selected[r.chassis]=8+i;
        }
    }
    std::fprintf(stderr,"Additional skins: %zu registered for Mech Lab\n",a.records.size());
}
void additional_skins_load(const OverrideModel& model,size_t first,size_t end,unsigned requested=~0U) {
    additional_skins_read();
    for(unsigned i=0;i<additional_skins.records.size();++i){const auto& r=additional_skins.records[i];
        if(r.chassis==model.id&&(requested==~0U||requested==8+i))override_load_textures(model,first,end,nullptr,8+i,(model.lod?r.distance:r.close).c_str());}
}
unsigned additional_skin_for(unsigned original,unsigned root,unsigned model,bool preview) {
    const auto& id=override_models.at(model).id;
    const auto found=additional_skins.selected.find(id);
    const std::optional<unsigned> selected=found==additional_skins.selected.end()?std::nullopt:std::optional<unsigned>(found->second);
    const bool player=!frontend_on()&&root&&root==photo_replay_player_root_node();
    // Frontend contains presentation models, never live enemy actors. In HUD
    // condition previews only the left/player model may use the selected skin.
    const bool local_preview=frontend_on()||(preview&&override_state().preview_role==WideLeft);
    auto result=mw34::skins::selection(original,selected,player,local_preview);
    // An added appearance must have complete textures for this exact LOD.
    if(selected&&(player||local_preview)&&result&&!additional_skins.verified.count({model,result})){
        bool seen=false;
        for(const auto& batch:override_state().batches)if(batch.model==model&&batch.texture>=0){seen=true;
            if(result>=batch.skin_textures.size()||batch.skin_textures[result]<0)
                throw std::runtime_error("Selected mech skin textures are unavailable");}
        if(!seen)throw std::runtime_error("Selected mech skin has no model materials");
        additional_skins.verified.emplace(model,result);
    }
    if(result>=8 && additional_skins.announced.emplace(root,result).second)
        std::fprintf(stderr,"Additional skin applied: %s root=0x%08x chassis=%s player=%u preview=%u\n",
            additional_skins.records.at(result-8).id.c_str(),root,id,player,local_preview);
    return result;
}
