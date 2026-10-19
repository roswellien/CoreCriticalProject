#include "effects.hpp"
#include "flow.hpp"
#include <iostream>
#include <limits>
#include <string>
using namespace mw34::effects_lab;
static unsigned checks=0;
static void require(bool b,const char* message){++checks;if(!b)throw std::runtime_error(message);}
template<class F> static void rejects(F f){bool rejected=false;try{f();}catch(const std::invalid_argument&){rejected=true;}require(rejected,"Malformed input accepted");}
static Event shot(std::uint64_t source=1){return {1,{source,1},Kind::ppc,.1,1.1,{0,1,0},{10,0,0}};}
int main() try {
    System s(1);
    require(s.submit(shot())==Submit::accepted,"Valid event rejected");
    auto expected=s.sample(.5);
    require(!expected.particles.empty()&&expected.lights.size()==1,"PPC missing particles/light");
    // Sampling/rendering cannot spawn particles, advance RNG or change state.
    for(int i=0;i<144;++i)(void)s.sample(static_cast<double>(i)/144.);
    require(s.sample(.5).particles==expected.particles && s.sample(.5).lights==expected.lights,"Render cadence changes effect state");
    require(s.sample(.5).ribbons==expected.ribbons&&!expected.ribbons.empty(),"Connected PPC trail missing or render dependent");
    require(s.submit(shot())==Submit::duplicate_or_stale,"Duplicate callback respawns emitter");
    require(s.sample(.5).particles==expected.particles,"Duplicate changes particles");
    require(s.sample(.05).particles.empty(),"Effect drawn before activation");
    require(s.sample(1.1).lights.empty(),"Projectile light outlives original end");
    require(s.sample(1.8).particles.empty(),"Particle tails never expire");
    auto newer=shot();newer.key.generation=2;
    require(s.submit(newer)==Submit::accepted,"Reused source generation rejected");
    require(s.submit(shot())==Submit::duplicate_or_stale,"Old source resurrected");
    require(!s.stop(2,newer.key,.5),"Other scene can stop effect");
    require(s.stop(1,newer.key,.5),"Known effect stop failed");
    auto tailSnapshot=s.sample(.6);
    require(std::none_of(tailSnapshot.lights.begin(),tailSnapshot.lights.end(),[&](auto l){return l.key==newer.key;}),"Stopped source still emits light");
    require(std::any_of(tailSnapshot.particles.begin(),tailSnapshot.particles.end(),[&](auto p){return p.key==newer.key;}),"Stop incorrectly deletes existing trail");
    s.retire_before(5);
    require(s.active_records()==0,"Expired events retained");
    require(s.submit(newer)==Submit::duplicate_or_stale,"Retirement loses reuse tombstone");
    s.reset(2);
    require(s.submit(shot())==Submit::wrong_scene,"Mission reload accepts stale event");
    require(s.sample(.5).particles.empty(),"Mission reload retains particles");
    rejects([&]{s.reset(2);});
    System limited(1,{1,1,3,0});
    require(limited.submit(shot())==Submit::accepted,"Bounded initial event rejected");
    require(limited.submit(shot(2))==Submit::capacity,"Event capacity ignored");
    require(limited.sample(.5).particles.size()==3 && limited.sample(.5).omitted_particles>0,"Particle budget not enforced");
    require(limited.sample(.5).lights.empty()&&limited.sample(.5).omitted_lights==1,"Light budget not enforced");
    limited.retire_before(5);
    require(limited.submit(newer)==Submit::accepted,"Rejected event consumed generation/capacity");
    System a(1,{8,8,7,1}),b(1,{8,8,7,1});
    require(a.submit(shot(2))==Submit::accepted && a.submit(shot(1))==Submit::accepted,"Order setup failed");
    require(b.submit(shot(1))==Submit::accepted && b.submit(shot(2))==Submit::accepted,"Order setup failed");
    require(a.sample(.5).particles==b.sample(.5).particles&&a.sample(.5).lights==b.sample(.5).lights,"Budget selection depends on submission order");
    System burst(1);auto blast=shot();blast.kind=Kind::explosion;blast.end=blast.begin;
    require(burst.submit(blast)==Submit::accepted,"Instantaneous burst rejected");
    require(!burst.sample(.2).lights.empty(),"Instantaneous burst lacks light envelope");
    require(burst.stop(1,blast.key,.25),"Burst stop failed");
    require(burst.sample(.3).lights.empty()&&!burst.sample(.3).particles.empty(),"Burst stop must extinguish light but retain born particle tails");
    for(unsigned k=0;k<8;++k){
        System profile(1);auto e=shot();e.kind=static_cast<Kind>(k);
        require(profile.submit(e)==Submit::accepted,"Profile rejected");
        for(unsigned frame=0;frame<360;++frame){
            auto snap=profile.sample(static_cast<double>(frame)/60.);
            for(const auto& p:snap.particles)
                require(finite(p.position)&&finite(p.color)&&std::isfinite(p.size)&&p.size>0&&p.alpha>=0&&p.alpha<=1,"Invalid particle output");
            for(const auto& l:snap.lights)
                require(finite(l.position)&&finite(l.color)&&l.radius>0&&l.intensity>0,"Invalid light output");
            for(const auto& r:snap.ribbons){
                require(r.points.size()>=2&&r.points.size()<=65&&finite(r.color)&&r.width>0&&r.alpha>=0&&r.alpha<=1,"Invalid ribbon output");
                for(auto p:r.points)require(finite(p),"Nonfinite connected trail");
            }
        }
        require(profile.sample(6).particles.empty()&&profile.sample(6).lights.empty(),"Profile never expires");
    }
    System invalid(1);
    for(unsigned field=0;field<6;++field){
        auto e=shot();
        switch(field){case 0:e.begin=std::numeric_limits<double>::quiet_NaN();break;
        case 1:e.position.x=std::numeric_limits<double>::infinity();break;
        case 2:e.end=-1;break;case 3:e.key.source=0;break;case 4:e.kind=static_cast<Kind>(77);break;
        case 5:e.end=40;break;}
        rejects([&]{(void)invalid.submit(e);});
    }
    rejects([&]{(void)invalid.sample(-1);});
    rejects([&]{(void)invalid.stop(1,{1,1},std::numeric_limits<double>::quiet_NaN());});
    require(invalid.active_records()==0,"Malformed inputs mutate state");
    System capped(1,{8,8,0,0,0});
    require(capped.submit(shot())==Submit::accepted,"Ribbon budget setup failed");
    require(capped.sample(.5).ribbons.empty()&&capped.sample(.5).omitted_ribbons==3,"Ribbon budget ignored");
    System green(1);auto gs=shot();gs.kind=Kind::gauss;
    require(green.submit(gs)==Submit::accepted,"Gauss setup failed");
    const auto g=green.sample(.5);
    require(g.lights.size()==1&&g.lights[0].color.y>g.lights[0].color.x*3,"Gauss no longer has green reference identity");
    require(g.ribbons.size()==1&&g.ribbons[0].points.front().x<g.ribbons[0].points.back().x,"Gauss coherent flight cue absent");
    for(Kind kind:{Kind::ppc_impact,Kind::gauss_impact}){
        System heavy(1);auto hit=shot();hit.kind=kind;hit.end=hit.begin;
        require(heavy.submit(hit)==Submit::accepted,"Heavy impact setup failed");
        const auto snap=heavy.sample(.3);
        require(snap.particles.size()>(kind==Kind::ppc_impact?30U:60U),"Heavy impact lacks ejecta");
        if(kind==Kind::ppc_impact){
            require(snap.ribbons.size()==24,"PPC outward discharge/fork count changed");
            require(snap.ribbons.front().points.size()==17,"PPC missing outward lightning channel");
            for(std::size_t i=0;i<snap.ribbons.size();i+=2){
                require(snap.ribbons[i].points.front()==hit.position,"PPC discharge arrives from outside instead of originating at hit");
                require(snap.ribbons[i+1].points.front()==snap.ribbons[i].points[7],"Electrical fork detached from outward channel");
            }
            for(const auto& r:snap.ribbons)require(!(r.points.front()==r.points.back()),"PPC lightning regressed to closed blast rings");
            require(lightning_pulse(.22)>lightning_pulse(.13)*2,"PPC restrike pulse missing");
            double radius=0;
            for(auto p:snap.ribbons.front().points){const auto d=p+hit.position*(-1);radius=std::max(radius,std::sqrt(d.x*d.x+d.y*d.y+d.z*d.z));}
            require(radius>2.0,"Electrical impact failed to reach enlarged scale");
            require(snap.lights.size()==1&&snap.lights[0].radius>=7,"Enlarged electrical impact light request missing");
        } else {
            require(snap.ribbons.empty(),"Kinetic Gauss impact retains energy rings/arcs");
            require(heavy.sample(.5).lights.empty(),"Gauss hot burst light outlives the hot body");
            unsigned debris=0,dust=0,hot=0;
            for(const auto& p:snap.particles){
                if(p.layer==Layer::debris){++debris;require(p.position.x<hit.position.x,"Slug fragments do not rebound from hit");}
                if(p.layer==Layer::smoke)++dust;
                if(p.layer==Layer::spark)++hot;
                require(p.color.y<=p.color.x*1.05,"Kinetic impact retains green energy color");
            }
            require(debris>50&&dust>40&&hot>15,"Ablative impact missing broad fragment/dust burst");
            unsigned incandescent=0;
            for(const auto& p:snap.particles)if(p.layer==Layer::hot_material)++incandescent;
            require(incandescent==25,"Gauss lacks visible hot body and glowing fragments");
            unsigned shower=0,embers=0;
            for(const auto& p:snap.particles)if(p.ordinal>=0xfffe0000U&&p.ordinal<0xfffe00a0U){
                ++shower;if(p.layer==Layer::glow)++embers;
                require(p.position.x<hit.position.x,"Added spark shower travels into armor");
            }
            require(shower==160&&embers==40,"Gauss spark/ember shower missing");
            const auto emberTail=heavy.sample(.6);
            require(std::any_of(emberTail.particles.begin(),emberTail.particles.end(),[](const auto& p){
                return p.ordinal>=0xfffe0000U&&p.ordinal<0xfffe00a0U&&p.layer==Layer::glow;}),"Cooling embers fail to outlast hot explosion");
            const auto early=heavy.sample(.13);
            for(const auto& p:early.particles)if(p.layer==Layer::debris){
                const Vec3 d=p.position+hit.position*(-1)+Vec3{0,3.5*.06*.06,0};
                require(d.x<0&&std::hypot(d.y,d.z)<=(-d.x)*.700001,"Initial armor ejecta escape outward cone");
            }
            const auto& base=snap.particles;
            std::vector<Particle> lobes;
            for(auto p:base)if(p.ordinal>=0xffff0000U&&p.ordinal<0xffff0009U)lobes.push_back(p);
            require(lobes.size()==9&&lobes[0].position.x>lobes[3].position.x&&lobes[3].position.x>lobes[6].position.x,
                "Hot cone does not extend away from hit");
            require(lobes[0].size<lobes[3].size&&lobes[3].size<lobes[6].size,"Hot cone fails to widen away from impact apex");
            require(snap.lights.size()==1&&snap.lights[0].color.x>snap.lights[0].color.y,"Hot burst lacks warm illumination request");
            const auto contact=heavy.sample(.11);
            require(contact.lights.size()==1&&contact.lights[0].color.x>contact.lights[0].color.y,"Contact flash is not warm white");
        }
        const auto late=heavy.sample(.6);
        require(!late.particles.empty(),"Impact aftermath disappears too early");
        const auto finished=heavy.sample(.95);
        require(finished.particles.empty()&&finished.ribbons.empty()&&finished.lights.empty(),"Sped-up impact exceeds shortened envelope");
        require(effect_speed(kind)==2.0,"Impact no longer runs at double speed");
    }
    Flow flow,repeat,blastFlow;
    const auto empty=flow.pixels(true);
    for(std::size_t i=3;i<empty.size();i+=4)require(empty[i]==0,"Unfed flow has visible flame");
    for(unsigned step=1;step<=240;++step){
        const double time=static_cast<double>(step)/60.;
        flow.step(time,false);repeat.step(time,false);blastFlow.step(time,true);
        if(step==90){
            require(flow.pixels(true)==repeat.pixels(true),"Fixed-step flow bake is not reproducible");
            const auto image=flow.pixels(true);unsigned visible=0;
            for(std::size_t i=3;i<image.size();i+=4)if(image[i]>32)++visible;
            require(visible>80,"Flow flame body missing");
        }
    }
    const auto smoke=blastFlow.pixels(false);unsigned billow=0;
    for(std::size_t i=3;i<smoke.size();i+=4)if(smoke[i]>8)++billow;
    require(billow>20,"Explosion lacks persistent smoke after initial flash");
    rejects([&]{flow.step(std::numeric_limits<double>::quiet_NaN(),false);});
    std::cout<<checks<<" particle contract checks passed (authored fixtures only).\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
