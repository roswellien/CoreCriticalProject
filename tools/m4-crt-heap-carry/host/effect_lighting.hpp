#pragma once
#include "material_normals.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <istream>
#include <vector>

namespace mw34::effects {
inline constexpr unsigned capacity = 64;
// Procedural missile exhaust shares the weapon-light budget, but one salvo
// must not displace every other weapon family or consume fixture reservation.
inline constexpr unsigned missile_light_capacity = 8;
// CPU/GPU protocol: xyz is an endpoint for capsules, a direction for spots.
enum class LightKind : unsigned { point = 0, capsule = 1, spot = 2 };
using Point = std::array<float, 3>;
// Explicit presentation clock: normal live rendering advances, frozen photo
// rendering holds. A source-frame delta field is not an elapsed-time clock.
class Clock {
    double previous_{}, elapsed_{};
    bool initialized_{};

  public:
    double update(double raw, bool paused) {
        if (!std::isfinite(raw) || raw < 0)
            throw std::runtime_error("Invalid effect clock");
        if (!initialized_) {
            previous_ = raw;
            initialized_ = true;
            return elapsed_;
        }
        if (raw < previous_)
            elapsed_ = 0;
        else if (!paused)
            elapsed_ += raw - previous_;
        previous_ = raw;
        return elapsed_;
    }
};
struct Emitter {
    unsigned kind{};
    float radius{}, intensity{}, lifetime{};
    Point color{};
};
inline float weapon_intensity_scale(const Emitter &e) {
    // MWFX1 kind 3 is PPC trail. Kind 2 groups PPC/Gauss/MAC muzzle flashes;
    // only the PPC muzzle has this blue signature in prepare_effect_lights.py.
    // Blue kind 5 impacts are shared with lasers and cannot identify a weapon.
    // Apply the presentation gain here so existing installed catalogs work
    // unchanged and repeated observations never compound the adjustment.
    const bool ppc = e.kind == 3 || (e.kind == 2 && e.color == Point{.15f, .4f, 1.f});
    return ppc ? 1.25f : 1.f;
}
using Catalog = std::map<materials::SurfaceKey, Emitter>;
inline Catalog read_catalog(std::istream &f) {
    auto fail = [] { throw std::runtime_error("Invalid effect-light material catalog"); };
    auto bytes = [&](void *p, size_t n) {
        if (!f.read(static_cast<char *>(p), std::streamsize(n)))
            fail();
    };
    char magic[8];
    bytes(magic, 8);
    if (std::memcmp(magic, "MWFX1\0\0\0", 8))
        fail();
    unsigned count{};
    bytes(&count, 4);
    if (!count || count > 8192)
        fail();
    Catalog out;
    for (unsigned i = 0; i < count; ++i) {
        materials::SurfaceKey k;
        Emitter e;
        bytes(&k.width, 4);
        bytes(&k.height, 4);
        bytes(&k.format, 4);
        bytes(&e.kind, 4);
        bytes(&k.hash, 8);
        bytes(&e.radius, 4);
        bytes(&e.intensity, 4);
        bytes(&e.lifetime, 4);
        bytes(e.color.data(), 12);
        if (!k.width || !k.height || k.width > 4096 || k.height > 4096 || k.format < 1 ||
            k.format > 3 || e.kind < 1 || e.kind > 6)
            fail();
        auto valid = [](float v, float a, float b) { return std::isfinite(v) && v >= a && v <= b; };
        if (!valid(e.radius, .25f, 128) || !valid(e.intensity, 0, 8) || !valid(e.lifetime, .01f, 1))
            fail();
        for (float c : e.color)
            if (!valid(c, 0, 4))
                fail();
        if (*std::max_element(e.color.begin(), e.color.end()) <= 0 || !out.emplace(k, e).second)
            fail();
    }
    if (f.peek() != std::char_traits<char>::eof())
        fail();
    return out;
}
struct alignas(16) Light {
    std::array<float, 4> start{}, end{}, color{};
};
struct alignas(16) Uniform {
    std::array<float, 4> params{};
    std::array<Light, capacity> lights{};
    std::array<std::array<float, 4>, capacity> shadow{};
};
static_assert(sizeof(Light) == 48 && sizeof(Uniform) == 16 + 64 * capacity);
inline unsigned fixture_slots(unsigned occupied, unsigned limit, unsigned weapon_reserve) {
    if (!limit || limit > capacity || occupied > limit)
        throw std::runtime_error("Invalid combined light budget");
    return std::min(limit - occupied, limit - std::min(weapon_reserve, limit));
}
inline float distance2(const Point &a, const Point &b) {
    float v = 0;
    for (unsigned i = 0; i < 3; ++i) {
        const float q = a[i] - b[i];
        v += q * q;
    }
    return v;
}
inline Point closest(const Point &p, const Point &a, const Point &b) {
    const float den = distance2(a, b);
    float t = 0;
    if (den > 1e-12f) {
        for (unsigned i = 0; i < 3; ++i)
            t += (p[i] - a[i]) * (b[i] - a[i]);
        t = std::clamp(t / den, 0.f, 1.f);
    }
    Point q{};
    for (unsigned i = 0; i < 3; ++i)
        q[i] = a[i] + t * (b[i] - a[i]);
    return q;
}
inline Point reconstruct(float x, float y, float depth, const std::array<float, 6> &p,
                         const std::array<float, 12> &w) {
    if (!std::isfinite(depth) || depth <= 0 || !std::isfinite(x) || !std::isfinite(y) ||
        p[1] == 0 || p[2] == 0)
        throw std::runtime_error("Invalid effect source projection");
    const Point c{(x - p[3]) / (p[1] * depth), (y - p[4]) / (p[2] * depth), p[0] / depth};
    Point q{};
    for (unsigned i = 0; i < 3; ++i) {
        q[i] = w[i * 4 + 3];
        for (unsigned j = 0; j < 3; ++j)
            q[i] += w[i * 4 + j] * c[j];
        if (!std::isfinite(q[i]) || std::abs(q[i]) > 1000000)
            throw std::runtime_error("Effect source position outside supported world");
    }
    return q;
}
// Presentation-only observations of original rendered effects. No source
// object lifetime, hit, weapon origin, animation or simulation is modified.
class Cache {
    struct Entry {
        Emitter emitter;
        Point a, b;
        double time;
        std::uint64_t source{};
    };
    std::vector<Entry> entries_;
    double previous_{};

  public:
    void clear() {
        entries_.clear();
        previous_ = 0;
    }
    size_t size() const { return entries_.size(); }
    void expire(double t) {
        if (!std::isfinite(t))
            throw std::runtime_error("Invalid effect presentation time");
        if (t < previous_)
            entries_.clear();
        previous_ = t;
        std::erase_if(entries_, [&](const Entry &e) { return t - e.time > e.emitter.lifetime; });
    }

  private:
    void observe_impl(const Emitter &e, const std::vector<Point> &points, double t,
                      std::uint64_t source) {
        expire(t);
        if (points.empty() || points.size() > 1024)
            return;
        for (const auto &p : points)
            for (float v : p)
                if (!std::isfinite(v) || std::abs(v) > 1000000)
                    throw std::runtime_error("Invalid observed effect point");
        Point a{}, b{};
        if (e.kind == 1 && points.size() > 1) {
            // Endpoints of an actual rendered beam, including clipped beams.
            // A capsule light avoids a row of fabricated moving point lights.
            a = points.front();
            b = a;
            float farthest = 0;
            for (const auto &p : points)
                if (distance2(a, p) > farthest) {
                    farthest = distance2(a, p);
                    b = p;
                }
            farthest = 0;
            for (const auto &p : points)
                if (distance2(b, p) > farthest) {
                    farthest = distance2(b, p);
                    a = p;
                }
            if (distance2(a, b) > 4096.f * 4096.f)
                return;
            if (b < a)
                std::swap(a, b);
        } else {
            for (const auto &p : points)
                for (unsigned j = 0; j < 3; ++j)
                    a[j] += p[j] / float(points.size());
            b = a;
        }
        for (auto &old : entries_)
            if ((source && old.source == source) ||
                (!source && !old.source && old.emitter.kind == e.kind &&
                 old.emitter.color == e.color && distance2(old.a, a) < .5625f &&
                 distance2(old.b, b) < .5625f)) {
                old = {e, a, b, t, source};
                return;
            }
        if (entries_.size() >= 256) {
            auto old =
                std::min_element(entries_.begin(), entries_.end(),
                                 [](const Entry &a, const Entry &b) { return a.time < b.time; });
            *old = {e, a, b, t, source};
        } else
            entries_.push_back({e, a, b, t, source});
    }

  public:
    void observe(const Emitter &e, const std::vector<Point> &points, double t) {
        observe_impl(e, points, t, 0);
    }
    // A moving emitter replaces its own previous position instead of leaving
    // stationary lights along its path. The caller owns a nonzero identity that
    // includes object generation and resets the cache when its context changes.
    // Spatially coincident tracked sources and ordinary flashes remain distinct.
    void observe_tracked(std::uint64_t source, const Emitter &e, const std::vector<Point> &points,
                         double t) {
        if (!source)
            throw std::runtime_error("Tracked effect source identity must be nonzero");
        observe_impl(e, points, t, source);
    }
    void erase_tracked(std::uint64_t source) {
        if (source)
            std::erase_if(entries_, [&](const Entry &entry) { return entry.source == source; });
    }
    Uniform uniform(double t, const Point &eye, unsigned limit, float strength) {
        expire(t);
        if (!limit || limit > capacity || !std::isfinite(strength) || strength < 0)
            throw std::runtime_error("Invalid effect light budget");
        struct Candidate {
            float score;
            Light light;
            bool missile;
        };
        std::vector<Candidate> picks;
        for (const auto &e : entries_) {
            const float fade = std::clamp(1.f - float((t - e.time) / e.emitter.lifetime), 0.f, 1.f);
            const float power =
                e.emitter.intensity * weapon_intensity_scale(e.emitter) * strength * fade * fade;
            if (power <= .0001f)
                continue;
            const float radius = e.emitter.radius, d2 = distance2(eye, closest(eye, e.a, e.b));
            const float score = power * radius * radius / (radius * radius + d2);
            Light l;
            l.start = {e.a[0], e.a[1], e.a[2], radius};
            l.end = {e.b[0], e.b[1], e.b[2], e.emitter.kind == 1 ? 1.f : 0.f};
            l.color = {e.emitter.color[0], e.emitter.color[1], e.emitter.color[2], power};
            // Kind 7 is internal procedural exhaust, never an MWFX1 catalog role.
            picks.push_back({score, l, e.emitter.kind == 7});
        }
        std::stable_sort(picks.begin(), picks.end(),
                         [](const Candidate &a, const Candidate &b) { return a.score > b.score; });
        Uniform out;
        unsigned n{}, missiles{};
        for (const auto &candidate : picks) {
            if (candidate.missile && missiles >= std::min(missile_light_capacity, limit))
                continue;
            out.lights[n++] = candidate.light;
            missiles += candidate.missile;
            if (n == limit)
                break;
        }
        out.params[0] = float(n);
        return out;
    }
};
} // namespace mw34::effects
