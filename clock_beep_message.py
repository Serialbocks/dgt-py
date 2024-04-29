class ClockBeepMessage:
    def __init__(self, duration):
        self.duration = duration

    def get_message_id(self):
        return 0x0b

    def get_message_data(self):
        return [self.duration]
