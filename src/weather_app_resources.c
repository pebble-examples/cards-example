/*
 * Copyright (c) 2015 Pebble Technology
 */

#include <pebble.h>
#include "weather_app_resources.h"

GDrawCommandImage *weather_app_resources_get_icon(WeatherAppIcon icon) {
  switch (icon) {
    case WEATHER_APP_ICON_HEAVY_RAIN:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_HEAVY_RAIN);

    case WEATHER_APP_ICON_LIGHT_RAIN:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_LIGHT_RAIN);

    case WEATHER_APP_ICON_HEAVY_SNOW:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_HEAVY_SNOW);

    case WEATHER_APP_ICON_LIGHT_SNOW:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_LIGHT_SNOW);

    case WEATHER_APP_ICON_PARTLY_CLOUDY:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_PARTLY_CLOUDY);

    case WEATHER_APP_ICON_SUNNY_DAY:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_SUNNY_DAY);

    default:
    case WEATHER_APP_ICON_GENERIC_WEATHER:
      return gdraw_command_image_create_with_resource(RESOURCE_ID_ICON_GENERIC_WEATHER);
  }
}
