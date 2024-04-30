from square import Square

from typing import List, Optional
from enum import Enum
from collections import defaultdict
from board_dump import BoardDump
from field_update import FieldUpdate
from move_list import MoveList

class Color(Enum):
    WHITE = 0
    BLACK = 1

class Role(Enum):
    KING = 0
    QUEEN = 1
    ROOK = 2
    BISHOP = 3
    KNIGHT = 4
    PAWN = 5

class Result(Enum):
    WHITE_WIN = 0
    BLACK_WIN = 1
    DRAW = 2

class Square:
    @staticmethod
    def rank(square: int) -> int:
        return square // 8

    @staticmethod
    def file(square: int) -> int:
        return square % 8


class Board:
    def __init__(self):
        self.pieces = [[None] * 8 for _ in range(8)]

    def equal_setup(self, other: 'Board') -> bool:
        for rank in range(8):
            for file in range(8):
                if self.pieces[rank][file] != other.pieces[rank][file]:
                    return False
        return True

    def role_at(self, square: int) -> Optional[Role]:
        rank = Square.rank(square)
        file = Square.file(square)
        return self.pieces[rank][file]

    def discard(self, square: int) -> None:
        rank = Square.rank(square)
        file = Square.file(square)
        self.pieces[rank][file] = None

    def put(self, square: int, color: Color, role: Role) -> None:
        rank = Square.rank(square)
        file = Square.file(square)
        self.pieces[rank][file] = (color, role)

    def rotate180(self) -> None:
        for rank in range(4):
            for file in range(8):
                self.pieces[rank][file], self.pieces[7 - rank][7 - file] = self.pieces[7 - rank][7 - file], self.pieces[rank][file]

    def result_signal(self) -> Optional[Result]:
        # Check if both kings are in the central four squares
        white_king_square = None
        black_king_square = None
        for rank in range(3, 5):
            for file in range(3, 5):
                if self.pieces[rank][file] == (Color.WHITE, Role.KING):
                    white_king_square = rank * 8 + file
                elif self.pieces[rank][file] == (Color.BLACK, Role.KING):
                    black_king_square = rank * 8 + file
        if white_king_square is not None and black_king_square is not None:
            if Square.rank(white_king_square) % 2 == Square.file(white_king_square) % 2:
                return Result.WHITE_WIN
            elif Square.rank(black_king_square) % 2 == Square.file(black_king_square) % 2:
                return Result.BLACK_WIN
            else:
                return Result.DRAW
        return None

class Move:
    CASTLING = 0

    initial_position = Board()
    rotated_initial_position = Board()
    rotated_initial_position.rotate180()

    def __init__(self, from_square: int, to_square: int, role: Role, capture: bool, promotion: Optional[Role] = None):
        self.from_square = from_square
        self.to_square = to_square
        self.role = role
        self.capture = capture
        self.promotion = promotion

class BWTime:
    def __init__(self, white_time: int, black_time: int):
        self.white_time = white_time
        self.black_time = black_time

    def rotate(self) -> 'BWTime':
        return BWTime(self.black_time, self.white_time)

class PlayedMove:
    def __init__(self, move: Move, time_info: Optional[BWTime], board: Board, via: Optional[Move]):
        self.move = move
        self.time_info = time_info
        self.board = board
        self.via = via

class Game:
    def __init__(self, moves: List[PlayedMove], result: Optional[Result]):
        self.moves = moves
        self.result = result

class MoveParser:
    class ReachablePosition:
        def __init__(self, board: Board, from_, via: Optional[Move]):
            self.board = board
            self.from_ = from_
            self.via = via
            self.time_info = None

    def __init__(self, game_callback):
        self.game_callback = game_callback
        self.board_state = None
        self.positions = {}
        self.seen_initial_position = False
        self.rotate = False
        self.last_reachable = None

    def reset_state(self):
        self.positions = {}
        self.seen_initial_position = False
        self.rotate = False
        self.last_reachable = None

    def got_message(self, msg):
        if isinstance(msg, BoardDump):
            self.handle_update(msg.board)
        elif isinstance(msg, FieldUpdate):
            update = msg
            if self.board_state is None:
                raise ValueError("Got FieldUpdate message before initial BoardDump.")
            new_state = Board(self.board_state)
            square = update.square ^ 63 if self.rotate else update.square
            if update.role is None:
                if new_state.role_at(square) is None:
                    raise ValueError("Piece removed from empty square.")
                new_state.discard(square)
            else:
                new_state.put(square, update.color, update.role)
            self.handle_update(new_state)
        elif isinstance(msg, BWTime):
            if self.last_reachable is not None:
                if self.rotate:
                    msg = msg.rotate()
                self.last_reachable.time_info = msg

    def handle_update(self, new_state):
        self.board_state = new_state
        if not self.seen_initial_position:
            self.pre_initial_position()
        else:
            self.handle_normal_update()

    def pre_initial_position(self):
        if self.board_state.equal_setup(self.initial_position):
            self.seen_initial_position = True
            self.last_reachable = self.ReachablePosition(self.initial_position, None, None)
            self.positions[self.last_reachable] = self.last_reachable
            self.add_reachable_positions(self.last_reachable, self.positions)
        elif self.board_state.equal_setup(self.rotated_initial_position):
            self.seen_initial_position = True
            self.last_reachable = self.ReachablePosition(self.initial_position, None, None)
            self.positions[self.last_reachable] = self.last_reachable
            self.add_reachable_positions(self.last_reachable, self.positions)
            self.board_state.rotate180()
            self.rotate = True

    def handle_normal_update(self):
        p = self.ReachablePosition(self.board_state, None, None)
        reachable = self.positions.get(p)
        if reachable is not None:
            self.add_reachable_positions(reachable, self.positions)
            self.last_reachable = reachable
        else:
            result = self.board_state.result_signal()
            if result is not None:
                self.game_callback(self.current_game(result))
                self.reset_state()

    def end_game(self):
        if self.last_reachable is not None:
            self.game_callback(self.current_game(None))
            self.reset_state()

    def current_game(self, result):
        if self.last_reachable is None:
            return Game([], None)
        moves = []
        for reachable in self.last_reachable:
            moves.insert(0, PlayedMove(
                self.move_to_san(reachable),
                reachable.time_info,
                reachable.board,
                reachable.via
            ))
        return Game(moves, result)

    def board_state(self):
        return Board(self.board_state)
    
    ranks = ["1", "2", "3", "4", "5", "6", "7", "8"]
    files = ["a", "b", "c", "d", "e", "f", "g", "h"]

    @staticmethod
    def move_to_san(r):
        sb = ''
        
        if r.via.type == Move.CASTLING:
            sb += "O-O" if Square.file(r.via.to) == 7 else "O-O-O"
        else:
            if r.via.role == Role.PAWN:
                if r.via.capture:
                    sb += MoveParser.files[Square.file(r.via.from_)]
            else:
                sb.append(r.via.role.symbol)
                moves = MoveList()
                r.from_.board.legal_moves(moves)
                rank = False
                file = False
                for m in moves:
                    if m.to != r.via.to or m.role != r.via.role or m.promotion != r.via.promotion or m.from_ == r.via.from_:
                        continue
                    if Square.rank(m.from_) == Square.rank(r.via.from_) or Square.file(m.from_) != Square.file(r.via.from_):
                        file = True
                    else:
                        rank = True
                if file:
                    sb.append(MoveParser.files[Square.file(r.via.from_)])
                if rank:
                    sb.append(MoveParser.ranks[Square.rank(r.via.from_)])
            if r.via.capture:
                sb.append('x')
            sb.append(MoveParser.square_string(r.via.to))
        if r.board.is_check():
            moves = MoveList()
            r.board.legal_moves(moves)
            if len(moves) > 0:
                sb.append('+')
            else:
                sb.append('#')
        return ''.join(sb)

    @staticmethod
    def square_string(square):
        return MoveParser.files[Square.file(square)] + MoveParser.ranks[Square.rank(square)]

    @staticmethod
    def add_reachable_positions(from_, positions):
        moves = MoveList()
        from_.board.legal_moves(moves)
        for m in moves:
            new_board = Board(from_.board)
            new_board.play(m)
            reachable = MoveParser.ReachablePosition(new_board, from_, m)
            positions[reachable] = reachable



