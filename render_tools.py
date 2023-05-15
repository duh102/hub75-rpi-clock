from PIL import Image, ImageDraw, ImageFont, ImageColor
import datetime


font_height_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-=!@#$%^&*()_+;:\'"[]{},.<>/?\\|`~ \t'

class TextImageCacheEntry(object):
    def __init__(self, bitmap, now_time, keepalive_time=None):
        self.bitmap = bitmap
        if keepalive_time is None:
            keepalive_time = datetime.timedelta(seconds=1)
        self.keepalive_time = keepalive_time
        self.last_use = now_time

    def get_bitmap(self, now_time):
        self.last_use = now_time
        return self.bitmap

    def get_keepalive_time(self):
        return self.keepalive_time

    def get_last_use(self):
        return self.last_use

    def is_expired(self, time_now):
        return (self.last_use + self.keepalive_time) < time_now

class TextImageCacheRenderer(object):
    def __init__(self, font):
        self.font = font

    def get_image(self, string):
        (width, height) = self.font.getsize(string)
        img = Image.new('L', (width, height))
        draw = ImageDraw.Draw(img)
        draw.text((0, height), string, font=self.font, fill=255, anchor='lb')
        return img

class TextImageCache(object):
    def __init__(self, renderer, time_func=None):
        if time_func is None:
            time_func = datetime.datetime.now
        self.time_func = time_func
        self.cache = {}
        self.renderer = renderer
        self.cache_check_time = self.time_func()
        self.cache_clear_time = datetime.timedelta(seconds=10)

    def get_string(self, string, keepalive_time=None):
        now = self.time_func()
        if string not in self.cache or self.cache[string].is_expired(now):
            self.cache[string] = TextImageCacheEntry(self.renderer.get_image(string), now, keepalive_time=keepalive_time)
        self._check_cache_expiration(now)
        return self.cache[string].get_bitmap(now)

    def _check_cache_expiration(self, now):
      if (self.cache_check_time + self.cache_clear_time) >= now:
        return
      self.cache_check_time = now
      to_del = []
      for string, entry in self.cache.items():
        if entry.is_expired(now):
          to_del.append(string)
      for string in to_del:
        del self.cache[string]

class BitmapBackedFont(object):
    def __init__(self, name, font, bitmap_text_drawing):
        self.name = name
        self.font = font
        self.bitmap_text_drawing = bitmap_text_drawing

    def get_name(self):
        return self.name

    def get_pil_font(self):
        return self.font

    def get_bm_font(self):
        return self.bitmap_text_drawing

class BitmapTextDrawing(object):
    def width(self, string):
        pass

    def text(self, position, image, string):
        pass

class CharacterCachedBitmapTextDrawing(BitmapTextDrawing):
    def __init__(self, font, font_map=None, fit_height=None):
        self.font = font
        if fit_height is None:
            fit_height = 16
        self.fit_height = fit_height
        if font_map is None:
            font_map = self.__generate_font_map(font, self.fit_height)
        self.font_map = font_map

    def __generate_font_map(self, font, fit_height):
        # Pre-populate the map with the expected contents
        # Could we make an object for this? Undoubtedly! But currently it's not worth the effort
        font_map = {char: {'width': 0, 'height': 0, 'img': None} for char in font_height_str}
        self.real_height = font.getsize(font_height_str)[1]
        for char, char_attributes in font_map.items():
            (width, height) = font.getsize(char)
            img = Image.new('L', (width, self.real_height))
            draw = ImageDraw.Draw(img)
            draw.text((0, self.real_height), str(char), font=font, fill=255, anchor='lb')
            char_attributes['width'] = width
            char_attributes['height'] = height
            char_attributes['img'] = img
        return font_map

    def __get_from_fontmap(self, character):
        if character not in font_height_str:
            return None
        return self.font_map[character]

    def width(self, string):
        acc = 0
        for char in string:
            bm_char = self.__get_from_fontmap(char)
            # if we don't support the character, skip it
            if bm_char is None:
                continue
            else:
                acc += bm_char['width']
        return acc

    def text(self, position, image, string):
        x_pos = 0
        img_size = image.size
        # No sense drawing off the image
        if position[1] + self.real_height < 0:
            return
        if position[1] > img_size[1]:
            return
        for char in string:
            bm_char = self.__get_from_fontmap(char)
            if bm_char is None:
                # if we don't support the character, skip it
                continue
            else:
                # Skip this character if it's off the left side of the image or if we're off the right side
                if (x_pos + position[0] + bm_char['width'] < 0) or (x_pos + position[0] > img_size[0]):
                    x_pos += bm_char['width']
                    continue
                image.paste(bm_char['img'], (x_pos+position[0], position[1]))
                x_pos += bm_char['width']

class StringCachedBitmapTextDrawing(BitmapTextDrawing):
    def __init__(self, font, cache_keepalive=None):
        self.font = font
        self.text_cache = TextImageCache(TextImageCacheRenderer(self.font))
        self.cache_keepalive = cache_keepalive

    def width(self, string):
        return self.font.getsize(string)[0]

    def text(self, position, image, string):
        string_image = self.text_cache.get_string(string, keepalive_time=self.cache_keepalive)
        image.paste(string_image, (position[0], position[1]))


def get_font_fit(font_name, fit_height, start_size=None):
    if start_size is None:
        start_size = 32

    font = ImageFont.truetype(font_name, start_size)
    font_size = font.getsize(font_height_str)
    while font_size[1] > fit_height:
        start_size -= 1
        font = ImageFont.truetype(font_name, start_size)
        font_size = font.getsize(font_height_str)
    bm_draw = StringCachedBitmapTextDrawing(font)
    return BitmapBackedFont(font.getname()[0], font, bm_draw)


def rgb_from_hue(hue, saturation=None, value=None):
    if saturation is None:
        saturation = 100
    if value is None:
        value = 100
    hue = hue % 360
    saturation = min(max(saturation, 0), 100)
    value = min(max(value, 0), 100)
    return ImageColor.getrgb('hsv({:d},{:d}%,{:d}%)'.format(hue, saturation, value))


def gen_color_table(saturation=None, value=None):
    return [rgb_from_hue(col, saturation=saturation, value=value) for col in range(360)]


def gen_rainbow_image(color_rot, color_table, image_size):
    img = Image.new("RGB", image_size)
    draw = ImageDraw.Draw(img)
    img_width = img.size[0]
    img_height = img.size[1]
    for i in range(img_width + img_height):
        color_int = (color_rot + i * 3) % 360
        draw.line(((i - img_height, img_height), (i, 0)), fill=color_table[color_int], width=1)
    return img


def gen_black_image(image_size):
    img = Image.new("RGB", image_size)
    draw = ImageDraw.Draw(img)
    draw.rectangle(((0, 0), img.size), fill=(0, 0, 0))
    return img
