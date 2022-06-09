import fps_tools
import render_tools
import font_utils
import math
from PIL import Image

time_fmt = '%I:%M:%S%p'
date_fmt = '%b %d %Y'


class ClockPattern(object):
    def __init__(self, function_data, fonts):
        self.function_data = function_data
        self.font_collection = font_utils.FontCollection(fonts)
        self.font = self.font_collection.get_current_font()
        debug_font = self.function_data.get_debug_flag('font')
        if debug_font is not None and debug_font:
            print('Clock using {:s}'.format(self.font.get_name()))

        # ## dT dependent data
        # Units are increments of pi per second; one full circle is 2 pi, so this is roughly one circle per 10s
        self.movement_rotation = fps_tools.DTAwareRotation(d_dt=math.pi/5)
        # Ditto, this is roughly one full rainbow rotation per 6s
        self.color_rotation = fps_tools.DTAwareRotation(d_dt=math.pi/3)
        # Unit is 1/Hz, we want to rotate the fonts once every 30s
        self.font_rotation = fps_tools.DTAwarePeriodicValue(d_dt=1/30, reset_func=lambda: self.choose_new_font())
        # Unit is 1/Hz, we want to invert the display once every 60s
        self.invert_toggle = fps_tools.DTAwarePeriodicValue(d_dt=1/60)

        # Normal variables
        self.inverted = False

        # Cached data
        self.color_table = render_tools.gen_color_table()
        self.black_image = render_tools.gen_black_image(function_data.get_image_size())
        self.rainbow_image_table = [render_tools.gen_rainbow_image(rot, self.color_table, function_data.get_image_size())
                                    for rot in range(360)]

    def choose_new_font(self):
        self.font = self.font_collection.choose_font()
        debug_font = self.function_data.get_debug_flag('font')
        if debug_font is not None and debug_font:
            print('Clock using {:s}'.format(self.font.get_name()))

    def invert_display(self):
        self.inverted = not self.inverted

    def frame(self, dt):
        # Update all our dT-dependent data
        self.movement_rotation.dt(dt)
        self.color_rotation.dt(dt)
        self.font_rotation.dt(dt)
        self.invert_toggle.dt(dt)

        now = self.function_data.get_now()
        if now is None:
            return
        time_str = now.strftime(time_fmt)
        date_str = now.strftime(date_fmt)
        bitmap_drawing = self.font.get_bm_font()

        time_str_size = bitmap_drawing.width(time_str)
        date_str_size = bitmap_drawing.width(date_str)

        image_size = self.function_data.get_image_size()

        alpha_img = Image.new("L", image_size)

        if time_str_size < image_size[0] and date_str_size < image_size[0]:
            # draw it once
            bitmap_drawing.text((0, 0), alpha_img, time_str)
            bitmap_drawing.text((0, 16), alpha_img, date_str)
        else:
            # animate it bouncing left to right
            time_x_siz = time_str_size
            date_x_siz = date_str_size
            time_x_var = time_x_siz - image_size[0]
            date_x_var = date_x_siz - image_size[0]
            half_time_x = time_x_siz / 2.0
            half_date_x = date_x_siz / 2.0

            time_x_inc = 0 if time_x_var < 0 else time_x_var
            date_x_inc = 0 if date_x_var < 0 else date_x_var

            sin_var = math.sin(self.movement_rotation.get_rotation())

            bitmap_drawing.text((int(round(sin_var * (time_x_inc / 2.0) - half_time_x + 32)), 0), alpha_img, time_str)
            bitmap_drawing.text((int(round(sin_var * (date_x_inc / 2.0) - half_date_x + 32)), 16), alpha_img, date_str)
        fg = self.rainbow_image_table[int(self.color_rotation.rotation_degrees)]
        bg = self.black_image
        if not self.inverted:
            return Image.composite(fg, bg, alpha_img).convert("RGB")
        else:
            return Image.composite(bg, fg, alpha_img).convert("RGB")
