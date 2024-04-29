from dgt_clock_message import DgtClockMessage

class ClockVersionMessage(DgtClockMessage):
    def get_message_id(self):
        return 0x09

    def get_message_data(self):
        return bytearray()
