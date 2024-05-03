import argparse
import sys, os, time, datetime
import enum
import serial
import chess
from utils import *
from square import *

class Event(enum.Enum):
    EE_POWERUP = 0x6a
    EE_EOF = 0x6b
    EE_FOURROWS = 0x6c
    EE_EMPTYBOARD = 0x6d
    EE_DOWNLOADED = 0x6e
    EE_BEGINPOS = 0x6f
    EE_BEGINPOS_ROT = 0x7a
    EE_START_TAG = 0x7b
    EE_WATCHDOG_ACTION = 0x7c
    EE_FUTURE_1 = 0x7d
    EE_FUTURE_2 = 0x7e
    EE_NOP = 0x7f
    EE_NOP2 = 0x00

class Piece(enum.Enum):
    EMPTY = 0x00  # Empty square.
    WPAWN = 0x01  # White pawn.
    WROOK = 0x02  # White rook.
    WKNIGHT = 0x03  # White knight.
    WBISHOP = 0x04  # White bishop.
    WKING = 0x05  # White king.
    WQUEEN = 0x06  # White queen.
    BPAWN = 0x07  # Black pawn.
    BROOK = 0x08  # Black rook.
    BKNIGHT = 0x09  # Black knight.
    BBISHOP = 0x0a  # Black bishop.
    BKING = 0x0b  # Black king.
    BQUEEN = 0x0c  # Black queen.
    PIECE1 = 0x0d  # Special piece to signal draw.
    PIECE2 = 0x0e  # Special piece to signal white win.
    PIECE3 = 0x0f  # Special piece to signal black win.

class SimpleEvent:
    def __init__(self, type):
        self.type = Event(type)
        
    def __str__(self):
        return 'simple event | type: ' + str(self.type)

class FieldEvent:
    def __init__(self, piece, field):
        self.square = field
        self.rank = Square.rank(field)
        self.file = Square.file(field)
        self.role = piece
        self.piece = Piece(piece)

    def __str__(self):
        return 'field event | piece: ' + str(self.piece) + ' rank: ' + str(self.rank) + ' file: ' + str(self.file)

class ClockEvent:
    def __init__(self, isLeft, hours, minutes, seconds):
        self.isLeft = isLeft
        self.time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def __str__(self):
        return 'clock event | is_left: ' + str(self.isLeft) + ' ' + str(self.time)

def get_ee_events(ser):
    request_board_ee_moves(ser)
    time.sleep(3)
    message = receive_board_message(ser)

    events = []
    i = 0
    while i < len(message):
        value = message[i]
        if (0x6a <= value <= 0x6f) or (0x7a <= value <= 0x7f) or value == 0x00:
            simple_event = SimpleEvent(value)
            events.append(simple_event)

            i += 1
        elif 0x40 <= value <= 0x5f:
            if i + 1 >= len(message):
                break

            field_event = FieldEvent(value & 0x0f, message[i+1])
            events.append(field_event)

            i += 2
        elif (0x60 <= value <= 0x69) or (0x70 <= value <= 0x79):
            if i + 2 >= len(message):
                break
            clock_event = ClockEvent((value & 0x10) == 0x10, value & 0x0f, message[i+1], message[i+2])
            events.append(clock_event)

        else:
            i += 1
    
    return events

def save_game(events, folder, game_index, start_move_index):
    filename = folder + str(game_index) + '.game'
    with open(filename, 'w') as file:
        event = None
        move_index = start_move_index
        game = chess.Board()
        physical_state = chess.Board()
        legal_moves = legal_fens(game)
        while type(event) is not SimpleEvent or (event.type != Event.EE_BEGINPOS and event.type != Event.EE_BEGINPOS_ROT and event.type != Event.EE_EOF):
            event = events[move_index]

            if type(event) is not FieldEvent:
                move_index += 1
                continue

            square = chess.square(7 - event.file, event.rank)
            match(event.piece):
                case Piece.EMPTY:
                    physical_state.remove_piece_at(square)
                case Piece.WPAWN:
                    physical_state.set_piece_at(square, chess.Piece(chess.PAWN, chess.WHITE))
                case Piece.WROOK:
                    physical_state.set_piece_at(square, chess.Piece(chess.ROOK, chess.WHITE))
                case Piece.WKNIGHT:
                    physical_state.set_piece_at(square, chess.Piece(chess.KNIGHT, chess.WHITE))
                case Piece.WBISHOP:
                    physical_state.set_piece_at(square, chess.Piece(chess.BISHOP, chess.WHITE))
                case Piece.WKING:
                    physical_state.set_piece_at(square, chess.Piece(chess.KING, chess.WHITE))
                case Piece.WQUEEN:
                    physical_state.set_piece_at(square, chess.Piece(chess.QUEEN, chess.WHITE))
                case Piece.BPAWN:
                    physical_state.set_piece_at(square, chess.Piece(chess.PAWN, chess.BLACK))
                case Piece.BROOK:
                    physical_state.set_piece_at(square, chess.Piece(chess.ROOK, chess.BLACK))
                case Piece.BKNIGHT:
                    physical_state.set_piece_at(square, chess.Piece(chess.KNIGHT, chess.BLACK))
                case Piece.BBISHOP:
                    physical_state.set_piece_at(square, chess.Piece(chess.BISHOP, chess.BLACK))
                case Piece.BKING:
                    physical_state.set_piece_at(square, chess.Piece(chess.KING, chess.BLACK))
                case Piece.BQUEEN:
                    physical_state.set_piece_at(square, chess.Piece(chess.QUEEN, chess.BLACK))
                case _:
                    pass

            physical_fen = fen_from_board(physical_state)
            if physical_fen in legal_moves:
                move = legal_moves[physical_fen]
                file.write(move + '\n')
                game.push_uci(move)
                legal_moves = legal_fens(game)

            move_index += 1

        file.write(game.fen())

def save_games(events):
    print('saving games...')
    folder = time.strftime("logs/%Y-%m-%d_%H.%M.%S/")
    os.makedirs(folder)

    # wait for first starting position message
    game_index = 0
    start_move_index = 0
    for event in events:
        start_move_index += 1
        if type(event) is not SimpleEvent or (event.type != Event.EE_BEGINPOS and event.type != Event.EE_BEGINPOS_ROT):
            continue

        game_index += 1
        save_game(events, folder, game_index, start_move_index)
    print('saved ' + str(game_index) + ' games to ' + folder)

def print_events(events):
    for event in events:
        print(event)

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Test pulling games off board EEPROM")
    parser.add_argument("--port", type=str, default="COM9", help="Name of serial port to connect to")
    parser.add_argument('--save', action=argparse.BooleanOptionalAction, help="Save games to files")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    save = args.save
    ser = serial.Serial(port=port, baudrate=9600)
    time.sleep(0.1)
    board_reset(ser)
    time.sleep(0.1)
    events = get_ee_events(ser)

    if save:
        save_games(events)
    else:
        print_events(events)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)