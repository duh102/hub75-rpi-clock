import weather
import render_tools
import patterns
import datetime
import concurrent.futures
from PIL import Image, ImageDraw


class WeatherPattern(patterns.DisplayPattern):
    cache_duration = datetime.timedelta(minutes=30)
    temp_thresholds = {
        37: (255, 50, 50),  # Very hot, almost exclusively red
        32: (255, 150, 100),  # Hot, red orange
        26: (255, 200, 150),  # Warm, yellowish orange
        21: (100, 255, 100),  # Mild, nice and green
        10: (100, 200, 255),  # Cool, more blue
        0:  (50, 100, 255),  # Freezing, very blue
    }

    def __init__(self, function_data, fonts):
        super().__init__(function_data, fonts)
        self.futureExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        min_width = self.function_data.get_size_data().get_image_size()[0]
        test_str = '100F'
        min_font_name = list(self.fonts.keys())[0]  # Pick a random one to make sure we have something
        self.font = self.fonts[min_font_name]
        for name, bbf in self.fonts.items():
            font_width = bbf.get_bm_font().width(test_str)
            if font_width < min_width:
                self.font = bbf
                min_width = font_width
                min_font_name = name
        if self.function_data.get_debug_flag('font'):
            print('Weather using {:s}'.format(min_font_name))
        self.weather_cache = weather.WeatherCache(zip_code='27529', country='US')
        self.cache_time = None
        self.image_cache = self.__default_image()
        self.__submit_weather_future()

    @staticmethod
    def __retrieve_limit_value(values, begin, end):
        time_limited_values = [value for value in values if value.is_timely(begin, end)]
        return time_limited_values

    def __get_temp_colorcode(self, value):
        if value is None:
            return (255, 255, 255)  # default to white
        sel_color = self.temp_thresholds[min(self.temp_thresholds.keys())]
        for temp_tup in sorted(self.temp_thresholds.items(), key=lambda temp_tuple: temp_tuple[0]):
            (temp, color) = (temp_tup[0], temp_tup[1])
            if value.get_value() > temp:
                sel_color = color
            else:
                break
        return sel_color

    def __default_image(self):
        bm_font = self.font.get_bm_font()
        image_size = self.function_data.get_size_data().get_image_size()
        text = 'Retrieving'
        max_width = bm_font.width(text)
        draw_w = int(image_size[0]/2 - max_width/2)
        bg = render_tools.gen_black_image(image_size)
        bm_font.text((draw_w, 0), bg, text)
        return bg

    def __submit_weather_future(self):
        self.weather_data_future = self.futureExecutor.submit(self.weather_cache.get_current_prediction)
        self.weather_data_future.add_done_callback(lambda future: self.__gen_image(future))

    @staticmethod
    def __fmt_time(timestamp):
        if timestamp.hour % 12 != 0 or timestamp.hour == 12:
            return '{:d}{:s}'.format(timestamp.hour % 12, 'A' if timestamp.hour < 12 else 'P')
        return 'MN'

    def __gen_image(self, future, wait=None):
        if wait is None:
            wait = False
        now = self.function_data.get_now()
        weather_data = None
        try:
            wait_time = None if wait else 0.1
            weather_data = future.result(wait_time)
            self.cache_time = now
        except concurrent.futures.TimeoutError:
            print('Timed out waiting for weather data')

        max_fmt = '--F'
        min_fmt = '--F'
        bm_font = self.font.get_bm_font()
        lookahead_max = None
        lookahead_min = None

        if weather_data is not None:
            day_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            valid_temps = self.__retrieve_limit_value(weather_data.get_temp_data().get_data_points(), day_begin, day_end)
            max_temps = sorted(valid_temps, key=lambda val: (val.get_value(), val.get_time()), reverse=True)
            min_temps = sorted(valid_temps, key=lambda val: (val.get_value(), val.get_time()))
            lookahead_max = max_temps[0] if len(max_temps) > 0 else None
            lookahead_min = min_temps[0] if len(min_temps) > 0 else None
            if lookahead_max is not None:
                tm = lookahead_max.get_time()
                max_fmt = '{:.0f}F {:s}'.format(lookahead_max.get_value_f(), self.__fmt_time(tm))
            if lookahead_min is not None:
                tm = lookahead_min.get_time()
                min_fmt = '{:.0f}F {:s}'.format(lookahead_min.get_value_f(), self.__fmt_time(tm))

        image_size = self.function_data.get_size_data().get_image_size()
        bg = render_tools.gen_black_image(image_size)
        hi_legend_text = 'Hi:'
        hi_legend_width = bm_font.width(hi_legend_text)
        lo_legend_text = 'Lo:'
        lo_legend_width = bm_font.width(lo_legend_text)
        max_legend_width = max(hi_legend_width, lo_legend_width)

        max_width = max_legend_width + 1 + max(bm_font.width(max_fmt), bm_font.width(min_fmt))
        draw_w = int(image_size[0]/2 - max_width/2)

        hi_img = Image.new('RGB', image_size)
        hi_al = Image.new('L', image_size)
        hi_draw = ImageDraw.Draw(hi_img)
        bm_font.text((draw_w, 0), bg, hi_legend_text)
        bm_font.text((draw_w+max_legend_width+1, 0), hi_al, max_fmt)
        hi_draw.rectangle(((0, 0), image_size), fill=self.__get_temp_colorcode(lookahead_max))
        bg = Image.composite(hi_img, bg, hi_al).convert("RGB")

        lo_img = Image.new('RGB', image_size)
        lo_al = Image.new('L', image_size)
        lo_draw = ImageDraw.Draw(lo_img)
        bm_font.text((draw_w, int(image_size[1]/2)), bg, lo_legend_text)
        bm_font.text((draw_w+max_legend_width+1, int(image_size[1]/2)), lo_al, min_fmt)
        lo_draw.rectangle(((0, 0), image_size), fill=self.__get_temp_colorcode(lookahead_min))
        bg = Image.composite(lo_img, bg, lo_al).convert("RGB")

        self.image_cache = bg

    def frame(self, dt):
        now = self.function_data.get_now()
        if now is None:
            return render_tools.gen_black_image(self.function_data.get_size_data().get_image_size())
        if (self.cache_time is None or self.cache_time < now-self.cache_duration) \
           and (self.weather_data_future is None or self.weather_data_future.done()):
            self.__submit_weather_future()
        if self.function_data.get_debug_flag('single') and self.weather_data_future is not None:
            self.__gen_image(self.weather_data_future, wait=True)
        return self.image_cache
