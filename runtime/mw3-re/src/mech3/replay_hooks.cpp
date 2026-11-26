#include "mech3/replay_hooks.h"

namespace mech3 {

namespace {
ReplayHooks* g_hooks = nullptr;
}  // namespace

void set_replay_hooks(ReplayHooks* hooks) { g_hooks = hooks; }
ReplayHooks* replay_hooks() { return g_hooks; }

}  // namespace mech3
