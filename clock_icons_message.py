class Icons:
    def __init__(self, time, fisch, delay, hglass, upcnt, byo, end,
                 period1, period2, period3, period4, period5, flag):
        self.time = time
        self.fisch = fisch
        self.delay = delay
        self.hglass = hglass
        self.upcnt = upcnt
        self.byo = byo
        self.end = end
        self.period1 = period1
        self.period2 = period2
        self.period3 = period3
        self.period4 = period4
        self.period5 = period5
        self.flag = flag

    def byte1(self):
        return ((self.time * 0x01)
                | (self.fisch * 0x02)
                | (self.delay * 0x04)
                | (self.hglass * 0x08)
                | (self.upcnt * 0x10)
                | (self.byo * 0x20)
                | (self.end * 0x40))

    def byte2(self):
        return ((self.period1 * 0x01)
                | (self.period2 * 0x02)
                | (self.period3 * 0x04)
                | (self.period4 * 0x08)
                | (self.period5 * 0x10)
                | (self.flag * 0x20))

class GeneralIcons:
    def __init__(self, clear, sound, blackWhite, whiteBlack, bat, remain):
        self.clear = clear
        self.sound = sound
        self.blackWhite = blackWhite
        self.whiteBlack = whiteBlack
        self.bat = bat
        self.remain = remain

    def value(self):
        return ((self.clear * 0x01)
                | (self.sound * 0x02)
                | (self.blackWhite * 0x04)
                | (self.whiteBlack * 0x08)
                | (self.bat * 0x10)
                | (self.remain * 0x40))

class ClockIconsMessage:
    def __init__(self, left, right, general):
        self.left = left
        self.right = right
        self.general = general

    def get_message_id(self):
        return 0x02

    def get_message_data(self):
        return bytes([
            self.left.byte1(),
            self.right.byte1(),
            self.left.byte2(),
            self.right.byte2(),
            self.general.value(),
            0x00,
            0x00,
            0x00,
        ])


