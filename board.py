from bitboard import Bitboard
from zobrist_hash import ZobristHash
from piece import Piece
from move import Move
from role import Role
from square import Square
from move_list import MoveList
from result import Result

class Board:
    def __init__(self):
        self.pawns = 0xff00000000ff00
        self.knights = 0x4200000000000042
        self.bishops = 0x2400000000000024
        self.rooks = 0x8100000000000081
        self.queens = 0x800000000000008
        self.kings = 0x1000000000000010

        self.white = 0xffff
        self.black = 0xffff000000000000
        self.occupied = 0xffff00000000ffff

        self.turn = True
        self.epSquare = 0
        self.castlingRights = self.rooks

        self.incrementalHash = ZobristHash.hashPieces(self) ^ ZobristHash.hashTurn(self)

    def __init__(self, board):
        self.pawns = board.pawns
        self.knights = board.knights
        self.bishops = board.bishops
        self.rooks = board.rooks
        self.queens = board.queens
        self.kings = board.kings

        self.white = board.white
        self.black = board.black
        self.occupied = board.occupied

        self.turn = board.turn
        self.epSquare = board.epSquare
        self.castlingRights = board.castlingRights

        self.incrementalHash = ZobristHash.hashPieces(self) ^ ZobristHash.hashTurn(self)

    def __init__(self, pawns, knights, bishops, rooks, queens, kings, white, black, turn, epSquare, castlingRights):
        self.pawns = pawns
        self.knights = knights
        self.bishops = bishops
        self.rooks = rooks
        self.queens = queens
        self.kings = kings

        self.white = white
        self.black = black
        self.occupied = white | black

        self.turn = turn
        self.epSquare = epSquare
        self.castlingRights = castlingRights

        self.incrementalHash = ZobristHash.hashPieces(self) ^ ZobristHash.hashTurn(self)

    @staticmethod
    def emptyBoard():
        return Board(0, 0, 0, 0, 0, 0, 0, 0, True, 0, 0)

    def isOccupied(self, square):
        return Bitboard.contains(self.occupied, square)

    def discard(self, square):
        if not self.isOccupied(square):
            return
        role = self.roleAt(square)
        mask = 1 << square

        if role == Role.PAWN:
            self.pawns ^= mask
        elif role == Role.KNIGHT:
            self.knights ^= mask
        elif role == Role.BISHOP:
            self.bishops ^= mask
        elif role == Role.ROOK:
            self.rooks ^= mask
        elif role == Role.QUEEN:
            self.queens ^= mask
        elif role == Role.KING:
            self.kings ^= mask

        color = self.whiteAt(square)
        if color:
            self.white ^= mask
        else:
            self.black ^= mask

        self.occupied ^= mask
        self.incrementalHash ^= ZobristHash.hashPiece(square, color, role)

    def put(self, square, color, role):
        self.discard(square)

        mask = 1 << square

        if role == Role.PAWN:
            self.pawns ^= mask
        elif role == Role.KNIGHT:
            self.knights ^= mask
        elif role == Role.BISHOP:
            self.bishops ^= mask
        elif role == Role.ROOK:
            self.rooks ^= mask
        elif role == Role.QUEEN:
            self.queens ^= mask
        elif role == Role.KING:
            self.kings ^= mask

        if color:
            self.white ^= mask
        else:
            self.black ^= mask

        self.occupied ^= mask
        self.incrementalHash ^= ZobristHash.hashPiece(square, color, role)

    def roleAt(self, square):
        if Bitboard.contains(self.pawns, square):
            return Role.PAWN
        elif Bitboard.contains(self.knights, square):
            return Role.KNIGHT
        elif Bitboard.contains(self.bishops, square):
            return Role.BISHOP
        elif Bitboard.contains(self.rooks, square):
            return Role.ROOK
        elif Bitboard.contains(self.queens, square):
            return Role.QUEEN
        elif Bitboard.contains(self.kings, square):
            return Role.KING
        return None

    def whiteAt(self, square):
        return Bitboard.contains(self.white, square)

    def zobristHash(self):
        return self.incrementalHash ^ ZobristHash.hashCastling(self) ^ ZobristHash.hashEnPassant(self)

    def pieceMap(self):
        map = {}
        occupied = self.occupied
        while occupied != 0:
            sq = Bitboard.lsb(occupied)
            map[sq] = Piece(self.whiteAt(sq), self.roleAt(sq))
            occupied &= occupied - 1
        return map

    def play(self, move):
        self.epSquare = 0

        if move.type == Move.NORMAL:
            if move.role == Role.PAWN and abs(move.from_square_square - move.to) == 16:
                theirPawns = self.them() & self.pawns
                if theirPawns != 0:
                    sq = move.from_square + (8 if self.turn else -8)
                    if Bitboard.pawnAttacks(self.turn, sq) & theirPawns != 0:
                        self.epSquare = sq

            if self.castlingRights != 0:
                if move.role == Role.KING:
                    self.castlingRights &= Bitboard.RANKS[7 if self.turn else 0]
                elif move.role == Role.ROOK:
                    self.castlingRights &= ~(1 << move.from_square)

                if move.capture:
                    self.castlingRights &= ~(1 << move.to)

            self.discard(move.from_square)
            self.put(move.to, self.turn, move.promotion if move.promotion is not None else move.role)
        elif move.type == Move.CASTLING:
            self.castlingRights &= Bitboard.RANKS[7 if self.turn else 0]
            rookTo = Square.combine(Square.D1 if move.to < move.from_square else Square.F1, move.to)
            kingTo = Square.combine(Square.C1 if move.to < move.from_square else Square.G1, move.from_square)
            self.discard(move.from_square)
            self.discard(move.to)
            self.put(rookTo, self.turn, Role.ROOK)
            self.put(kingTo, self.turn, Role.KING)
        elif move.type == Move.EN_PASSANT:
            self.discard(Square.combine(move.to, move.from_square))
            self.discard(move.from_square)
            self.put(move.to, self.turn, Role.PAWN)

        self.turn = not self.turn
        self.incrementalHash ^= ZobristHash.POLYGLOT[780]

    def us(self):
        return self.byColor(self.turn)

    def them(self):
        return self.byColor(not self.turn)

    def byColor(self, white):
        return self.white if white else self.black

    def king(self, white):
        return Bitboard.lsb(self.kings & self.byColor(white))

    def sliderBlockers(self, king):
        snipers = self.them() & (
            Bitboard.rookAttacks(king, 0) & (self.rooks ^ self.queens) |
            Bitboard.bishopAttacks(king, 0) & (self.bishops ^ self.queens))

        blockers = 0

        while snipers != 0:
            sniper = Bitboard.lsb(snipers)
            between = Bitboard.BETWEEN[king][sniper] & self.occupied
            if not Bitboard.moreThanOne(between):
                blockers |= between
            snipers &= snipers - 1

        return blockers

    def isCheck(self):
        return self.attacksTo(self.king(self.turn), not self.turn) != 0

    def attacksTo(self, sq, attacker):
        return self.attacksTo(sq, attacker, self.occupied)

    def attacksTo(self, sq, attacker, occupied):
        return self.byColor(attacker) & (
            Bitboard.rookAttacks(sq, occupied) & (self.rooks ^ self.queens) |
            Bitboard.bishopAttacks(sq, occupied) & (self.bishops ^ self.queens) |
            Bitboard.KNIGHT_ATTACKS[sq] & self.knights |
            Bitboard.KING_ATTACKS[sq] & self.kings |
            Bitboard.pawnAttacks(not attacker, sq) & self.pawns)

    def legalMoves(self, moves):
        moves.clear()

        if self.epSquare != 0:
            self.genEnPassant(moves)

        king = self.king(self.turn)
        checkers = self.attacksTo(king, not self.turn)
        if checkers == 0:
            target = ~self.us()
            self.genNonKing(target, moves)
            self.genSafeKing(king, target, moves)
            self.genCastling(king, moves)
        else:
            self.genEvasions(king, checkers, moves)

        blockers = self.sliderBlockers(king)
        if blockers != 0 or self.epSquare != 0:
            moves.retain(lambda m: self.isSafe(king, m, blockers))

    def hasLegalEnPassant(self):
        moves = MoveList(2)
        self.genEnPassant(moves)

        king = self.king(self.turn)
        blockers = self.sliderBlockers(king)
        return moves.anyMatch(lambda m: self.isSafe(king, m, blockers))

    def genNonKing(self, mask, moves):
        self.genPawn(mask, moves)

        knights = self.us() & self.knights
        while knights != 0:
            from_ = Bitboard.lsb(knights)
            targets = Bitboard.KNIGHT_ATTACKS[from_] & mask
            while targets != 0:
                to = Bitboard.lsb(targets)
                moves.pushNormal(self, Role.KNIGHT, from_, self.isOccupied(to), to)
                targets &= targets - 1
            knights &= knights - 1

        bishops = self.us() & self.bishops
        while bishops != 0:
            from_ = Bitboard.lsb(bishops)
            targets = Bitboard.bishopAttacks(from_, self.occupied) & mask
            while targets != 0:
                to = Bitboard.lsb(targets)
                moves.pushNormal(self, Role.BISHOP, from_, self.isOccupied(to), to)
                targets &= targets - 1
            bishops &= bishops - 1

        rooks = self.us() & self.rooks
        while rooks != 0:
            from_ = Bitboard.lsb(rooks)
            targets = Bitboard.rookAttacks(from_, self.occupied) & mask
            while targets != 0:
                to = Bitboard.lsb(targets)
                moves.pushNormal(self, Role.ROOK, from_, self.isOccupied(to), to)
                targets &= targets - 1
            rooks &= rooks - 1

        queens = self.us() & self.queens
        while queens != 0:
            from_ = Bitboard.lsb(queens)
            targets = Bitboard.queenAttacks(from_, self.occupied) & mask
            while targets != 0:
                to = Bitboard.lsb(targets)
                moves.pushNormal(self, Role.QUEEN, from_, self.isOccupied(to), to)
                targets &= targets - 1
            queens &= queens - 1

    def genSafeKing(self, king, mask, moves):
        targets = Bitboard.KING_ATTACKS[king] & mask
        while targets != 0:
            to = Bitboard.lsb(targets)
            if self.attacksTo(to, not self.turn) == 0:
                moves.pushNormal(self, Role.KING, king, self.isOccupied(to), to)
            targets &= targets - 1

    def genEvasions(self, king, checkers, moves):
        sliders = checkers & (self.bishops ^ self.rooks ^ self.queens)
        attacked = 0
        while sliders != 0:
            slider = Bitboard.lsb(sliders)
            attacked |= Bitboard.RAYS[king][slider] ^ (1 << slider)
            sliders &= sliders - 1

        self.genSafeKing(king, ~self.us() & ~attacked, moves)

        if checkers != 0 and not Bitboard.moreThanOne(checkers):
            checker = Bitboard.lsb(checkers)
            target = Bitboard.BETWEEN[king][checker] | checkers
            self.genNonKing(target, moves)

    def genPawn(self, mask, moves):
        capturers = self.us() & self.pawns
        while capturers != 0:
            from_ = Bitboard.lsb(capturers)
            targets = Bitboard.pawnAttacks(self.turn, from_) & self.them() & mask
            while targets != 0:
                to = Bitboard.lsb(targets)
                self.addPawnMoves(from_, True, to, moves)
                targets &= targets - 1
            capturers &= capturers - 1

        singleMoves = ~self.occupied & (self.white & self.pawns) << 8 if self.turn else (self.black & self.pawns) >> 8
        doubleMoves = ~self.occupied & (singleMoves << 8 if self.turn else singleMoves >> 8) & Bitboard.RANKS[3 if self.turn else 4]
        singleMoves &= mask
        doubleMoves &= mask

        while singleMoves != 0:
            to = Bitboard.lsb(singleMoves)
            from_ = to + (-8 if self.turn else 8)
            self.addPawnMoves(from_, False, to, moves)
            singleMoves &= singleMoves - 1

        while doubleMoves != 0:
            to = Bitboard.lsb(doubleMoves)
            from_ = to + (-16 if self.turn else 16)
            moves.pushNormal(self, Role.PAWN, from_, False, to)
            doubleMoves &= doubleMoves - 1

    def addPawnMoves(self, from_, capture, to, moves):
        if Square.rank(to) == (7 if self.turn else 0):
            moves.pushPromotion(self, from_, capture, to, Role.QUEEN)
            moves.pushPromotion(self, from_, capture, to, Role.KNIGHT)
            moves.pushPromotion(self, from_, capture, to, Role.ROOK)
            moves.pushPromotion(self, from_, capture, to, Role.BISHOP)
        else:
            moves.pushNormal(self, Role.PAWN, from_, capture, to)

    def genEnPassant(self, moves):
        pawns = self.us() & self.pawns & Bitboard.pawnAttacks(not self.turn, self.epSquare)
        while pawns != 0:
            pawn = Bitboard.lsb(pawns)
            moves.pushEnPassant(self, pawn, self.epSquare)
            pawns &= pawns - 1

    def genCastling(self, king, moves):
        rooks = self.castlingRights & Bitboard.RANKS[0 if self.turn else 7]
        while rooks != 0:
            rook = Bitboard.lsb(rooks)
            path = Bitboard.BETWEEN[king][rook]
            if (path & self.occupied) == 0:
                kingTo = Square.combine(Square.C1 if rook < king else Square.G1, king)
                kingPath = Bitboard.BETWEEN[king][kingTo] | (1 << kingTo) | (1 << king)
                while kingPath != 0:
                    sq = Bitboard.lsb(kingPath)
                    if self.attacksTo(sq, not self.turn, self.occupied ^ (1 << king)) != 0:
                        break
                    kingPath &= kingPath - 1
                if kingPath == 0:
                    moves.pushCastle(self, king, rook)
            rooks &= rooks - 1

    def isSafe(self, king, move, blockers):
        if move.type == Move.NORMAL:
            return not Bitboard.contains(self.us() & blockers, move.from_square) or Square.aligned(move.from_square, move.to, king)
        elif move.type == Move.EN_PASSANT:
            occupied = self.occupied
            occupied ^= 1 << move.from_square
            occupied ^= 1 << Square.combine(move.to, move.from_square)  # captured pawn
            occupied |= 1 << move.to
            return (Bitboard.rookAttacks(king, occupied) & self.them() & (self.rooks ^ self.queens)) == 0 and \
                   (Bitboard.bishopAttacks(king, occupied) & self.them() & (self.bishops ^ self.queens)) == 0
        else:
            return True

    def rotate180(self):
        self.pawns = Bitboard.rotate180(self.pawns)
        self.knights = Bitboard.rotate180(self.knights)
        self.bishops = Bitboard.rotate180(self.bishops)
        self.rooks = Bitboard.rotate180(self.rooks)
        self.queens = Bitboard.rotate180(self.queens)
        self.kings = Bitboard.rotate180(self.kings)

        self.white = Bitboard.rotate180(self.white)
        self.black = Bitboard.rotate180(self.black)
        self.occupied = Bitboard.rotate180(self.occupied)

        self.castlingRights = Bitboard.rotate180(self.castlingRights)

        self.incrementalHash = ZobristHash.hashPieces(self)

    D4 = 1 << Square.square(3, 3)
    D5 = 1 << Square.square(3, 4)
    E4 = 1 << Square.square(4, 3)
    E5 = 1 << Square.square(4, 4)
    centralSquares = D4 | D5 | E4 | E5

    def resultSignal(self):
        if (self.kings & self.white & self.centralSquares) == 0 or (self.kings & self.black & self.centralSquares) == 0:
            return None
        elif (self.kings & self.E4) != 0 and (self.kings & self.D5) != 0:
            return Result.WHITE_WIN
        elif (self.kings & self.E5) != 0 and (self.kings & self.D4) != 0:
            return Result.BLACK_WIN
        else:
            return Result.DRAW

    def equalSetup(self, b):
        return self.pawns == b.pawns and self.knights == b.knights and self.bishops == b.bishops and \
               self.rooks == b.rooks and self.queens == b.queens and self.kings == b.kings and \
               self.white == b.white and self.black == b.black and self.occupied == b.occupied

    def debugBoard(self):
        sb = ""
        for row in range(7, -1, -1):
            for file in range(8):
                if file > 0:
                    sb += ' '
                square = row * 8 + file
                if self.isOccupied(square):
                    s = self.roleAt(square).symbol
                    if s == "":
                        s = "P"
                    sb += s if self.whiteAt(square) else s.lower()
                else:
                    sb += '.'
            sb += '\n'
        return sb


