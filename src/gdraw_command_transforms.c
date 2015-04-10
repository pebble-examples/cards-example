/*
 * Copyright (c) 2015 Pebble Technology
 */

#include <pebble.h>
#include "gdraw_command_transforms.h"

#define ABS(a) (((a) > 0) ? (a) : -1 * (a))

static int16_t prv_int_attract_to(int16_t i, int16_t bounds, int32_t normalized) {
  const int16_t delta_0 = (int16_t) ((0 + 1) - i);
  const int16_t delta_b = (int16_t) ((bounds - 1) - i);
  const int16_t delta = ABS(delta_0) < ABS(delta_b) ? delta_0 : delta_b;

  return (int16_t) (i + delta * normalized / ANIMATION_NORMALIZED_MAX);
}

GPoint gpoint_attract_to_square(GPoint point, GSize size, int32_t normalized) {
  point.y += 1;
  point = GPoint(
      prv_int_attract_to(point.x, size.w, normalized),
      prv_int_attract_to(point.y, size.h, normalized));
  return point;
}

typedef struct {
  GSize size;
  int32_t normalized;
} ToSquareCBContext;

static bool prv_attract_draw_command_list_to_square_cb(GDrawCommand *command, uint32_t index, void *context) {
  ToSquareCBContext *to_square = context;
  for (int i = 0; i < gdraw_command_get_num_points(command); i++) {
    gdraw_command_set_point(command, i, gpoint_attract_to_square(gdraw_command_get_point(command, i), to_square->size, to_square->normalized));
  }
  return true;
}

void attract_draw_command_list_to_square(GDrawCommandList *list, GSize size, int32_t normalized) {
  ToSquareCBContext ctx = {
      .size = size,
      .normalized = normalized,
  };
  gdraw_command_list_iterate(list, prv_attract_draw_command_list_to_square_cb, &ctx);
}

void attract_draw_command_image_to_square(GDrawCommandImage *image, int32_t normalized) {
  attract_draw_command_list_to_square(gdraw_command_image_get_command_list(image), gdraw_command_image_get_bounds_size(image), normalized);
}
