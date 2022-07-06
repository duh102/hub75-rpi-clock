class FakeMatrix(object):
    def __init__(self):
        self._brightness = 0

    def SetImage(self, image, x, y):
        pass

    def get_brightness(self):
        return self._brightness

    def set_brightness(self, brightness):
        self._brightness = brightness
        print('matrix brightness set to {:d}'.format(self._brightness))

    brightness = property(get_brightness, set_brightness)


class FakeMatrixSaving(FakeMatrix):
    def SetImage(self, image, x, y):
        image.save('debug.png')


def real_matrix(size_data):
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    options = RGBMatrixOptions()
    module_size = size_data.get_module_size()
    options.rows = module_size[1]
    options.cols = module_size[0]
    options.chain_length = size_data.width
    options.parallel = size_data.height
    # this is appropriate for an rpi3
    options.gpio_slowdown = 2
    # 120hz is more than enough for most applications, and will free up CPU time for other things
    options.limit_refresh_rate_hz = 120

    return RGBMatrix(options=options)
