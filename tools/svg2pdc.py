#
# Copyright (c) 2015 Pebble Technology
#
'''
SVG2PDC converts SVG images to a PDC (Pebble Draw Command) binary format image or sequence. The PDC file format
consists of a header, followed by the binary representation of a PDC image or sequence.
The file header is as follows:
Magic Word (4 bytes) - 'PDCI' for image, 'PDCS' for sequence
Size (4 bytes) - size of PDC image or sequence following the header in bytes

Currently the following SVG elements are supported:
g, layer, path, rect, polyline, polygon, line, circle,

'''

import xml.etree.ElementTree as ET
import svg.path
import argparse
from struct import pack
import os
import glob
import sys

epsilon = sys.float_info.epsilon

DRAW_COMMAND_VERSION = 1
DRAW_COMMAND_TYPE_PATH = 1
DRAW_COMMAND_TYPE_CIRCLE = 2
DRAW_COMMAND_TYPE_PRECISE_PATH = 3

COORDINATE_SHIFT_WARNING_THRESHOLD = 0.1

xmlns = '{http://www.w3.org/2000/svg}'


def sum_points(p1, p2):
    return p1[0] + p2[0], p1[1] + p2[1]


def subtract_points(p1, p2):
    return p1[0] - p2[0], p1[1] - p2[1]


def round_point(p):
    return round(p[0] + epsilon), round(p[1] + epsilon)  # hack to get around the fact that python rounds negative
                                                         # numbers downwards


def scale_point(p, factor):
    return p[0] * factor, p[1] * factor


def find_nearest_valid_point(p):
    return (round(p[0] * 2.0) / 2.0), (round(p[1] * 2.0) / 2.0)


def find_nearest_valid_precise_point(p):
    return (round(p[0] * 8.0) / 8.0), (round(p[1] * 8.0) / 8.0)


def convert_to_pebble_coordinates(point, precise=False):
    # convert from graphic tool coordinate system to pebble coordinate system so that they render the same on
    # both

    if not precise:
        nearest = find_nearest_valid_point(point)  # used to give feedback to user if the point shifts considerably
    else:
        nearest = find_nearest_valid_precise_point(point)

    valid = compare_points(point, nearest)
    if not valid:
        print "Invalid point: ({}, {}). Closest supported coordinate: ({}, {})".format(point[0], point[1],
                                                                                       nearest[0], nearest[1])

    translated = sum_points(point, (-0.5, -0.5))   # translate point by (-0.5, -0.5)
    if precise:
        translated = scale_point(translated, 8)  # scale point for precise coordinates
    rounded = round_point(translated)

    return rounded, valid


def compare_points(p1, p2):
    return p1[0] == p2[0] and p1[1] == p2[1]


class InvalidPointException(Exception):
    pass

class Command():
    '''
    Draw command serialized structure:
    | Bytes | Field
    | 1     | Draw command type
    | 1     | Reserved byte
    | 1     | Stroke color
    | 1     | Stroke width
    | 1     | Fill color

    For Paths:
    | 1     | Open path
    | 1     | Unused/Reserved

    For Circles:
    | 2     | Radius

    Common:
    | 2     | Number of points (should always be 1 for circles)
    | n * 4 | Array of n points in the format below:


    Point:
    | 2     | x
    | 2     | y
    '''

    def __init__(self, points, translate, stroke_width=0, stroke_color=0, fill_color=0, precise=False,
                 raise_error=False):
        for i in range(len(points)):
            points[i], valid = convert_to_pebble_coordinates(sum_points(points[i], translate), precise)
            if not valid and raise_error:
                raise InvalidPointException("Invalid point in command")

        self.points = points
        self.stroke_width = stroke_width
        self.stroke_color = stroke_color
        self.fill_color = fill_color

    def serialize_common(self):
        return pack('<BBBB',
                    0,                  #reserved byte
                    self.stroke_color,
                    self.stroke_width,
                    self.fill_color)

    def serialize_points(self):
        s = pack('H', len(self.points))  # number of points (16-bit)
        for p in self.points:
            s += pack('<hh',
                      int(p[0]),        # x (16-bit)
                      int(p[1]))        # y (16-bit)
        return s


class PathCommand(Command):
    def __init__(self, points, path_open, translate, stroke_width=0, stroke_color=0, fill_color=0, precise=False,
                 raise_error=False):
        self.open = path_open
        self.type = DRAW_COMMAND_TYPE_PATH if not precise else DRAW_COMMAND_TYPE_PRECISE_PATH
        Command.__init__(self, points, translate, stroke_width, stroke_color, fill_color, precise, raise_error)

    def serialize(self):
        s = pack('B', self.type)   # command type
        s += self.serialize_common()
        s += pack('<BB',
                  int(self.open),   # open path boolean
                  0)                # unused byte in path
        s += self.serialize_points()
        return s

    def __str__(self):
        points = self.points[:]
        if self.type == DRAW_COMMAND_TYPE_PRECISE_PATH:
            type = 'P'
            for i in range(len(points)):
                points[i] = scale_point(points[i], 0.125)
        else:
            type = ''
        return "Path: [fill color:{}; stroke color:{}; stroke width:{}] {} {} {}".format(self.fill_color,
                                                                                         self.stroke_color,
                                                                                         self.stroke_width,
                                                                                         points,
                                                                                         self.open,
                                                                                         type)


class CircleCommand(Command):
    def __init__(self, center, radius, translate, stroke_width=0, stroke_color=0, fill_color=0):
        points = [(center[0], center[1])]
        Command.__init__(self, points, translate, stroke_width, stroke_color, fill_color)
        self.radius = radius

    def serialize(self):
        s = pack('B', DRAW_COMMAND_TYPE_CIRCLE)  # command type
        s += self.serialize_common()
        s += pack('H', self.radius)  # circle radius (16-bit)
        s += self.serialize_points()
        return s

    def __str__(self):
        return "Circle: [fill color:{}; stroke color:{}; stroke width:{}] {} {}".format(self.fill_color,
                                                                                        self.stroke_color,
                                                                                        self.stroke_width,
                                                                                        self.points[0],
                                                                                        self.radius)


def get_viewbox(root):
    try:
        coords = root.get('viewBox').split()
        return (float(coords[0]), float(coords[1])), (float(coords[2]), float(coords[3]))
    except (ValueError, TypeError):
        return (0, 0), (0, 0)


def get_translate(group):
    trans = group.get('translate')
    if trans is not None:
        pos = trans.find('translate')
        if pos < 0:
            print "No translation in translate"
            return 0, 0

        import ast
        try:
            return ast.literal_eval(trans[pos + len('translate'):])
        except (ValueError, TypeError):
            print "translate contains unsupported elements in addition to translation"

    return 0, 0


def convert_color(rgb, a, truncate=True):
    from pebble_image_routines import pebble_nearest_color_to_pebble_palette, pebble_truncate_color_to_pebble_palette, \
        rgba32_triplet_to_argb8

    r, g, b = (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF
    if truncate:
        (r, g, b, a) = pebble_truncate_color_to_pebble_palette(r, g, b, a)
    else:
        (r, g, b, a) = pebble_nearest_color_to_pebble_palette(r, g, b, a)

    return rgba32_triplet_to_argb8(r, g, b, a)


def parse_color(color, opacity, truncate):
    if color is None or color[0] != '#':
        return 0

    rgb = int(color[1:7], 16)
    a = int(opacity * 255)

    return convert_color(rgb, a, truncate)


def calc_opacity(a1, a2):
    try:
        a1 = float(a1)
    except (ValueError, TypeError):
        a1 = 1.0
    try:
        a2 = float(a2)
    except (ValueError, TypeError):
        a2 = 1.0

    return a1 * a2


def get_points_from_str(point_str):
    points = []
    for p in point_str.split():
        pair = p.split(',')
        try:
            points.append((float(pair[0]), float(pair[1])))
        except (ValueError, TypeError):
            return None
    return points


def parse_path(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    import svg.path
    d = element.get('d')
    if d is not None:
        path = svg.path.parse_path(d)
        points = [(lambda l: (l.real, l.imag))(line.start) for line in path]
        if not points:
            print "No points in parsed path"
            return None

        path_open = path[-1].end != path[0].start

        if path_open:
            points.append((path[-1].end.real, path[-1].end.imag))

        # remove last point if it matches first point
        if compare_points(points[0], points[-1]):
            points = points[0:-1]

        return PathCommand(points, path_open, translate, stroke_width, stroke_color, fill_color, precise, raise_error)
    else:
        print "Path element does not have path attribute"


def parse_circle(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    cx = element.get('cx')      # center x-value
    cy = element.get('cy')      # center y-value
    radius = element.get('r')   # radius
    if radius is None:
        radius = element.get('z')   # 'z' sometimes used instead of 'r' for radius
    if cx is not None and cy is not None and radius is not None:
        try:
            center = (float(cx), float(cy))
            radius = float(radius)
            return CircleCommand(center, radius, translate, stroke_width, stroke_color, fill_color)
        except ValueError:
            print "Unrecognized circle format"
    else:
        print "Unrecognized circle format"


def parse_polyline(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    points = get_points_from_str(element.get('points'))
    if not points:
        return None

    return PathCommand(points, True, translate, stroke_width, stroke_color, fill_color, precise, raise_error)


def parse_polygon(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    points = get_points_from_str(element.get('points'))
    if not points:
        return None

    return PathCommand(points, False, translate, stroke_width, stroke_color, fill_color, precise, raise_error)


def parse_line(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    try:
        points = [(float(element.get('x1')), float(element.get('y1'))),
                  (float(element.get('x2')), float(element.get('y2')))]
    except (TypeError, ValueError):
        return None

    return PathCommand(points, True, translate, stroke_width, stroke_color, fill_color, precise, raise_error)


def parse_rect(element, translate, stroke_width, stroke_color, fill_color, precise, raise_error):
    try:
        origin = (float(element.get('x')), float(element.get('y')))
        width = float(element.get('width'))
        height = float(element.get('height'))
    except (ValueError, TypeError):
        return None
    points = [origin, sum_points(origin, (width, 0)), sum_points(origin, (width, height)),
              sum_points(origin, (0, height))]

    return PathCommand(points, False, translate, stroke_width, stroke_color, fill_color, precise, raise_error)

svg_element_parser = {'path': parse_path,
                      'circle': parse_circle,
                      'polyline': parse_polyline,
                      'polygon': parse_polygon,
                      'line': parse_line,
                      'rect': parse_rect}


def create_command(translate, element, precise=False, raise_error=False, truncate_color=True):
    try:
        stroke_width = int(element.get('stroke-width'))
    except TypeError:
        stroke_width = 1
    except ValueError:
        stroke_width = 0

    stroke_color = parse_color(element.get('stroke'), calc_opacity(element.get('stroke-opacity'),
                               element.get('opacity')), truncate_color)
    fill_color = parse_color(element.get('fill'), calc_opacity(element.get('fill-opacity'), element.get('opacity')),
                             truncate_color)

    if stroke_color == 0 and fill_color == 0:
        return None

    if stroke_color == 0:
        stroke_width = 0
    elif stroke_width == 0:
        stroke_color = 0

    try:
        tag = element.tag[len(xmlns):]
    except IndexError:
        return None

    try:
        return svg_element_parser[tag](element, translate, stroke_width, stroke_color, fill_color, precise, raise_error)
    except KeyError:
        if tag != 'g' and tag != 'layer':
            print "Unsupported element: " + tag

    return None


def get_commands(translate, group, precise=False, raise_error=False, truncate_color=True):
    commands = []
    error = False
    for child in group.getchildren():
        # ignore elements that are marked display="none"
        display = child.get('display')
        if display is not None and display == 'none':
            continue
        try:
            tag = child.tag[len(xmlns):]
        except IndexError:
            continue

        # traverse tree of nested layers or groups
        if tag == 'layer' or tag == 'g':
            translate += get_translate(child)
            cmd_list, err = get_commands(translate, child, precise, raise_error, truncate_color)
            commands += cmd_list
            if err:
                error = True
        else:
            try:
                c = create_command(translate, child, precise, raise_error, truncate_color)
                if c is not None:
                    commands.append(c)
            except InvalidPointException:
                error = True

    return commands, error


def get_xml(filename):
    try:
        root = ET.parse(filename).getroot()
    except IOError:
        return None
    return root


def serialize(commands):
    output = pack('H', len(commands))   # number of commands in list
    for c in commands:
        output += c.serialize()

    return output


def print_commands(commands):
    for c in commands:
        print str(c)


def print_frames(frames):
    for i in range(len(frames)):
        print 'Frame {}:'.format(i + 1)
        print_commands(frames[i])


def serialize_frame(frame, duration):
    return pack('H', duration) + serialize(frame)   # Frame duration


def pack_header(size):
    return pack('<BBhh', DRAW_COMMAND_VERSION, 0, int(round(size[0])), int(round(size[1])))


def serialize_sequence(frames, size, duration, play_count):
    s = pack_header(size) + pack('H', play_count) + pack('H', len(frames))
    for f in frames:
        s += serialize_frame(f, duration)

    output = "PDCS"
    output += pack('I', len(s))
    output += s
    return output


def serialize_image(commands, size):
    s = pack_header(size)
    s += serialize(commands)

    output = "PDCI"
    output += pack('I', len(s))
    output += s
    return output


def get_info(xml):
    viewbox = get_viewbox(xml)
    translate = (-viewbox[0][0], -viewbox[0][1])  # subtract origin point in viewbox to get relative positions
    return translate, viewbox[1]


def parse_svg_image(filename, precise=False, raise_error=False):
    root = get_xml(filename)
    translate, size = get_info(root)
    cmd_list, error = get_commands(translate, root, precise, raise_error)
    return size, cmd_list, error


def parse_svg_sequence(dir_name, precise=False, raise_error=False):
    frames = []
    error_files = []
    file_list = sorted(glob.glob(dir_name + "/*.svg"))
    if not file_list:
        return
    translate, size = get_info(get_xml(file_list[0]))  # get the viewbox from the first file
    for filename in file_list:
        cmd_list, error = get_commands(translate, get_xml(filename), precise, raise_error)
        if cmd_list is not None:
            frames.append(cmd_list)
        if error:
            error_files.append(filename)
    return size, frames, error_files


def create_pdc_from_path(path, sequence, out_path, verbose, duration, play_count, precise=False, raise_error=False):
    dir_name = path
    output = ''
    error_files = []
    if os.path.exists(path):
        if verbose:
            print path + ":"
        if os.path.isfile(path):
            dir_name = os.path.dirname(path)
        frames = []
        commands = []
        if sequence:
            # get all .svg files in directory
            result = parse_svg_sequence(dir_name, precise, raise_error)
            if result:
                frames = result[1]
                size = result[0]
                error_files += result[2]
                output = serialize_sequence(frames, size, duration, play_count)
        elif os.path.isfile(path):
            size, commands, error = parse_svg_image(path, precise, raise_error)
            if commands:
                output = serialize_image(commands, size)
            if error:
                error_files += [path]

        if verbose:
            if sequence and frames:
                print_frames(frames)
            elif commands:
                print_commands(commands)
    else:
        print "Invalid path"

    if output != '':
        if out_path is None:
            if sequence:
                f = os.path.basename(dir_name.rstrip('/')) + '.pdc'
            else:
                base = os.path.basename(path)
                f = '.'.join(base.split('.')[:-1]) + '.pdc'
            out_path = os.path.join(dir_name, f)
        with open(out_path, 'w') as out_file:
            out_file.write(output)
            out_file.close()

    return error_files


def main(args):
    path = os.path.abspath(args.path)
    error_files = create_pdc_from_path(path, args.sequence, args.output, args.verbose, args.duration, args.play_count,
                                       args.precise)
    if error_files:
        print "Errors in the following files:"
        for ef in error_files:
            print "\t" + str(ef)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="Path to svg file or directory (with multiple svg files)")
    parser.add_argument('-s', '--sequence', action='store_true',
                        help="Path is a directory and a sequence will be produced as output")
    parser.add_argument('-o', '--output', type=str,
                        help="Output file path (.pdc will be appended to file name if it is not included in the path "
                             "specified")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Verbose output")
    parser.add_argument('-d', '--duration', type=int, default=33,
                        help="Duration (ms) of each frame in a sequence (only valid with --sequence) - default = 33ms")
    parser.add_argument('-c', '--play_count', type=int, default=1,
                        help="Number of times the sequence should play - default = 1")
    parser.add_argument('-p', '--precise', action='store_true',
                        help="Use sub-pixel precision for paths")
    args = parser.parse_args()
    main(args)


