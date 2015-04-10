/*
 * Copyright (c) 2015 Pebble Technology
 */

#pragma once

#include <pebble.h>

typedef enum {
  WEATHER_APP_ICON_GENERIC_WEATHER,
  WEATHER_APP_ICON_HEAVY_RAIN,
  WEATHER_APP_ICON_LIGHT_RAIN,
  WEATHER_APP_ICON_HEAVY_SNOW,
  WEATHER_APP_ICON_LIGHT_SNOW,
  WEATHER_APP_ICON_PARTLY_CLOUDY,
  WEATHER_APP_ICON_SUNNY_DAY,
} WeatherAppIcon;

GDrawCommandImage *weather_app_resources_get_icon(WeatherAppIcon icon);
