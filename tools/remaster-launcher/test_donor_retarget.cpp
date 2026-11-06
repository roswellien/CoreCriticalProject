// Asset-free tests for the optional visual solver. No game inputs or guest state.
#include "../m4-crt-heap-carry/host/donor_retarget.hpp"
#include <iostream>
#include <limits>

using namespace mw34::donor;
unsigned checks = 0;
void check(bool value, const char *label) {
    ++checks;
    if (!value)
        throw std::runtime_error(label);
}
double error(const Mat &a, const Mat &b) {
    double e = 0;
    for (unsigned i = 0; i < 16; ++i)
        e = std::max(e, std::abs(a[i] - b[i]));
    return e;
}
Rig fixture() {
    Rig r;
    auto bone = [&](const char *name, const char *control, int parent, Vec p) {
        r.bones.push_back({name, control, parent, translate(identity(), p)});
        r.reference.emplace(control, r.bones.back().rest);
    };
    bone("Pelvis", "hip", -1, {0, 0, 4});
    bone("Torso_Twist", "torso", 0, {0, 0, 5});
    bone("Upperarm_Left", "larm", 1, {0, 2, 5});
    bone("Forearm_Left", "lhand", 2, {1, 2, 4});
    bone("Upperarm_Right", "rarm", 1, {0, -2, 5});
    bone("Forearm_Right", "rhand", 4, {1, -2, 4});
    bone("Thigh_Left", "lthigh", 0, {0, 1, 4});
    bone("Calf_Left", "lcalf", 6, {1, 1, 2});
    bone("Foot0_Left", "lfoot", 7, {0, 1, .5});
    bone("Thigh_Right", "rthigh", 0, {0, -1, 4});
    bone("Calf_Right", "rcalf", 9, {1, -1, 2});
    bone("Foot0_Right", "rfoot", 10, {0, -1, .5});
    r.walk_z = {.5, .5};
    return r;
}
void lengths(const Rig &r, const Pose &p) {
    for (auto edge :
         std::array<std::pair<unsigned, unsigned>, 4>{{{6, 7}, {7, 8}, {9, 10}, {10, 11}}}) {
        check(std::abs(length(sub(position(r.bones[edge.first].rest),
                                  position(r.bones[edge.second].rest))) -
                       length(sub(position(p.world[edge.first]), position(p.world[edge.second])))) <
                  1e-9,
              "fixed donor limb length");
    }
}
int main() {
    try {
        auto r = fixture();
        const auto original = r.reference;
        auto p = retarget(r, original, 0);
        check(!p.reach_clamps, "stand reachable");
        for (size_t i = 0; i < r.bones.size(); ++i)
            check(error(p.world[i], r.bones[i].rest) < 1e-9, "stand matches donor rest");
        check(r.reference == original, "reference transforms unchanged");
        check(locomotion(r, original) == 0, "stand gait blend zero");
        auto walking = original;
        walking.at("lfoot")[3] = .35;
        walking.at("lfoot")[11] += .2;
        walking.at("rfoot")[3] = -.35;
        p = retarget(r, walking, 1);
        lengths(r, p);
        check(!p.reach_clamps, "ordinary stride reachable");
        check(locomotion(r, walking) == 1, "stride gait blend one");
        auto moved = walking;
        for (auto &[name, m] : moved)
            m = translate(m, add(position(m), {7, -3, 0}));
        auto q = retarget(r, moved, 1);
        for (size_t i = 0; i < p.world.size(); ++i)
            check(error(q.world[i], translate(p.world[i], add(position(p.world[i]), {7, -3, 0}))) <
                      1e-9,
                  "root travel restored without changing stride");
        walking.at("lfoot")[3] = 100;
        p = retarget(r, walking, 1);
        check(p.reach_clamps > 0, "unreachable visual goal explicitly clamped");
        lengths(r, p);
        auto m = identity();
        m[0] = m[5] = m[10] = .6;
        m = translate(m, {2, -3, 7});
        check(error(product(m, inverse(m)), identity()) < 1e-9, "scaled affine inverse");
        check(length(sub(vector(swing({1, 0, 0}, {-1, 0, 0}), {1, 0, 0}), {-1, 0, 0})) < 1e-9,
              "opposite-direction swing finite");
        bool rejected = false;
        try {
            retarget(r, original, std::numeric_limits<double>::quiet_NaN());
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        check(rejected, "NaN gait rejected");
        rejected = false;
        try {
            auto singular = identity();
            singular[0] = 0;
            inverse(singular);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        check(rejected, "singular affine matrix rejected");
        // Original-joint mode must preserve the complete supplied pose, including
        // translations, rotations and scale. It must not run the foot-target solver.
        r = fixture();
        r.source_joint_pose = true;
        r.hip_drop = 9;
        auto source = r.reference;
        source.at("lcalf") =
            product(translate(swing({1, 0, 0}, {0, 1, 0}), {7, -3, 2}), r.reference.at("lcalf"));
        source.at("lfoot") = translate(identity(), {100, 50, -10});
        source.at("torso")[0] = .8;
        source.at("torso")[5] = 1.2;
        const auto saved = source;
        p = retarget(r, source, 1);
        q = retarget(r, source, 0);
        check(!p.reach_clamps, "original joints bypass visual reach clamp");
        for (size_t i = 0; i < r.bones.size(); ++i) {
            check(error(p.world[i], source.at(r.bones[i].control)) < 1e-9,
                  "original full joint pose preserved");
            check(error(p.world[i], q.world[i]) == 0, "original joints independent of gait");
        }
        check(source == saved, "source joints remain read-only");
        // An attached unbound part follows its parent's full delta exactly once.
        r.bones.push_back({"Attachment", "", 7, translate(identity(), {3, 1, 2})});
        p = retarget(r, source, 1);
        const auto attachment = product(
            product(source.at("lcalf"), inverse(r.reference.at("lcalf"))), r.bones.back().rest);
        check(error(p.world.back(), attachment) < 1e-9,
              "unbound part inherits original joint delta");
        // Keep an authored bind offset, even when it differs from the source pivot.
        r.bones[6].rest = translate(identity(), {2, 3, 4});
        p = retarget(r, source, 1);
        check(error(p.world[6],
                    product(product(source.at("lthigh"), inverse(r.reference.at("lthigh"))),
                            r.bones[6].rest)) < 1e-9,
              "source bind offset preserved");
        auto prior = retarget(r, source, 1);
        for (unsigned sample = 0; sample < 1000; ++sample) {
            source.at("lfoot")[3] += .0001;
            source.at("lfoot")[7] -= .0002;
            const auto next = retarget(r, source, 1);
            check(length(sub(position(next.world[8]), position(prior.world[8]))) < .000224,
                  "no knee-pole discontinuity in source mode");
            check(error(next.world[7], prior.world[7]) == 0,
                  "independent original knee remains fixed");
            prior = next;
        }
        rejected = false;
        try {
            source.at("lfoot")[3] = std::numeric_limits<double>::infinity();
            retarget(r, source, 1);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        check(rejected, "nonfinite original pose rejected");
        std::cout << "donor retarget checks=" << checks << " failures=0\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "donor retarget failure: " << e.what() << '\n';
        return 1;
    }
}
