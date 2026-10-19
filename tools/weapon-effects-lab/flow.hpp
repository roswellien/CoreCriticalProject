// Authored offline 2D visual fluid bake. No Pyrefall code or game code imported.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace mw34::effects_lab {
class Flow {
    static constexpr int w=64,h=96,n=w*h;
    std::vector<float> vx_=std::vector<float>(n),vy_=std::vector<float>(n);
    std::vector<float> heat_=std::vector<float>(n),smoke_=std::vector<float>(n);
    float time_{};
    static float noise(float x,float y){
        const int ix=static_cast<int>(std::floor(x)),iy=static_cast<int>(std::floor(y));
        float a=x-static_cast<float>(ix),b=y-static_cast<float>(iy);
        a=a*a*(3-2*a);b=b*b*(3-2*b);
        auto hash=[](int px,int py){
            std::uint32_t v=static_cast<std::uint32_t>(px)*1597334677U^static_cast<std::uint32_t>(py)*3812015801U;
            v=(v^(v>>16))*2246822519U;v^=v>>13;
            return static_cast<float>(v&65535U)/65535.F;
        };
        return (1-b)*((1-a)*hash(ix,iy)+a*hash(ix+1,iy))+b*((1-a)*hash(ix,iy+1)+a*hash(ix+1,iy+1));
    }
    static float fbm(float x,float y){
        return .57F*noise(x,y)+.28F*noise(x*2.07F+13,y*2.07F-4)+.15F*noise(x*4.13F-5,y*4.13F+17);
    }
    static int at(int x,int y){return std::clamp(y,0,h-1)*w+std::clamp(x,0,w-1);}
    static float fetch(const std::vector<float>& f,float x,float y){
        x=std::clamp(x,0.F,static_cast<float>(w-1));y=std::clamp(y,0.F,static_cast<float>(h-1));
        const int ix=static_cast<int>(x),iy=static_cast<int>(y);
        const float a=x-static_cast<float>(ix),b=y-static_cast<float>(iy);
        return (1-b)*((1-a)*f[at(ix,iy)]+a*f[at(ix+1,iy)])+
                  b*((1-a)*f[at(ix,iy+1)]+a*f[at(ix+1,iy+1)]);
    }
    void advect(std::vector<float>& f,float dt,float decay){
        auto old=f;
        for(int y=0;y<h;++y)for(int x=0;x<w;++x){const int i=at(x,y);
            f[i]=fetch(old,static_cast<float>(x)-dt*vx_[i],static_cast<float>(y)-dt*vy_[i])*decay;}
    }
public:
    static constexpr int width=w,height=h;
    void step(double time,bool explosion){
        if(!std::isfinite(time)||time<0)throw std::invalid_argument("Invalid offline flow sample time");
        time_=static_cast<float>(time);
        constexpr float dt=1.F/60;
        const float age=static_cast<float>(time-.25);
        const bool feeding=age>=0 && age<(explosion?.17F:2.55F);
        if(feeding){
            for(int y=1;y<38;++y)for(int x=1;x<w-1;++x){
                const float fx=static_cast<float>(x),fy=static_cast<float>(y);
                const float phase=static_cast<float>(time);
                const float cx=32+2.8F*std::sin(phase*2.1F)+1.8F*std::sin(phase*4.7F);
                const float cy=explosion?13.F:7.F;
                const float dx=fx-cx,dy=fy-cy;
                const float rad=explosion?7.F+age*30.F:5.0F;
                float shape=std::exp(-(dx*dx+dy*dy)/(rad*rad));
                if(!explosion){
                    shape=.55F*shape+.38F*std::exp(-((dx-6)*(dx-6)+dy*dy)/14.F)+
                          .38F*std::exp(-((dx+6)*(dx+6)+dy*dy)/14.F);
                }
                shape*=.35F+1.15F*noise(fx*.4F+phase,fy*.37F-phase*4);
                const int i=at(x,y);
                heat_[i]=std::min(2.1F,heat_[i]+shape*dt*(explosion?65.F:9.F));
                smoke_[i]=std::min(1.3F,smoke_[i]+shape*dt*(explosion?24.F:2.7F));
                vx_[i]+=shape*dt*(explosion?dx*100.F:65.F*std::sin(phase*3.1F+fx*.21F));
                vy_[i]+=shape*dt*(explosion?(dy+4)*75.F:140.F);
            }
        }
        auto curl=std::vector<float>(n);
        for(int y=0;y<h;++y)for(int x=0;x<w;++x)
            curl[at(x,y)]=.5F*(vy_[at(x+1,y)]-vy_[at(x-1,y)]-vx_[at(x,y+1)]+vx_[at(x,y-1)]);
        for(int y=1;y<h-1;++y)for(int x=1;x<w-1;++x){
            const int i=at(x,y);
            const float gx=std::abs(curl[at(x+1,y)])-std::abs(curl[at(x-1,y)]);
            const float gy=std::abs(curl[at(x,y+1)])-std::abs(curl[at(x,y-1)]);
            const float length=std::sqrt(gx*gx+gy*gy)+.0001F;
            vx_[i]+=dt*gy/length*curl[i]*3.5F;
            vy_[i]+=dt*(-gx/length*curl[i]*3.5F+heat_[i]*52.F-smoke_[i]*2.F);
            vx_[i]=std::clamp(vx_[i],-90.F,90.F);vy_[i]=std::clamp(vy_[i],-90.F,110.F);
        }
        // Semi-Lagrangian velocity transport, both channels use the same old field.
        auto u=vx_,v=vy_;
        for(int y=0;y<h;++y)for(int x=0;x<w;++x){const int i=at(x,y);
            const float px=static_cast<float>(x)-dt*u[i],py=static_cast<float>(y)-dt*v[i];
            vx_[i]=fetch(u,px,py)*.998F;vy_[i]=fetch(v,px,py)*.998F;}
        auto div=std::vector<float>(n),pressure=std::vector<float>(n),next=pressure;
        for(int y=0;y<h;++y)for(int x=0;x<w;++x)
            div[at(x,y)]=.5F*(vx_[at(x+1,y)]-vx_[at(x-1,y)]+vy_[at(x,y+1)]-vy_[at(x,y-1)]);
        for(int iteration=0;iteration<16;++iteration){
            for(int y=0;y<h;++y)for(int x=0;x<w;++x)
                next[at(x,y)]=.25F*(pressure[at(x-1,y)]+pressure[at(x+1,y)]+pressure[at(x,y-1)]+pressure[at(x,y+1)]-div[at(x,y)]);
            pressure.swap(next);
        }
        for(int y=0;y<h;++y)for(int x=0;x<w;++x){const int i=at(x,y);
            vx_[i]-=.5F*(pressure[at(x+1,y)]-pressure[at(x-1,y)]);
            vy_[i]-=.5F*(pressure[at(x,y+1)]-pressure[at(x,y-1)]);
            if(x==0||x==w-1)vx_[i]=0;
            if(y==0)vy_[i]=std::max(0.F,vy_[i]);
        }
        advect(heat_,dt,.993F);advect(smoke_,dt,.998F);
        for(auto& t:heat_)t=std::max(0.F,t-dt*(explosion?.7F:.32F));
    }
    // Two straight-alpha layers, encoded for an illustrative sRGB Canvas viewer.
    // A future native material must use its own reviewed linear/HDR color contract.
    std::vector<std::uint8_t> pixels(bool fire) const {
        std::vector<std::uint8_t> out(n*4);
        for(int y=0;y<h;++y)for(int x=0;x<w;++x){
            const int i=at(x,y),p=((h-1-y)*w+x)*4;
            const float edge=std::clamp(static_cast<float>(std::min({x,w-1-x,y,h-1-y}))/5.F,0.F,1.F);
            const float t=heat_[i],d=smoke_[i];
            const float fx=static_cast<float>(x),fy=static_cast<float>(y);
            const float warp=fbm(fx*.12F+time_*.35F,fy*.12F-time_*.6F);
            const float texture=fbm(fx*.21F+warp*2,fy*.21F-time_*1.3F+warp);
            float r,g,b,a;
            if(fire){
                const float burn=t-.16F-texture*.65F;
                const float hot=std::clamp(burn/1.25F,0.F,1.F);
                r=1.F;g=.10F+.88F*std::pow(hot,.65F);b=.012F+.70F*std::pow(hot,3.F);
                a=std::clamp(burn*1.7F,0.F,.88F)*edge;
            } else {
                r=.17F+.18F*texture+.08F*std::min(t,1.F);
                g=.18F+.17F*texture+.025F*std::min(t,1.F);b=.20F+.16F*texture;
                a=std::clamp(d*(.3F+texture*.65F),0.F,.73F)*std::clamp(1.4F-t,0.F,1.F)*edge;
            }
            const float channels[]={r,g,b,a};
            for(int c=0;c<4;++c){if(!std::isfinite(channels[c]))throw std::runtime_error("Nonfinite fluid output");
                out[static_cast<std::size_t>(p+c)]=static_cast<std::uint8_t>(std::clamp(channels[c],0.F,1.F)*255+.5F);}
        }
        return out;
    }
};
} // namespace mw34::effects_lab
