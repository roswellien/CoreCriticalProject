#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <istream>
#include <stdexcept>
#include <string>

namespace mw34::controller {
struct Axis {
    double minimum{-32768}, center{}, maximum{32767}, deadzone{.12}, response{1};
    bool inverted{};
    void validate(bool trigger) const {
        if (!std::isfinite(minimum) || !std::isfinite(center) || !std::isfinite(maximum) ||
            !std::isfinite(deadzone) || !std::isfinite(response) || minimum < -32768 || maximum > 32767 ||
            deadzone < 0 || deadzone > .45 || response < .25 || response > 4 ||
            (trigger ? center < 0 || maximum-center < 8192 : center-minimum < 8192 || maximum-center < 8192))
            throw std::runtime_error("Invalid controller calibration range");
    }
    double adjust(short raw, bool trigger) const {
        double value = trigger ? std::clamp((raw-center)/(maximum-center),0.,1.) :
            std::clamp((raw-center)/(raw >= center ? maximum-center : center-minimum),-1.,1.);
        value = std::copysign(std::pow(std::max(0.,std::abs(value)-deadzone)/(1-deadzone),response),value);
        return inverted ? (trigger ? 1-value : -value) : value;
    }
};
struct Config {
    std::string device;
    std::array<Axis,6> calibration;
    std::array<unsigned,26> buttons{};
    std::array<unsigned,2> triggers{};
    std::array<int,4> axes{1,0,2,3};
    std::array<double,4> scale{-1,1,1,1};
    double threshold{.25};
    static Config read(std::istream& stream) {
        Config c; std::string magic; stream >> magic >> c.device;
        if (magic != "CC_MW3_CONTROLLER_V1" || c.device.size()!=64 ||
            c.device.find_first_not_of("0123456789ABCDEFabcdef")!=std::string::npos)
            throw std::runtime_error("Unknown MW3 controller config identity/version");
        for (unsigned i=0;i<6;++i) {
            int invert{}; auto& a=c.calibration[i]; stream >> a.minimum >> a.center >> a.maximum >> a.deadzone >> a.response >> invert;
            if (invert!=0 && invert!=1) throw std::runtime_error("Invalid controller inversion");
            a.inverted=invert!=0; a.validate(i>=4);
        }
        for (auto& command:c.buttons) { stream >> command; if(command>166) throw std::runtime_error("Controller button command outside MW3 range"); }
        for (auto& command:c.triggers) { stream >> command; if(command>166) throw std::runtime_error("Controller trigger command outside MW3 range"); }
        for (auto& axis:c.axes) { stream >> axis; if(axis < -1 || axis > 3) throw std::runtime_error("Invalid controller stick assignment"); }
        for (auto& scale:c.scale) { stream >> scale; if(!std::isfinite(scale)||std::abs(scale)<.1||std::abs(scale)>2) throw std::runtime_error("Invalid controller sensitivity"); }
        stream >> c.threshold;
        if (!stream || !std::isfinite(c.threshold) || c.threshold<.05 || c.threshold>.95) throw std::runtime_error("Incomplete controller config");
        stream >> std::ws; if (!stream.eof()) throw std::runtime_error("Unexpected controller config fields");
        std::transform(c.device.begin(),c.device.end(),c.device.begin(),[](char ch){return ch>='a'&&ch<='f'?char(ch-'a'+'A'):ch;});
        return c;
    }
};
struct Sample { std::array<short,6> axes{}; std::array<bool,26> buttons{}; bool connected{}, focused{}; };
struct State {
    std::array<unsigned,167> actions{};
    std::array<bool,167> pressed{};
    std::array<double,4> analog{}; // throttle, steering, torso yaw, torso pitch
    bool armed{}, connected{}, throttle_stopped{};
    void update(const Config& config,const Sample& sample) {
        std::array<bool,167> down{}; std::array<double,6> adjusted{};
        const bool available=sample.connected&&sample.focused;
        bool neutral=true;
        for(unsigned i=0;i<6;++i) {
            adjusted[i]=config.calibration[i].adjust(sample.axes[i],i>=4);
            // Rearming is based on physical release, before optional inversion.
            Axis rest=config.calibration[i]; rest.inverted=false;
            neutral &= std::abs(rest.adjust(sample.axes[i],i>=4)) < .05;
            neutral &= i<4 || adjusted[i]<.05;
        }
        for(bool held:sample.buttons) neutral &= !held;
        if (!available) armed=false;
        else if (!armed && neutral) armed=true;
        connected=available&&armed;
        analog.fill(0);
        if (connected) {
            for(unsigned i=0;i<26;++i) if(sample.buttons[i]&&config.buttons[i]) down[config.buttons[i]]=true;
            for(unsigned i=0;i<2;++i) if(adjusted[4+i]>=config.threshold&&config.triggers[i]) down[config.triggers[i]]=true;
            for(unsigned i=0;i<4;++i) if(config.axes[i]>=0) analog[i]=std::clamp(adjusted[config.axes[i]]*config.scale[i],-1.,1.);
            if(down[27])throttle_stopped=true;
            else if(std::abs(analog[0])<.05)throttle_stopped=false;
            if(throttle_stopped)analog[0]=0;
        }
        for(unsigned i=0;i<167;++i) {
            const bool was=(actions[i]&3)!=0;
            pressed[i]=down[i]&&!was;
            actions[i]=down[i]?(was?2U:1U):(was?4U:0U);
        }
    }
};
} // namespace mw34::controller
