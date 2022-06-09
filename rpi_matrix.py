class FakeMatrix(object):
    def __init__(self):
        self.brightness = 0

    def SetImage(self, image, x, y):
        pass


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
