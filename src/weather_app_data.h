/*
 * Copyright (c) 2015 Pebble Technology
 */

#pragma once

#include <pebble.h>

struct WeatherAppMainWindowViewModel;

typedef void (*WeatherAppMainWindowViewModelFunc)(struct WeatherAppMainWindowViewModel* model);

typedef struct {
  WeatherAppMainWindowViewModelFunc announce_changed;
  struct {
    GColor top;
    GColor bottom;
    int32_t to_bottom_normalized;
  } bg_color;
  char *city;
  struct {
    int16_t value;
    char text[8];
  } temperature;
  struct {
    GDrawCommandImage *draw_command;
    int32_t to_square_normalized;
  } icon;
  struct {
    int16_t idx;
    int16_t num;
    char text[8];
  } pagination;
  struct {
    int16_t high;
    int16_t low;
    char text[20];
  } highlow;
  char *description;
} WeatherAppMainWindowViewModel;

//! calls model's .announce_changed or does nothing if NULL
void weather_app_main_window_view_model_announce_changed(WeatherAppMainWindowViewModel *model);

typedef struct {
  char *city;
  char *description;
  int icon;
  int16_t current;
  int16_t high;
  int16_t low;
} WeatherAppDataPoint;

typedef struct {
  int16_t temperature;
  int16_t low;
  int16_t high;
} WeatherDataViewNumbers;


void weather_app_view_model_set_highlow(WeatherAppMainWindowViewModel *model, int16_t high, int16_t low);

void weather_app_view_model_set_temperature(WeatherAppMainWindowViewModel *model, int16_t value);
void weather_app_view_model_set_icon(WeatherAppMainWindowViewModel *model, GDrawCommandImage *image);

WeatherDataViewNumbers weather_app_data_point_view_model_numbers(WeatherAppDataPoint *data_point);

GDrawCommandImage *weather_app_data_point_create_icon(WeatherAppDataPoint *data_point);

void weather_app_view_model_fill_strings_and_pagination(WeatherAppMainWindowViewModel *view_model, WeatherAppDataPoint *data_point);

void weather_view_model_fill_numbers(WeatherAppMainWindowViewModel *model, WeatherDataViewNumbers numbers);

void weather_app_view_model_fill_all(WeatherAppMainWindowViewModel *model, WeatherAppDataPoint *data_point);

void weather_app_view_model_fill_colors(WeatherAppMainWindowViewModel *model, GColor color);

void weather_app_view_model_deinit(WeatherAppMainWindowViewModel *model);

GColor weather_app_data_point_color(WeatherAppDataPoint *data_point);

int weather_app_num_data_points(void);

WeatherAppDataPoint *weather_app_data_point_at(int idx);
WeatherAppDataPoint *weather_app_data_point_delta(WeatherAppDataPoint *dp, int delta);
