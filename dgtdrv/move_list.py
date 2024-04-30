from move import Move
from role import Role

class MoveList:
    def __init__(self, capacity=256):
        self.buffer = [Move() for _ in range(capacity)]
        self.size = 0

    def clear(self):
        self.size = 0

    def __len__(self):
        return self.size

    def __getitem__(self, i):
        assert i < self.size
        return self.buffer[i]

    def is_empty(self):
        return self.size == 0

    def push_normal(self, board, role, from_pos, capture, to):
        self.buffer[self.size].set(board, Move.NORMAL, role, from_pos, capture, to, None)
        self.size += 1

    def push_promotion(self, board, from_pos, capture, to, promotion):
        self.buffer[self.size].set(board, Move.NORMAL, Role.PAWN, from_pos, capture, to, promotion)
        self.size += 1

    def push_castle(self, board, king, rook):
        self.buffer[self.size].set(board, Move.CASTLING, Role.KING, king, False, rook, None)
        self.size += 1

    def push_en_passant(self, board, capturer, to):
        self.buffer[self.size].set(board, Move.EN_PASSANT, Role.PAWN, capturer, True, to, None)
        self.size += 1

    def sort(self):
        self.buffer = sorted(self.buffer[:self.size])

    def any_match(self, predicate):
        return any(predicate(move) for move in self.buffer[:self.size])

    def retain(self, predicate):
        self.buffer = [move for move in self.buffer[:self.size] if predicate(move)]
        self.size = len(self.buffer)

    def __iter__(self):
        return iter(self.buffer[:self.size])


