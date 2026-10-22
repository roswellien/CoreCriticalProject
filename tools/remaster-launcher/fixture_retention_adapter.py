"""Authored adapter for the UV-aware native fixture manager; no game execution."""
from pathlib import Path

SELECT=r'''    std::vector<effects::Light> select_lights(const Point& eye,unsigned limit,float strength=1,float range_scale=1,float retain_distance=160,float fade_distance=32){
        // View-frustum visibility never deletes a fixture. Invalidated original
        // sources still remove it immediately; distant unseen entries can expire.
        std::erase_if(fixtures_,[&](const auto& f){const float keep=std::max(retain_distance,f.def->radius*range_scale*4);return f.last_frame!=frame_&&effects::distance2(eye,f.position)>keep*keep;});
        struct Candidate{float score;effects::Light light;size_t index;};std::vector<Candidate> picks;
        for(size_t index=0;index<fixtures_.size();++index){auto& f=fixtures_[index];const auto& d=*f.def;
            const float radius=d.radius*range_scale,radius2=radius*radius,distance2=effects::distance2(eye,f.position);
            const float distance=std::sqrt(distance2);
            const float keep=std::max(retain_distance,radius*4),band=std::max(fade_distance,radius);
            float fade=std::clamp((keep-distance)/band,0.f,1.f);fade=fade*fade*(3-2*fade);
            const float arrival=std::clamp(float((time_-f.first_seen)/.25),0.f,1.f);
            const float power=d.intensity*strength*fade*arrival;
            if(power<=0||radius<=0)continue;effects::Light l;l.start={f.position[0],f.position[1],f.position[2],radius};
            l.end=d.is_spot?std::array<float,4>{f.direction[0],f.direction[1],f.direction[2],float(effects::LightKind::spot)}:std::array<float,4>{f.position[0],f.position[1],f.position[2],float(effects::LightKind::point)};
            l.color={d.color[0],d.color[1],d.color[2],power};
            // Keep incumbents unless a new candidate is materially stronger.
            picks.push_back({power*radius2/(radius2+distance2)*(f.selected?1.25f:1.f),l,index});
        }
        std::stable_sort(picks.begin(),picks.end(),[](const auto&a,const auto&b){return a.score>b.score;});
        for(auto& f:fixtures_)f.selected=false;
        std::vector<effects::Light> out;for(size_t i=0;i<std::min<size_t>(limit,picks.size());++i){fixtures_[picks[i].index].selected=true;out.push_back(picks[i].light);}return out;
    }
'''

def adapt(text):
    assert 'emission_regions' in text and 'std::uint64_t owner{};' in text
    text=text.replace('// anonymous billboards exist only in their submission frame.','// anonymous observations are retained within the configured player distance.')
    text=text.replace('    std::uint64_t owner{};','    std::uint64_t owner{};\n    double first_seen{};bool selected{};')
    text=text.replace('    std::vector<ActiveFixture> fixtures_;','    std::vector<ActiveFixture> fixtures_;\n    unsigned frame_{};double time_{};')
    old='    void begin_frame(unsigned frame){std::erase_if(fixtures_,[&](const auto& f){return !f.source&&f.last_frame!=frame;});}'
    assert text.count(old)==1
    text=text.replace(old,'    void begin_frame(unsigned frame,double time=0){frame_=frame;time_=time;}')
    text=text.replace('old={c,normal,&def,frame,source};','const double first=old.first_seen;const bool selected=old.selected;old={c,normal,&def,frame,source,0,first,selected};')
    text=text.replace('*oldest={c,normal,&def,frame,source};','*oldest={c,normal,&def,frame,source,0,time_};')
    text=text.replace('fixtures_.push_back({c,normal,&def,frame,source});','fixtures_.push_back({c,normal,&def,frame,source,0,time_});')
    text=text.replace('old={position,normal,&def,frame,id,owner};','const double first=old.first_seen;const bool selected=old.selected;old={position,normal,&def,frame,id,owner,first,selected};')
    text=text.replace('fixtures_.push_back({position,normal,&def,frame,id,owner});','fixtures_.push_back({position,normal,&def,frame,id,owner,time_});')
    text=text.replace('fixtures_.size()>=512','fixtures_.size()>=4096').replace('fixtures_.size()<512','fixtures_.size()<4096')
    start=text.index('    std::vector<effects::Light> select_lights(')
    end=text.index('    struct UvPoint',start)
    return text[:start]+SELECT+'\n'+text[end:]
