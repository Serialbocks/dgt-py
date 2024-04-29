from datetime import timedelta

class ClockSetNRunMessage:
    def __init__(self, left_time, left_counts_up, right_time, right_counts_up, pause, toggle_on_lever):
        self.left_time = left_time
        self.right_time = right_time
        self.left_counts_up = left_counts_up
        self.right_counts_up = right_counts_up
        self.pause = pause
        self.toggle_on_lever = toggle_on_lever

    def get_message_id(self):
        return 0x0a

    def get_message_data(self):
        return [
            (int(self.left_time.total_seconds() // 3600) | (0x10 if self.left_counts_up else 0x00)),
            int(self.left_time.total_seconds() // 60 % 60),
            int(self.left_time.total_seconds() % 60),
            (int(self.right_time.total_seconds() // 3600) | (0x10 if self.right_counts_up else 0x00)),
            int(self.right_time.total_seconds() // 60 % 60),
            int(self.right_time.total_seconds() % 60),
            ((0x01 if not self.left_counts_up else 0x00)
             | (0x02 if not self.right_counts_up else 0x00)
             | (0x04 if self.pause else 0x00)
             | (0x08 if self.toggle_on_lever else 0x00))
        ]


