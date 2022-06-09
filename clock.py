#!/usr/bin/env python
import argparse
import datetime
import os
import time

import fps_tools
import render_tools
import rpi_matrix
import clock_pattern


def find_fonts(search_in):
    found_fonts = ['DejaVuSans.ttf']
    search_path = os.path.join(search_in, 'fonts')
    if os.path.exists(search_path):
        fonts_in_path = os.listdir(search_path)
        for fil in fonts_in_path:
            temp_file = os.path.join(search_path, fil)
            if os.path.isfile(temp_file) and temp_file[-4:].lower() == '.ttf':
                found_fonts.append(temp_file)
    generated_fonts = [render_tools.get_font_fit(font_name, 16) for font_name in found_fonts]
    found_fonts = {font_data.get_name(): font_data for font_data in generated_fonts}
    return found_fonts


class NightClock(object):
    def __init__(self, morning_hour=None, night_hour=None):
        if morning_hour is None:
            morning_hour = 6
        if night_hour is None:
            night_hour = 9
        self.morning_hour = datetime.time(hour=morning_hour)
        self.night_hour = datetime.time(hour=night_hour)
        self.is_night_hours = False

    def update_time(self, instant):
        if not self.is_night_hours and (instant.time() > self.night_hour or instant.time() < self.morning_hour):
            self.is_night_hours = True
        if self.is_night_hours and (self.night_hour >= instant.time() >= self.morning_hour):
            self.is_night_hours = False

    def is_night_hours(self):
        return self.is_night_hours


class FunctionData(object):
    def __init__(self, night_clock, fps_clock, image_size, debug_flags):
        self.night_clock = night_clock
        self.fps_clock = fps_clock
        self.now = None
        self.image_size = image_size
        self.debug_flags = debug_flags

    def set_now(self, now):
        self.now = now

    def get_now(self):
        return self.now

    def get_fps_clock(self):
        return self.fps_clock

    def get_night_clock(self):
        return self.night_clock

    def get_image_size(self):
        return self.image_size

    def get_debug_flags(self):
        return self.debug_flags

    def get_debug_flag(self, flag_name):
        return self.debug_flags.get(flag_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-fps', action='store_true', help='Enable the performance output')
    parser.add_argument('--debug-font', action='store_true',
                        help='Enable the font output (outputs font name when it changes)')
    parser.add_argument('--debug-single', action='store_true', help='Render a single frame')
    parser.add_argument('--debug-no-matrix', action='store_true', help='Use a fake matrix, discard output')
    parser.add_argument('--debug-no-matrix-save', action='store_true', help='Use a fake matrix, output to file')
    parser.add_argument('--debug-action', choices=['clock', 'weather'], help='Perform specific function rather than rotating through them')
    args = parser.parse_args()

    debug_options = {
        'fps': args.debug_fps,
        'font': args.debug_font,
        'single': args.debug_single,
        'no-matrix': args.debug_no_matrix,
        'no-matrix-save': args.debug_no_matrix_save,
        'action': args.debug_action
    }

    # Loop invariants
    image_size = (64, 32)
    night_clock = NightClock()
    fps_clock = fps_tools.FPSClock(target_fps=60)
    function_data = FunctionData(night_clock, fps_clock, image_size, debug_options)

    fonts = find_fonts(os.path.dirname(os.path.realpath(__file__)))

    clock_pat = clock_pattern.ClockPattern(function_data, fonts)

    if args.debug_no_matrix:
        matrix = rpi_matrix.FakeMatrix()
    elif args.debug_no_matrix_save:
        matrix = rpi_matrix.FakeMatrixSaving()
    else:
        matrix = rpi_matrix.real_matrix(image_size)

    while True:
        fps_clock.start_frame()

        # Update the pattern in progress
        function_data.set_now(datetime.datetime.now())
        night_clock.update_time(function_data.get_now())
        img = clock_pat.frame(fps_clock.get_dt())
        matrix.SetImage(img, 0, 0)

        # Perform the FPS counting
        fps_clock.finish_render()
        sleep_time = fps_clock.get_sleep_time()
        if args.debug_fps:
            print('Frame time {:.3f} Target {:.3f} Sleep Time {:.3f}'.format(fps_clock.get_last_render_time(),
                                                                             fps_clock.get_dt_target(), sleep_time))
        if args.debug_single:
            return
        if sleep_time > 0:
            time.sleep(sleep_time)
        fps_clock.finish_frame()


if __name__ == '__main__':
    main()
