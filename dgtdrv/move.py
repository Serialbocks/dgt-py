from bitboard import Bitboard
from square import Square
from role import Role

class Move:
    NORMAL = 0
    EN_PASSANT = 1
    CASTLING = 2

    def __init__(self, move=None):
        if move is None:
            self.type = None
            self.role = None
            self.from_square = None
            self.capture = None
            self.to = None
            self.promotion = None
            self.score = None
        else:
            self.type = move.type
            self.role = move.role
            self.from_square = move.from_square
            self.capture = move.capture
            self.to = move.to
            self.promotion = move.promotion
            self.score = move.score

    def set(self, board, move_type, role, from_square, capture, to, promotion):
        self.type = move_type
        self.role = role
        self.from_square = from_square
        self.capture = capture
        self.to = to
        self.promotion = promotion

        defending_pawns = (
            Bitboard.pawn_attacks(board.turn, to)
            & board.pawns
            & board.them()
        )

        move_value = self.piece_value(board, role, to) - self.piece_value(board, role, from_square)

        self.score = (
            (promotion.index << 26 if promotion else 0)
            + (1 << 25 if capture else 0)
            + ((6 if defending_pawns == 0 else 5 - role.index) << 22)
            + (512 + move_value << 12)
            + (to << 6)
            + from_square
        )

    def __lt__(self, other):
        return self.score < other.score

    def uci(self):
        to = self.to

        if self.type == Move.CASTLING:
            to = Square.combine(Square.C1 if self.to < self.from_square else Square.G1, self.from_square)

        builder = (
            chr(Square.file(self.from_square) + ord('a'))
            + chr(Square.rank(self.from_square) + ord('1'))
            + chr(Square.file(to) + ord('a'))
            + chr(Square.rank(to) + ord('1'))
        )
        if self.promotion:
            builder += self.promotion.symbol.lower()
        return builder

    def is_zeroing(self):
        return self.capture or self.role == Role.PAWN

    @staticmethod
    def piece_value(board, role, square):
        return PSQT[role.index][board.turn ^ Square.mirror(square)]

PSQT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5, 5, 10, 25, 25, 10, 5, 5, 0, 0, 0, 20, 21, 0, 0, 0, 5, -5, -10, 0, 0, -10, -5, 5, 5, 10, 10, -31, -31, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    [-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 0, 0, 0, -20, -40, -30, 0, 10, 15, 15, 10, 0, -30, -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30, -30, 5, 10, 15, 15, 11, 5, -30, -40, -20, 0, 5, 5, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50],
    [-20, -10, -10, -10, -10, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 10, 10, 5, 0, -10, -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 10, 10, 10, 10, 10, 10, -10, -10, 5, 0, 0, 0, 0, 5, -10, -20, -10, -10, -10, -10, -10, -10, -20],
    [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, 10, 10, 10, 10, 5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 5, 5, 0, 0, 0],
    [-20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 5, 5, 5, 0, -10, -5, 0, 5, 5, 5, 5, 0, -5, 0, 0, 5, 5, 5, 5, 0, -5, -10, 5, 5, 5, 5, 5, 0, -10, -10, 0, 5, 0, 0, 0, 0, -10, -20, -10, -10, -5, -5, -10, -10, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -20, -30, -30, -40, -40, -30, -30, -20, -10, -20, -20, -20, -20, -20, -20, -10, 20, 20, 0, 0, 0, 0, 20, 20, 0, 30, 10, 0, 0, 10, 30, 0]
]

