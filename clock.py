#!/usr/bin/env python
import datetime, argparse, time, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageColor

time_fmt = '%I:%M:%S%p'
date_fmt = '%b %d %Y'
image_size = (64, 32)
font_height_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_+='


def setup_matrix():
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    options = RGBMatrixOptions()
    options.rows = image_size[1]
    options.cols = image_size[0]
    options.chain_length = 1
    options.parallel = 1
    options.gpio_slowdown = 2

    return RGBMatrix(options=options)


def find_fonts(search_in):
    found_fonts = ['DejaVuSans.ttf']
    search_path = os.path.join(search_in, 'fonts')
    if os.path.exists(search_path):
        fonts_in_path = os.listdir(search_path)
        for fil in fonts_in_path:
            temp_file = os.path.join(search_path, fil)
            if os.path.isfile(temp_file) and temp_file[-4:].lower() == '.ttf':
                found_fonts.append(temp_file)
    found_fonts = [get_font_fit(fontName, 16) for fontName in found_fonts]
    return found_fonts


def get_font_fit(font_name, fit_height, start_size=None):
    if start_size is None:
        start_size = 32

    font = ImageFont.truetype(font_name, start_size)
    font_size = font.getsize(font_height_str)
    while font_size[1] > fit_height:
        start_size -= 1
        font = ImageFont.truetype(font_name, start_size)
        font_size = font.getsize(font_height_str)
    return font


def rgb_from_hue(hue):
    return ImageColor.getrgb('hsv({:d},100%,100%)'.format(hue))


def gen_color_table():
    return [rgb_from_hue(col) for col in range(360)]


def gen_rainbow_image(color_rot, color_table):
    img = Image.new("RGB", image_size)
    draw = ImageDraw.Draw(img)
    img_width = img.size[0]
    img_height = img.size[1]
    for i in range(img_width + img_height):
        color_int = (color_rot + i * 3) % 360
        draw.line(((i - img_height, img_height), (i, 0)), fill=color_table[color_int], width=1)
    return img


def gen_black_image():
    img = Image.new("RGB", image_size)
    draw = ImageDraw.Draw(img)
    draw.rectangle(((0, 0), img.size), fill=(0, 0, 0))
    return img


def clock(now, font, rot, fg, bg, invert=None):
    if invert is None:
        invert = False
    time_str = now.strftime(time_fmt)
    date_str = now.strftime(date_fmt)

    time_str_size = font.getsize(time_str)
    date_str_size = font.getsize(date_str)

    alpha_img = Image.new("L", image_size)
    alpha_draw = ImageDraw.Draw(alpha_img)

    if time_str_size[0] < 64 and date_str_size[0] < 64:
        # draw it once
        alpha_draw.text((0, 0), time_str, font=font, fill=255)
        alpha_draw.text((0, 16), date_str, font=font, fill=255)
    else:
        # animate it bouncing left to right
        time_x_siz = time_str_size[0]
        date_x_siz = date_str_size[0]
        time_x_var = time_x_siz - 64
        date_x_var = date_x_siz - 64
        half_time_x = time_x_siz / 2.0
        half_date_x = date_x_siz / 2.0

        time_x_inc = 0 if time_x_var < 0 else time_x_var
        date_x_inc = 0 if date_x_var < 0 else date_x_var

        sin_var = math.sin(rot)

        alpha_draw.text((int(round(sin_var * (time_x_inc / 2.0) - half_time_x + 32)), 0), time_str, font=font, fill=255)
        alpha_draw.text((int(round(sin_var * (date_x_inc / 2.0) - half_date_x + 32)), 16), date_str, font=font, fill=255)
    if not invert:
        return Image.composite(fg, bg, alpha_img).convert("RGB")
    else:
        return Image.composite(bg, fg, alpha_img).convert("RGB")


def choose_font(all_fonts, current_choices, debug=None):
    if debug is None:
        debug = False
    font = random.choice(current_choices)
    current_choices.remove(font)
    if len(current_choices) < 1:
        current_choices.extend(all_fonts)
    if debug:
        print('New font: {}'.format(font.getname()))
    return font


class FakeMatrix(object):
    def __init__(self):
        pass

    def SetImage(self, image, x, y):
        image.save('debug.png')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-fps', action='store_true', help='Enable the performance output')
    parser.add_argument('--debug-font', action='store_true',
                        help='Enable the font output (outputs font name when it changes)')
    parser.add_argument('--debug-single', action='store_true', help='Render a single frame and do not initialize the matrix')
    args = parser.parse_args()
    if args.debug_single:
        matrix = FakeMatrix()
    else:
        matrix = setup_matrix()

    # Loop invariants
    target_fps = 60
    target_time = 1 / target_fps
    font_time = 15 * target_fps
    invert_time = 33 * target_fps

    frame_rot_add = math.pi / (target_fps * 5)
    color_frame_rot_add = math.pi / (target_fps * 3)

    night_hour_begin = datetime.time(hour=20)
    night_hour_end = datetime.time(hour=6)

    # Loop variants
    rot = 0
    color_rot = 0
    color_rot_deg = 0
    font_at = 0
    invert_at = 0
    invert = False
    is_night_hours = False

    # Cached data
    color_table = gen_color_table()
    black_image = gen_black_image()
    rainbow_image_table = [gen_rainbow_image(rot, color_table) for rot in range(360)]

    fonts = find_fonts(os.path.dirname(os.path.realpath(__file__)))
    font_choices = fonts.copy()
    font = choose_font(fonts, font_choices, debug=args.debug_font)

    while True:
        before = time.time()
        rot = (rot + frame_rot_add) % (math.pi * 2)
        color_rot = (color_rot + color_frame_rot_add) % (math.pi * 2)
        color_rot_deg = int((color_rot / (2 * math.pi)) * 360.0) % 360
        font_at = (font_at + 1) % font_time
        invert_at = (invert_at + 1) % invert_time
        if font_at == 0:
            font = choose_font(fonts, font_choices, debug=args.debug_font)
        if invert_at == 0:
            invert = not invert

        now = datetime.datetime.now()
        if not is_night_hours and (now.time() > night_hour_begin or now.time() < night_hour_end):
            is_night_hours = True
            matrix.brightness = 10
        if is_night_hours and (night_hour_begin >= now.time() >= night_hour_end):
            is_night_hours = False
            matrix.brightness = 100
        img = clock(now, font, rot, rainbow_image_table[color_rot_deg], black_image, invert=invert)
        matrix.SetImage(img, 0, 0)
        if args.debug_single:
            return
        after = time.time()
        consumed_time = after - before
        sleep_time = target_time - consumed_time
        sleep_time = 0 if sleep_time < 0 else sleep_time
        if args.debug_fps:
            print('Frame time {:.3f} Target {:.3f} Sleep Time {:.3f}'.format(consumed_time, target_time, sleep_time))
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == '__main__':
    main()
