from enum import Enum

class Role(Enum):
    PAWN = (0, "")
    KNIGHT = (1, "N")
    BISHOP = (2, "B")
    ROOK = (3, "R")
    QUEEN = (4, "Q")
    KING = (5, "K")

    def __init__(self, index, symbol):
        self.index = index
        self.symbol = symbol


