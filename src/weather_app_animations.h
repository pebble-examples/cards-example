/*
 * Copyright (c) 2015 Pebble Technology
 */

#pragma once

#include <pebble.h>
#include "weather_app_data.h"

Animation *weather_app_create_view_model_animation_numbers(WeatherAppMainWindowViewModel *view_model, WeatherAppDataPoint *next_data_point);

Animation *weather_app_create_view_model_animation_bgcolor(WeatherAppMainWindowViewModel *view_model, WeatherAppDataPoint *next_data_point);

Animation *weather_app_create_view_model_animation_icon(WeatherAppMainWindowViewModel *view_model, WeatherAppDataPoint *next_data_point, uint32_t duration);
