import random


class FontCollection(object):
    def __init__(self, fonts):
        self.font_bank = fonts
        self.all_fonts = list(self.font_bank.keys())
        self.current_font_choices = list(self.all_fonts)
        self.font = None
        self.choose_font()

    def choose_font(self):
        font = random.choice(self.current_font_choices)
        self.current_font_choices.remove(font)
        if len(self.current_font_choices) < 1:
            self.current_font_choices.extend(self.all_fonts)
        self.font = self.font_bank[font]
        return self.font

    def get_current_font(self):
        return self.font
