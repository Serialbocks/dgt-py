class SevenSegment:
    def __init__(self, top, right_top, right_bottom, bottom, left_bottom, left_top, center):
        self.top = top
        self.right_top = right_top
        self.right_bottom = right_bottom
        self.bottom = bottom
        self.left_bottom = left_bottom
        self.left_top = left_top
        self.center = center

    def as_byte(self):
        return ((self.top * 0x01)
                | (self.right_top * 0x02)
                | (self.right_bottom * 0x04)
                | (self.bottom * 0x08)
                | (self.left_bottom * 0x10)
                | (self.left_top * 0x20)
                | (self.center * 0x40))

class DotsAndOnes:
    def __init__(self, left_one, left_dot, left_semicolon, right_one, right_dot, right_semicolon):
        self.left_one = left_one
        self.left_dot = left_dot
        self.left_semicolon = left_semicolon
        self.right_one = right_one
        self.right_dot = right_dot
        self.right_semicolon = right_semicolon

    def as_byte(self):
        return ((self.right_dot * 0x01)
                | (self.right_semicolon * 0x02)
                | (self.right_one * 0x04)
                | (self.left_dot * 0x08)
                | (self.left_semicolon * 0x10)
                | (self.left_one * 0x20))

class ClockDisplayMessage:
    def __init__(self, a_location, b_location, c_location, d_location, e_location, f_location, dots_and_ones, beep):
        self.a_location = a_location
        self.b_location = b_location
        self.c_location = c_location
        self.d_location = d_location
        self.e_location = e_location
        self.f_location = f_location
        self.dots_and_ones = dots_and_ones
        self.beep = beep

    def get_message_id(self):
        return 0x01

    def get_message_data(self):
        return bytes([
            self.c_location.as_byte(),
            self.b_location.as_byte(),
            self.a_location.as_byte(),
            self.f_location.as_byte(),
            self.e_location.as_byte(),
            self.d_location.as_byte(),
            self.dots_and_ones.as_byte(),
            0x03 if self.beep else 0x01
        ])


