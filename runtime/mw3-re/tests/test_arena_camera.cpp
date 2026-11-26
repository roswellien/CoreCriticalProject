// #529 (docs/arena.md): drive the spectator camera with synthetic mech positions and viewer input.
#include <cmath>

#include "check.h"
#include "mech3/arena_camera.h"

namespace {
using namespace mech3::arena_camera;

constexpr float kTolerance = 0.001f;

float eye_distance(const Pose &first, const Pose &second) {
    return std::hypot(first.eye[0] - second.eye[0], first.eye[1] - second.eye[1],
                      first.eye[2] - second.eye[2]);
}

bool same_pose(const Pose &first, const Pose &second) {
    return eye_distance(first, second) < kTolerance &&
           std::abs(first.yaw - second.yaw) < kTolerance &&
           std::abs(first.pitch - second.pitch) < kTolerance;
}

bool finite_pose(const Pose &pose) {
    return std::isfinite(pose.eye[0]) && std::isfinite(pose.eye[1]) && std::isfinite(pose.eye[2]) &&
           std::isfinite(pose.yaw) && std::isfinite(pose.pitch);
}

Pose chase_after_one_second(int frames_per_second) {
    Camera camera;
    Subject subject;
    subject.present = true;
    camera.update(subject, {}, {}, 0.0f);
    subject.centre[0] = 120.0f;
    subject.centre[1] = 15.0f;
    subject.centre[2] = 80.0f;
    for (int frame = 0; frame < frames_per_second; ++frame) {
        camera.update(subject, {}, {}, 1.0f / frames_per_second);
    }
    return camera.pose();
}
} // namespace

TEST(arena_camera_smoothing_is_frame_rate_independent) {
    EXPECT(smoothing(4.0f, 0.0f) == 0.0f);
    EXPECT(smoothing(4.0f, -1.0f) == 0.0f);
    EXPECT(smoothing(-4.0f, 1.0f) == 0.0f);
    EXPECT(smoothing(4.0f, 100.0f) == 1.0f);
    const Pose slow = chase_after_one_second(30);
    const Pose fast = chase_after_one_second(240);
    EXPECT(same_pose(slow, fast));
    EXPECT(std::abs(slow.eye[0] - 120.0f * (1.0f - std::exp(-4.0f))) < kTolerance);
}

TEST(arena_camera_overhead_stays_north_up_when_subject_turns) {
    Camera camera;
    camera.set_mode(Mode::Overhead);
    Subject subject;
    subject.present = true;
    subject.centre[0] = 30.0f;
    subject.centre[2] = 20.0f;
    const Pose initial = camera.update(subject, {}, {}, 0.0f);
    subject.forward[0] = 1.0f;
    subject.forward[2] = 0.0f;
    const Pose turned = camera.update(subject, {}, {}, 0.2f);
    EXPECT(initial.yaw == 0.0f);
    EXPECT(turned.yaw == 0.0f);
    EXPECT(eye_distance(initial, turned) == 0.0f);
    EXPECT(std::abs(turned.pitch - kOverheadPitch) < kTolerance);
}

TEST(arena_camera_overhead_converges_without_overshoot) {
    Camera camera;
    camera.set_mode(Mode::Overhead);
    Subject subject;
    subject.present = true;
    camera.update(subject, {}, {}, 0.0f);

    subject.centre[0] = 100.0f;
    subject.centre[1] = 25.0f;
    subject.centre[2] = -60.0f;
    Camera target_camera;
    target_camera.set_mode(Mode::Overhead);
    const Pose target = target_camera.update(subject, {}, {}, 0.0f);
    float previous_distance = eye_distance(camera.pose(), target);
    for (int frame = 0; frame < 40; ++frame) {
        const Pose pose = camera.update(subject, {}, {}, 0.1f);
        const float distance = eye_distance(pose, target);
        EXPECT(distance <= previous_distance);
        EXPECT(pose.eye[0] <= target.eye[0]);
        EXPECT(pose.yaw == 0.0f);
        EXPECT(std::abs(pose.pitch - kOverheadPitch) < kTolerance);
        previous_distance = distance;
    }
    EXPECT(previous_distance < 0.01f);
}

TEST(arena_camera_chase_jumps_behind_subject_on_first_update_and_reset) {
    Camera camera;
    Subject subject;
    subject.present = true;
    subject.centre[0] = 60.0f;
    subject.centre[1] = 12.0f;
    subject.centre[2] = 30.0f;
    subject.forward[0] = 0.6f;
    subject.forward[2] = 0.8f;
    const Pose first = camera.update(subject, {}, {}, 0.0f);
    const float dot = (first.eye[0] - subject.centre[0]) * subject.forward[0] +
                      (first.eye[2] - subject.centre[2]) * subject.forward[2];
    EXPECT(dot < 0.0f);
    EXPECT(std::abs(dot + kChaseDistance) < kTolerance);
    EXPECT(std::abs(first.eye[1] - subject.centre[1] - kChaseDistance * 0.4f) < kTolerance);

    camera.reset();
    subject.centre[0] += 90.0f;
    const Pose after_reset = camera.update(subject, {}, {}, 0.0f);
    EXPECT(std::abs(after_reset.eye[0] - first.eye[0] - 90.0f) < kTolerance);
}

TEST(arena_camera_orbit_centres_on_the_action_and_advances_with_time) {
    Camera camera;
    camera.set_mode(Mode::Orbit);
    Subject subject;
    subject.present = true;
    Action action;
    action.count = 2;
    action.centre[0] = 90.0f;
    action.centre[2] = 10.0f;
    action.radius = 50.0f;
    const float radius = action.radius * 1.6f;
    const Pose first = camera.update(subject, action, {}, 0.0f);
    EXPECT(first.eye[0] == action.centre[0]);
    EXPECT(std::abs(first.eye[1] - radius * 0.45f) < kTolerance);
    EXPECT(std::abs(first.eye[2] - action.centre[2] - radius) < kTolerance);

    constexpr float kElapsed = 0.2f;
    const float travel = std::sin(kOrbitTurnRate * kElapsed) * radius * smoothing(3.0f, kElapsed);
    const Pose next = camera.update(subject, action, {}, kElapsed);
    EXPECT(std::abs(next.eye[0] - first.eye[0] - travel) < kTolerance);
}

TEST(arena_camera_zoom_clamps_chase_distance_and_free_speed) {
    Camera chase;
    Subject subject;
    subject.present = true;
    Input input;
    input.zoom = 1000.0f;
    EXPECT(chase.update(subject, {}, input, 0.0f).eye[2] == -kChaseDistanceMin);
    chase.reset();
    input.zoom = -1000.0f;
    EXPECT(chase.update(subject, {}, input, 0.0f).eye[2] == -kChaseDistanceMax);

    Camera free_camera;
    free_camera.set_mode(Mode::Free);
    input.forward = 1.0f;
    Pose before = free_camera.pose();
    Pose after = free_camera.update({}, {}, input, 0.25f);
    EXPECT(std::abs(eye_distance(before, after) - kFreeSpeedMin * 0.25f) < kTolerance);
    before = after;
    input.zoom = 1000.0f;
    after = free_camera.update({}, {}, input, 0.25f);
    EXPECT(std::abs(eye_distance(before, after) - kFreeSpeedMax * 0.25f) < kTolerance);
}

TEST(arena_camera_free_looks_and_flies_along_the_view) {
    Camera camera;
    camera.set_mode(Mode::Free);
    const Pose initial = camera.pose();
    Input input;
    input.look_dx = 75.0f;
    input.look_dy = 50.0f;
    const Pose turned = camera.update({}, {}, input, 0.0f);
    EXPECT(std::abs(turned.yaw - (initial.yaw - 75.0f * kLookRadiansPerCount)) < kTolerance);
    EXPECT(std::abs(turned.pitch - (initial.pitch + 50.0f * kLookRadiansPerCount)) < kTolerance);

    input = {};
    input.forward = 1.0f;
    constexpr float kElapsed = 0.125f;
    const Pose moved = camera.update({}, {}, input, kElapsed);
    const float travel = kFreeSpeed * kElapsed;
    EXPECT(std::abs(moved.eye[0] - turned.eye[0] -
                    std::cos(turned.pitch) * std::sin(turned.yaw) * travel) < kTolerance);
    EXPECT(std::abs(moved.eye[1] - turned.eye[1] + std::sin(turned.pitch) * travel) < kTolerance);
    EXPECT(std::abs(moved.eye[2] - turned.eye[2] -
                    std::cos(turned.pitch) * std::cos(turned.yaw) * travel) < kTolerance);

    input.fast = true;
    const Pose fast = camera.update({}, {}, input, kElapsed);
    EXPECT(std::abs(eye_distance(fast, moved) - 4.0f * travel) < kTolerance);
    const Pose after_stall = camera.update({}, {}, input, 2.0f);
    EXPECT(std::abs(eye_distance(after_stall, fast) - 4.0f * kFreeSpeed * 0.25f) < kTolerance);

    input = {};
    input.look_dy = 10000.0f;
    EXPECT(camera.update({}, {}, input, 0.0f).pitch == kMaxPitch);
    input.look_dy = -10000.0f;
    EXPECT(camera.update({}, {}, input, 0.0f).pitch == -kMaxPitch);
}

TEST(arena_camera_toggle_and_cycle_keep_the_previous_automatic_mode) {
    Camera camera;
    camera.set_mode(Mode::Orbit);
    camera.toggle_free();
    EXPECT(camera.mode() == Mode::Free);
    camera.set_mode(Mode::Free);
    camera.toggle_free();
    EXPECT(camera.mode() == Mode::Orbit);

    camera.toggle_free();
    camera.cycle(1);
    EXPECT(camera.mode() == Mode::Overhead);
    camera.cycle(1);
    EXPECT(camera.mode() == Mode::Chase);
    camera.cycle(-1);
    EXPECT(camera.mode() == Mode::Overhead);
}

TEST(arena_camera_automatic_mode_glides_from_the_free_pose) {
    Camera camera;
    camera.set_mode(Mode::Free);
    Input input;
    input.forward = 1.0f;
    input.look_dx = 100.0f;
    const Pose free_pose = camera.update({}, {}, input, 0.2f);
    camera.set_mode(Mode::Chase);
    Subject subject;
    subject.present = true;
    EXPECT(same_pose(camera.update(subject, {}, {}, 0.0f), free_pose));
    const Pose gliding = camera.update(subject, {}, {}, 0.1f);
    Camera target_camera;
    const Pose target = target_camera.update(subject, {}, {}, 0.0f);
    EXPECT(eye_distance(gliding, free_pose) > kTolerance);
    EXPECT(eye_distance(gliding, target) < eye_distance(free_pose, target));
    EXPECT(eye_distance(gliding, target) > kTolerance);
}

TEST(arena_camera_empty_inputs_stay_finite) {
    constexpr Mode kModes[] = {Mode::Chase, Mode::Cockpit, Mode::Orbit, Mode::Overhead, Mode::Free};
    for (const Mode mode : kModes) {
        Camera camera;
        camera.set_mode(mode);
        const Pose initial = camera.pose();
        EXPECT(finite_pose(camera.update({}, {}, {}, 0.0f)));
        EXPECT(finite_pose(camera.update({}, {}, {}, 0.1f)));
        if (mode == Mode::Chase || mode == Mode::Cockpit) {
            EXPECT(same_pose(camera.pose(), initial));
        }
    }
}

TEST(arena_camera_zero_subject_directions_face_north_and_missing_subject_holds_pose) {
    Subject subject;
    subject.present = true;
    subject.forward[2] = 0.0f;
    subject.look[2] = 0.0f;

    Camera chase;
    const Pose chased = chase.update(subject, {}, {}, 0.0f);
    EXPECT(finite_pose(chased));
    EXPECT(chased.yaw == 0.0f);
    EXPECT(chased.eye[2] == -kChaseDistance);
    EXPECT(same_pose(chase.update({}, {}, {}, 0.2f), chased));

    Camera cockpit;
    cockpit.set_mode(Mode::Cockpit);
    subject.cockpit[1] = 10.0f;
    const Pose seated = cockpit.update(subject, {}, {}, 0.0f);
    EXPECT(finite_pose(seated));
    EXPECT(seated.yaw == 0.0f);
    EXPECT(seated.pitch == 0.0f);
    EXPECT(seated.eye[1] == 10.5f);
    EXPECT(same_pose(cockpit.update({}, {}, {}, 0.2f), seated));
}
