
import ctypes
from magic import Magic

class Bitboard:
    ALL = -1

    RANKS = [0] * 8
    FILES = [0] * 8

    KNIGHT_DELTAS = [17, 15, 10, 6, -17, -15, -10, -6]
    BISHOP_DELTAS = [7, -7, 9, -9]
    ROOK_DELTAS = [1, -1, 8, -8]
    KING_DELTAS = [1, 7, 8, 9, -1, -7, -8, -9]
    WHITE_PAWN_DELTAS = [7, 9]
    BLACK_PAWN_DELTAS = [-7, -9]

    KNIGHT_ATTACKS = [0] * 64
    KING_ATTACKS = [0] * 64
    WHITE_PAWN_ATTACKS = [0] * 64
    BLACK_PAWN_ATTACKS = [0] * 64

    BETWEEN = [[0] * 64 for _ in range(64)]
    RAYS = [[0] * 64 for _ in range(64)]

    # Large overlapping attack table indexed using magic multiplication.
    ATTACKS = [0] * 88772

    def __init__(self):
        for sq in range(64):
            self.KNIGHT_ATTACKS[sq] = self.sliding_attacks(sq, self.ALL, self.KNIGHT_DELTAS)
            self.KING_ATTACKS[sq] = self.sliding_attacks(sq, self.ALL, self.KING_DELTAS)
            self.WHITE_PAWN_ATTACKS[sq] = self.sliding_attacks(sq, self.ALL, self.WHITE_PAWN_DELTAS)
            self.BLACK_PAWN_ATTACKS[sq] = self.sliding_attacks(sq, self.ALL, self.BLACK_PAWN_DELTAS)

            self.init_magics(sq, Magic.ROOK[sq], 12, self.ROOK_DELTAS)
            self.init_magics(sq, Magic.BISHOP[sq], 9, self.BISHOP_DELTAS)

            for a in range(64):
                for b in range(64):
                    if self.contains(self.sliding_attacks(a, 0, self.ROOK_DELTAS), b):
                        self.BETWEEN[a][b] = self.sliding_attacks(a, 1 << b, self.ROOK_DELTAS) & self.sliding_attacks(b, 1 << a, self.ROOK_DELTAS)
                        self.RAYS[a][b] = (1 << a) | (1 << b) | self.sliding_attacks(a, 0, self.ROOK_DELTAS) & self.sliding_attacks(b, 0, self.ROOK_DELTAS)
                    elif self.contains(self.sliding_attacks(a, 0, self.BISHOP_DELTAS), b):
                        self.BETWEEN[a][b] = self.sliding_attacks(a, 1 << b, self.BISHOP_DELTAS) & self.sliding_attacks(b, 1 << a, self.BISHOP_DELTAS)
                        self.RAYS[a][b] = (1 << a) | (1 << b) | self.sliding_attacks(a, 0, self.BISHOP_DELTAS) & self.sliding_attacks(b, 0, self.BISHOP_DELTAS)
    
    def square_distance(a, b):
        return max(abs(a // 8 - b // 8), abs(a % 8 - b % 8))

    # Slow attack set generation. Used only to bootstrap the attack tables.
    def sliding_attacks(square, occupied, deltas):
        attacks = 0
        for delta in deltas:
            sq = square
            while True:
                sq += delta
                if sq < 0 or sq >= 64 or Bitboard.square_distance(sq, sq - delta) > 2:
                    break
                attacks |= 1 << sq
                if Bitboard.contains(occupied, sq):
                    break
        return attacks

    def init_magics(square, magic, shift, deltas):
        subset = 0
        while True:
            attack = Bitboard.sliding_attacks(square, subset, deltas)
            idx = (int)((magic.factor * (subset & magic.mask)) >> (64 - shift)) + magic.offset
            assert Bitboard.ATTACKS[idx] == 0 or Bitboard.ATTACKS[idx] == attack
            Bitboard.ATTACKS[idx] = attack

            # Carry-rippler trick for enumerating subsets.
            subset = (subset - magic.mask) & magic.mask
            if subset == 0:
                break

    def bishop_attacks(square, occupied):
        magic = Magic.BISHOP[square]
        return Bitboard.ATTACKS[(int)((magic.factor * (occupied & magic.mask)) >> (64 - 9)) + magic.offset]

    def rook_attacks(square, occupied):
        magic = Magic.ROOK[square]
        return Bitboard.ATTACKS[(int)((magic.factor * (occupied & magic.mask)) >> (64 - 12)) + magic.offset]

    def queen_attacks(square, occupied):
        return Bitboard.bishop_attacks(square, occupied) ^ Bitboard.rook_attacks(square, occupied)

    def pawn_attacks(white, square):
        return Bitboard.WHITE_PAWN_ATTACKS[square] if white else Bitboard.BLACK_PAWN_ATTACKS[square]

    def lsb(b):
        assert b != 0
        return ctypes.c_int64(b & -b).bit_length() - 1

    def msb(b):
        assert b != 0
        return 63 - ctypes.c_int64(b).bit_length()

    def more_than_one(b):
        return (b & (b - 1)) != 0

    def contains(b, sq):
        return (b & (1 << sq)) != 0
    
    def square_set(b):
        set_ = set()
        while b != 0:
            sq = Bitboard.lsb(b)
            set_.add(sq)
            b &= b - 1
        return set_

    def rotate180(x):
        h1 = 0x5555555555555555
        h2 = 0x3333333333333333
        h4 = 0x0F0F0F0F0F0F0F0F
        v1 = 0x00FF00FF00FF00FF
        v2 = 0x0000FFFF0000FFFF
        x = ((x >>  1) & h1) | ((x & h1) <<  1)
        x = ((x >>  2) & h2) | ((x & h2) <<  2)
        x = ((x >>  4) & h4) | ((x & h4) <<  4)
        x = ((x >>  8) & v1) | ((x & v1) <<  8)
        x = ((x >> 16) & v2) | ((x & v2) << 16)
        x = (x >> 32)       | (x       << 32)
        return x
