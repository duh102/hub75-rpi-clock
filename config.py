class DisplayConfig(object):
    def __init__(self, width=None, height=None, module_size=None):
        if width is None:
            width = 1
        if height is None:
            height = 1
        if module_size is None:
            module_size = (64, 32)

        # Width of the full display, in modules
        self.width = width
        # Height of the full display, in modules
        self.height = height
        # The size of one single module; all modules must be the same topography
        # It's also recommended to buy them all in one purchase, as they can have differing controllers
        self.module_size = module_size

        # Cached, because this won't change (though it is derived)
        self.image_size = (
            self.width * self.module_size[0],
            self.height * self.module_size[1]
        )

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_module_size(self):
        return self.module_size

    def get_image_size(self):
        return self.image_size

    def serialize(self):
        return {
            'width': self.width,
            'height': self.height,
            'module-size': self.module_size
        }

    @classmethod
    def deserialize(cls, json_obj):
        return cls(
            width=json_obj.get('width'),
            height=json_obj.get('height'),
            module_size=json_obj.get('module-size')
        )
