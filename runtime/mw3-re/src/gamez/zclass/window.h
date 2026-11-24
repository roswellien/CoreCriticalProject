#pragma once
#include <cstdint>

#include "gamez/zclass/cls_node.h"

// zClass\Window.c: the window node's rect (data +0 x, +4 y, +8 width, +0xc height).
namespace zcls {

int window_size(Node* node, int32_t* width, int32_t* height);  // 0x004fa020
int window_origin(Node* node, int32_t* x, int32_t* y);         // 0x004fa130
// A window node (class 3), 1 x 1, on list 14 (the HUD's views make theirs).
Node* window_create();                                         // 0x004f9e90
int window_set_size(Node* node, int32_t width, int32_t height); // 0x004f9fa0
int window_set_origin(Node* node, int32_t x, int32_t y);       // 0x004fa0b0

// FIX (bug), ours (issue 467): false only for a real window node with no area
// (width or height 0 or less), its size left in width and height. A missing or
// non-window node counts as having area, so the caller keeps its own fallback
// and no error is reported for it. A camera drawn into a window with no area
// gets a zero focal length, which the renderer's local lights reject.
bool window_has_area(Node* node, int32_t* width, int32_t* height);
// One line the first time each empty size is skipped (at most 8 sizes), so a
// player's log shows the skip without repeating every frame.
void log_skipped_empty_window(int32_t width, int32_t height);

}  // namespace zcls
