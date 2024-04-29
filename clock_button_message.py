from dgt_clock_message import DgtClockMessage

class ClockButtonMessage(DgtClockMessage):
    def get_message_id(self):
        return 0x08

    def get_message_data(self):
        return bytearray()


