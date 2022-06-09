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


def real_matrix(image_size):
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    options = RGBMatrixOptions()
    options.rows = image_size[1]
    options.cols = image_size[0]
    options.chain_length = 1
    options.parallel = 1
    options.gpio_slowdown = 2

    return RGBMatrix(options=options)
