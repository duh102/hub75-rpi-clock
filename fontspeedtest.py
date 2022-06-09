#!/usr/bin/env python3
import datetime, os
from PIL import Image, ImageDraw
import clock


def run_benchmark():
    data = {}
    fonts = clock.find_fonts(os.path.dirname(os.path.realpath(__file__)))
    for font_name in fonts.keys():
        font_data = fonts[font_name]
        bitmap_drawing = font_data['bm_draw']
        run_data = {}
        data[font_name] = run_data
        runs = 100
        run_time = datetime.timedelta(microseconds=0)
        image = Image.new("L", clock.image_size)
        draw = ImageDraw.Draw(image)
        while run_time.total_seconds() < 10:
            if run_time.total_seconds() > 1:
                next_runs = int(12 * runs / run_time.total_seconds())
                runs = next_runs if next_runs > runs else runs * 10
            else:
                runs *= 15
            print('Running {:s} for {:d} times'.format(font_name, runs))
            pre_run = datetime.datetime.now()
            for i in range(runs):
                bitmap_drawing.text((0, 0), image, "12:55:00")
            post_run = datetime.datetime.now()
            run_time = post_run - pre_run
        run_data['runs'] = runs
        run_data['time'] = run_time
    for fontName, fontRow in sorted(data.items(), key=lambda x: x[0]):
        runs_per_time = fontRow['runs'] / fontRow['time'].total_seconds()
        print('{:s},{:.2f}'.format(fontName, runs_per_time))


if __name__ == '__main__':
    run_benchmark()
