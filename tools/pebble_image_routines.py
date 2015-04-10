#!/usr/bin/env python
#
# Copyright (c) 2015 Pebble Technology
#

import math

# This module contains common image and color routines used to convert images
# for use with Pebble.

# Create pebble 64 colors-table (r, g, b - 2 bits per channel)
def pebble_get_64color_palette():
    pebble_palette = []
    for i in xrange(0, 64):
        pebble_palette.append((
            ((i >> 4) & 0x3) * 85,   # R
            ((i >> 2) & 0x3) * 85,   # G
            ((i     ) & 0x3) * 85))  # B
    return pebble_palette


# match each rgba32 pixel to the nearest color in pebble_palette
# returns closest rgba32 color triplet (r, g, b, a)
def pebble_nearest_color_to_pebble_palette(r, g, b, a):
    a = ((a + 42) / 85) * 85  # fast nearest alpha for 2bit color range
    # clear transparent pixels (makes image more compress-able)
    # and required for greyscale tests
    if a == 0:
        r, g, b = (0, 0, 0)
    else:
        r = ((r + 42) / 85) * 85  # nearest for 2bit color range
        g = ((g + 42) / 85) * 85  # nearest for 2bit color range
        b = ((b + 42) / 85) * 85  # nearest for 2bit color range

    return r, g, b, a


# converts each rgba32 pixel to the next lower matching color (truncate method)
# in the pebble palette
# returns the truncated color as a rgba32 color triplet (r, g, b, a)
def pebble_truncate_color_to_pebble_palette(r, g, b, a):
    a = (a / 85) * 85  # truncate alpha for 2bit color range
    # clear transparent pixels (makes image more compress-able)
    # and required for greyscale tests
    if a == 0:
        r, g, b = (0, 0, 0)
    else:
        r = (r / 85) * 85  # truncate for 2bit color range
        g = (g / 85) * 85  # truncate for 2bit color range
        b = (b / 85) * 85  # truncate for 2bit color range

    return r, g, b, a


# converts a 32-bit RGBA color by channel to an ARGB8 (1 byte containing all 4 channels)
def rgba32_triplet_to_argb8(r, g, b, a):
    a, r, g, b = (a >> 6, r >> 6, g >> 6, b >> 6)
    argb8 = (a << 6) | (r << 4) | (g << 2) | b
    return argb8


# convert 32-bit color (r, g, b, a) to 32-bit RGBA word
def rgba32_triplet_to_rgba32(r, g, b, a):
    return (((r & 0xFF) << 24) | ((g & 0xFF) << 16) | ((b & 0xFF) << 8) | (a & 0xFF))


# takes number of colors and outputs PNG & PBI compatible bit depths for paletted images
def num_colors_to_bitdepth(num_colors):
    bitdepth = int(math.ceil(math.log(num_colors, 2)))

    # only bitdepth 1,2,4 and 8 supported by PBI and PNG
    if bitdepth == 0:
        # caused when palette has only 1 color
        bitdepth = 1
    elif bitdepth == 3:
        bitdepth = 4
    elif bitdepth > 4:
        bitdepth = 8

    return bitdepth
