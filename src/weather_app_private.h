/*
 * Copyright (c) 2015 Pebble Technology
 */

#pragma once

#include <pebble.h>
#include "weather_app_data.h"

typedef struct {
  WeatherAppDataPoint *data_point;
  WeatherAppMainWindowViewModel view_model;
  Animation *previous_animation;
  TextLayer *fake_statusbar;
  TextLayer *pagination_layer;
  TextLayer *city_layer;
  Layer *horizontal_ruler_layer;
  TextLayer *temperature_layer;
  TextLayer *highlow_layer;
  TextLayer *description_layer;
  Layer *icon_layer;
} WeatherAppData;
