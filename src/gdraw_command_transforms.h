/*
 * Copyright (c) 2015 Pebble Technology
 */

#pragma once

#include <pebble.h>

void attract_draw_command_image_to_square(GDrawCommandImage *image, int32_t normalized);
GPoint gpoint_attract_to_square(GPoint point, GSize size, int32_t normalized);
