class DgtProtocolException(Exception):
    pass

class Button:
    BACK = 'BACK'
    PLUS = 'PLUS'
    RUN = 'RUN'
    MINUS = 'MINUS'
    OK = 'OK'

class ClockAck:
    def __init__(self, data):
        if len(data) != 7:
            raise DgtProtocolException(f"ClockAck expects exactly 7 bytes of data (got {len(data)})")

        self.ack0 = (data[1] & 0x7f) | ((data[3] << 3) & 0x80)
        self.ack1 = (data[2] & 0x7f) | ((data[3] << 2) & 0x80)
        self.ack2 = (data[4] & 0x7f) | ((data[0] << 3) & 0x80)
        self.ack3 = (data[5] & 0x7f) | ((data[0] << 2) & 0x80)

    def is_error(self):
        return self.ack0 == 0x40

    def is_auto_generated(self):
        return (self.ack1 & 0x80) == 0x80

    def is_ready(self):
        return self.ack1 == 0x81

    def button_pressed(self):
        if self.ack3 == 0x31:
            return Button.BACK
        elif self.ack3 == 0x32:
            return Button.PLUS
        elif self.ack3 == 0x33:
            return Button.RUN
        elif self.ack3 == 0x34:
            return Button.MINUS
        elif self.ack3 == 0x35:
            return Button.OK
        else:
            return None

    def is_display_ack(self):
        return self.ack1 == 0x01

    def is_button_ack(self):
        return self.ack1 == 0x08

    def is_version_ack(self):
        return self.ack1 == 0x09

    def clock_version(self):
        return [self.ack2 >> 4, self.ack2 & 0x0f]

    def is_set_n_run_ack(self):
        return self.ack1 == 0x0a

    def is_beep_ack(self):
        return self.ack1 == 0x0b


