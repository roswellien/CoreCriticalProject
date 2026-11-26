#include "mech3/arena_camera.h"

#include <algorithm>
#include <cmath>

namespace mech3::arena_camera {
namespace {

constexpr float kFullTurn = 6.283185307179586f;
constexpr int kAutomaticModeCount = static_cast<int>(Mode::Free);
constexpr float kMaxFrameSeconds = 0.25f;

void look_direction(float yaw, float pitch, float (&direction)[3]) {
    const float flat_length = std::cos(pitch);
    direction[0] = flat_length * std::sin(yaw);
    direction[1] = -std::sin(pitch);
    direction[2] = flat_length * std::cos(yaw);
}

void unit_direction(const float (&source)[3], float (&direction)[3]) {
    const float length = std::hypot(source[0], source[1], source[2]);
    if (length > 0.0f && std::isfinite(length)) {
        for (int axis = 0; axis < 3; ++axis) {
            direction[axis] = source[axis] / length;
        }
    } else {
        direction[0] = 0.0f;
        direction[1] = 0.0f;
        direction[2] = 1.0f;
    }
}

void glide(float (&point)[3], const float (&target)[3], float fraction) {
    for (int axis = 0; axis < 3; ++axis) {
        point[axis] += (target[axis] - point[axis]) * fraction;
    }
}

} // namespace

const char *mode_name(Mode mode) {
    switch (mode) {
    case Mode::Chase:
        return "chase";
    case Mode::Cockpit:
        return "cockpit";
    case Mode::Orbit:
        return "orbit";
    case Mode::Overhead:
        return "overhead";
    case Mode::Free:
        return "free";
    }
    return "unknown";
}

float smoothing(float rate, float dt) {
    if (!(dt > 0.0f)) {
        return 0.0f;
    }
    // expm1 preserves the small movement that would be lost subtracting two near-equal values.
    return std::clamp(-std::expm1(-rate * dt), 0.0f, 1.0f);
}

void Camera::set_mode(Mode mode) {
    if (mode == Mode::Free && mode_ != Mode::Free) {
        before_free_ = mode_;
    }
    mode_ = mode;
}

void Camera::cycle(int direction) {
    const Mode current = mode_ == Mode::Free ? before_free_ : mode_;
    const int step = direction % kAutomaticModeCount;
    const int next = (static_cast<int>(current) + step + kAutomaticModeCount) % kAutomaticModeCount;
    set_mode(static_cast<Mode>(next));
}

void Camera::toggle_free() { set_mode(mode_ == Mode::Free ? before_free_ : Mode::Free); }

Pose Camera::update(const Subject &subject, const Action &action, const Input &input, float dt) {
    // Limit the motion after a stalled frame and keep negative elapsed time from reversing it.
    dt = std::clamp(dt, 0.0f, kMaxFrameSeconds);
    const float zoom_factor = std::pow(kZoomStep, input.zoom);

    if (mode_ == Mode::Free) {
        free_speed_ = std::clamp(free_speed_ * zoom_factor, kFreeSpeedMin, kFreeSpeedMax);
        pose_.yaw -= input.look_dx * kLookRadiansPerCount;
        // Kept in -pi .. pi so a long session never loses float precision.
        pose_.yaw = std::remainder(pose_.yaw, 2.0f * 3.14159265358979f);
        pose_.pitch =
            std::clamp(pose_.pitch + input.look_dy * kLookRadiansPerCount, -kMaxPitch, kMaxPitch);

        float forward[3];
        look_direction(pose_.yaw, pose_.pitch, forward);
        const float right[3] = {-std::cos(pose_.yaw), 0.0f, std::sin(pose_.yaw)};
        const float speed = free_speed_ * (input.fast ? kFastFactor : 1.0f);
        const float travel = speed * dt;
        for (int axis = 0; axis < 3; ++axis) {
            eye_[axis] += (forward[axis] * input.forward + right[axis] * input.right) * travel;
        }
        eye_[1] += input.up * travel;

        // Keep an aim point for the next automatic mode to glide from.
        for (int axis = 0; axis < 3; ++axis) {
            aim_[axis] = eye_[axis] + forward[axis] * 10.0f;
        }
        std::copy_n(eye_, 3, pose_.eye);
        fresh_ = false;
        return pose_;
    }

    float target_eye[3] = {};
    float target_aim[3] = {};
    float eye_rate = 0.0f;
    float aim_rate = 0.0f;
    switch (mode_) {
    case Mode::Chase: {
        chase_distance_ =
            std::clamp(chase_distance_ / zoom_factor, kChaseDistanceMin, kChaseDistanceMax);
        if (!subject.present) {
            return pose_;
        }
        float heading[3];
        unit_direction(subject.forward, heading);
        for (int axis = 0; axis < 3; ++axis) {
            target_eye[axis] = subject.centre[axis] - heading[axis] * chase_distance_;
            target_aim[axis] = subject.centre[axis];
        }
        target_eye[1] += chase_distance_ * 0.4f;
        target_aim[1] += 2.0f;
        eye_rate = 4.0f;
        aim_rate = 8.0f;
        break;
    }
    case Mode::Cockpit: {
        if (!subject.present) {
            return pose_;
        }
        float look[3];
        unit_direction(subject.look, look);
        std::copy_n(subject.cockpit, 3, target_eye);
        target_eye[1] += 0.5f;
        for (int axis = 0; axis < 3; ++axis) {
            target_aim[axis] = target_eye[axis] + look[axis] * 50.0f;
        }
        eye_rate = 30.0f;
        aim_rate = 12.0f;
        break;
    }
    case Mode::Orbit: {
        const float *centre = aim_;
        float action_radius = 0.0f;
        if (action.count > 0) {
            centre = action.centre;
            action_radius = action.radius;
        } else if (subject.present) {
            centre = subject.centre;
        }
        orbit_zoom_ = std::clamp(orbit_zoom_ / zoom_factor, 0.25f, 8.0f);
        const float radius = std::max(kOrbitRadiusMin, action_radius * 1.6f) * orbit_zoom_;
        orbit_angle_ += kOrbitTurnRate * dt;
        if (orbit_angle_ >= kFullTurn) {
            orbit_angle_ -= kFullTurn;
        }
        std::copy_n(centre, 3, target_aim);
        target_eye[0] = centre[0] + std::sin(orbit_angle_) * radius;
        target_eye[1] = centre[1] + radius * 0.45f;
        target_eye[2] = centre[2] + std::cos(orbit_angle_) * radius;
        eye_rate = 3.0f;
        aim_rate = 2.0f;
        break;
    }
    case Mode::Overhead: {
        const float *ground = aim_;
        if (subject.present) {
            ground = subject.centre;
        } else if (action.count > 0) {
            ground = action.centre;
        }
        overhead_height_ =
            std::clamp(overhead_height_ / zoom_factor, kOverheadHeightMin, kOverheadHeightMax);
        float north_down[3];
        look_direction(0.0f, kOverheadPitch, north_down);
        const float sight_distance = overhead_height_ / std::sin(kOverheadPitch);
        for (int axis = 0; axis < 3; ++axis) {
            target_aim[axis] = ground[axis];
            target_eye[axis] = ground[axis] - north_down[axis] * sight_distance;
        }
        // Equal rates let the view translate while keeping its north-facing sight line.
        eye_rate = aim_rate = 2.5f;
        break;
    }
    case Mode::Free:
        break;
    }

    if (fresh_) {
        std::copy_n(target_eye, 3, eye_);
        std::copy_n(target_aim, 3, aim_);
        fresh_ = false;
    } else {
        glide(eye_, target_eye, smoothing(eye_rate, dt));
        glide(aim_, target_aim, smoothing(aim_rate, dt));
    }

    std::copy_n(eye_, 3, pose_.eye);
    const float delta_x = aim_[0] - eye_[0];
    const float delta_y = aim_[1] - eye_[1];
    const float delta_z = aim_[2] - eye_[2];
    const float flat_length = std::hypot(delta_x, delta_z);
    // Coincident points can occur during a mode change and have no viewing direction.
    if (flat_length > 0.0f || delta_y != 0.0f) {
        pose_.yaw = flat_length > 0.0f ? std::atan2(delta_x, delta_z) : 0.0f;
        pose_.pitch = std::clamp(std::atan2(-delta_y, flat_length), -kMaxPitch, kMaxPitch);
    }
    return pose_;
}

} // namespace mech3::arena_camera
