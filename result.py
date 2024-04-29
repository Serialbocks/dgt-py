from enum import Enum

class Result(Enum):
    WHITE_WIN = "1-0"
    BLACK_WIN = "0-1"
    DRAW = "1/2-1/2"

    def result_string(self):
        return self.value
