from PIL import Image, ImageDraw, ImageFont, ImageColor


font_height_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-=!@#$%^&*()_+;:\'"[]{},.<>/?\\|`~ \t'


def generate_font_map(font, fit_height):
    # Pre-populate the map with the expected contents
    # Could we make an object for this? Undoubtedly! But currently it's not worth the effort
    font_map = {char: {'width': 0, 'img': None} for char in font_height_str}
    for char, char_attributes in font_map.items():
        width = font.getsize(char)[0]
        img = Image.new('L', (width, fit_height))
        draw = ImageDraw.Draw(img)
        draw.text((0, fit_height), str(char), font=font, fill=255, anchor='lb')
        char_attributes['width'] = width
        char_attributes['img'] = img
    return font_map


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
    def __init__(self, font, font_map=None, fit_height=None):
        self.font = font
        if fit_height is None:
            fit_height = 16
        self.fit_height = fit_height
        if font_map is None:
            font_map = generate_font_map(font, self.fit_height)
        self.font_map = font_map

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
        if position[1] + self.fit_height < 0:
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
                if not (x_pos + position[0] + bm_char['width'] < 0) or (x_pos + position[0] > img_size[0]):
                    image.paste(bm_char['img'], (x_pos+position[0], position[1]))
                x_pos += bm_char['width']


def get_font_fit(font_name, fit_height, start_size=None):
    if start_size is None:
        start_size = 32

    font = ImageFont.truetype(font_name, start_size)
    font_size = font.getsize(font_height_str)
    while font_size[1] > fit_height:
        start_size -= 1
        font = ImageFont.truetype(font_name, start_size)
        font_size = font.getsize(font_height_str)
    bm_draw = BitmapTextDrawing(font, fit_height=fit_height)
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


def gen_color_table():
    return [rgb_from_hue(col) for col in range(360)]


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
