import os, time, enum, datetime
from square import *
import chess
import pyautogui

from dgt_constants import *

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

def move_cursor(y, x):
    print("\033[%d;%dH" % (y, x))

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def print_board(board):
    move_cursor(0, 0)
    print(board)

def piece_byte_to_ascii(piece_byte):
    if piece_byte == DgtConstants.EMPTY:
        return ''
    elif piece_byte == DgtConstants.WPAWN:
        return 'P'
    elif piece_byte == DgtConstants.WROOK:
        return 'R'
    elif piece_byte == DgtConstants.WKNIGHT:
        return 'N'
    elif piece_byte == DgtConstants.WBISHOP:
        return 'B'
    elif piece_byte == DgtConstants.WKING:
        return 'K'
    elif piece_byte == DgtConstants.WQUEEN:
        return 'Q'
    elif piece_byte == DgtConstants.BPAWN:
        return 'p'
    elif piece_byte == DgtConstants.BROOK:
        return 'r'
    elif piece_byte == DgtConstants.BKNIGHT:
        return 'n'
    elif piece_byte == DgtConstants.BBISHOP:
        return 'b'
    elif piece_byte == DgtConstants.BKING:
        return 'k'
    elif piece_byte == DgtConstants.BQUEEN:
        return 'q'
    else:
        raise ValueError("Invalid piece detected")

def dgt_message_to_fen(message):
    stripped_message = message[3:]
    if(len(stripped_message) != 64):
        print("Invalid board state message")
        return ''
    
    result = ''
    empty_count = 0
    for rev_rank in range(0, 8):
        rank = 7 - rev_rank
        if empty_count > 0:
            result += str(empty_count)
        if rev_rank != 0:
            result += '/'
        empty_count = 0
        for rev_file in range(0, 8):
            file = 7 - rev_file
            message_index = (rank * 8) + file
            piece = piece_byte_to_ascii(stripped_message[message_index])
            if len(piece) == 0:
                empty_count += 1
            elif empty_count > 0:
                result += str(empty_count)
                empty_count = 0
            result += piece

    if empty_count > 0:
        result += str(empty_count)
            
    return result

def fen_from_board(board):
    fen = board.fen()
    return fen[:fen.find(' ')]

def is_white_to_move(board):
    fen = board.fen()
    return fen[fen.index(' ')+1:][0] == 'w'

def legal_fens(board):
    legal_moves = list(board.legal_moves)
    result = {}
    for legal_move in legal_moves:
        legal_move_uci = legal_move.uci()
        board.push_uci(legal_move_uci)
        fen = fen_from_board(board)
        board.pop()
        result[fen] = legal_move_uci
    return result

def previous_fen_from_history(fen_history):
    history_len = len(fen_history)
    if history_len > 0:
        return fen_history[history_len-1]
    return ''

def request_board_state(ser):
    ser.write(bytes([DgtConstants.DGT_SEND_BRD]))

def board_reset(ser):
    ser.write(bytes([DgtConstants.DGT_SEND_RESET]))

def request_board_ee_moves(ser):
    ser.write(bytes([DgtConstants.DGT_SEND_EE_MOVES]))

def receive_board_message(ser):
    s = b''
    bytes_read = 0
    while(ser.in_waiting > 0):
        waiting = ser.in_waiting
        c = ser.read(waiting)
        s += c
        bytes_read += waiting
    return s

def get_dgt_board_state(ser):
    request_board_state(ser)
    time.sleep(0.3)
    return receive_board_message(ser)

def get_piece_on_browser_square(driver, file, rank):
    selector = '.piece.square-' + file + rank
    try:
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        classSplit = elem.get_attribute('class').split(' ')
        pieceStr = ''
        for item in classSplit:
            if len(item) == 2 and (item[0] == 'w' or item[0] == 'b'):
                pieceStr = item
                break
        if(pieceStr[0] == 'w'):
            return pieceStr[1].upper()
        else:
            return pieceStr[1]
    except NoSuchElementException:
        return ''

def get_fen_from_browser(driver):
    result = ''
    coords = ['8', '7', '6', '5', '4', '3', '2', '1']
    empty_count = 0

    for rank in coords:
        if empty_count > 0:
            result += str(empty_count)
        if rank != '8':
            result += '/'
        empty_count = 0
        for file in reversed(coords):
            piece = get_piece_on_browser_square(driver, file, rank)
            if len(piece) == 0:
                empty_count += 1
            elif empty_count > 0:
                result += str(empty_count)
                empty_count = 0
            result += piece

    if empty_count > 0:
        result += str(empty_count)

    return result


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
    message = bytes()
    in_message = receive_board_message(ser)
    while len(in_message) > 0:
        message += in_message
        time.sleep(3)
        in_message = receive_board_message(ser)

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
            i += 2
        else:
            i += 1

    return events

def get_ee_game(events, start_move_index):
    event = None
    move_index = start_move_index
    game = chess.Board()
    
    physical_state = chess.Board()
    legal_moves = legal_fens(game)
    while type(event) is not SimpleEvent or (event.type != Event.EE_BEGINPOS and event.type != Event.EE_BEGINPOS_ROT and event.type != Event.EE_EOF):
        if move_index < 0 or move_index >= len(events):
            break
        
        event = events[move_index]

        if type(event) is not FieldEvent:
            move_index += 1
            continue

        square = chess.square(7 - event.file, event.rank)
        if event.piece == Piece.EMPTY:
            physical_state.remove_piece_at(square)
        elif event.piece == Piece.WPAWN:
            physical_state.set_piece_at(square, chess.Piece(chess.PAWN, chess.WHITE))
        elif event.piece == Piece.WROOK:
            physical_state.set_piece_at(square, chess.Piece(chess.ROOK, chess.WHITE))
        elif event.piece == Piece.WKNIGHT:
            physical_state.set_piece_at(square, chess.Piece(chess.KNIGHT, chess.WHITE))
        elif event.piece == Piece.WBISHOP:
            physical_state.set_piece_at(square, chess.Piece(chess.BISHOP, chess.WHITE))
        elif event.piece == Piece.WKING:
            physical_state.set_piece_at(square, chess.Piece(chess.KING, chess.WHITE))
        elif event.piece == Piece.WQUEEN:
            physical_state.set_piece_at(square, chess.Piece(chess.QUEEN, chess.WHITE))
        elif event.piece == Piece.BPAWN:
            physical_state.set_piece_at(square, chess.Piece(chess.PAWN, chess.BLACK))
        elif event.piece == Piece.BROOK:
            physical_state.set_piece_at(square, chess.Piece(chess.ROOK, chess.BLACK))
        elif event.piece == Piece.BKNIGHT:
            physical_state.set_piece_at(square, chess.Piece(chess.KNIGHT, chess.BLACK))
        elif event.piece == Piece.BBISHOP:
            physical_state.set_piece_at(square, chess.Piece(chess.BISHOP, chess.BLACK))
        elif event.piece == Piece.BKING:
            physical_state.set_piece_at(square, chess.Piece(chess.KING, chess.BLACK))
        elif event.piece == Piece.BQUEEN:
            physical_state.set_piece_at(square, chess.Piece(chess.QUEEN, chess.BLACK))
        else:
            pass

        physical_fen = fen_from_board(physical_state)
        if physical_fen in legal_moves:
            move = legal_moves[physical_fen]
            game.push_uci(move)
            legal_moves = legal_fens(game)

        move_index += 1
    return game

def get_ee_games(events):
    # wait for first starting position message
    start_move_index = 0
    games = []
    for event in events:
        start_move_index += 1
        if type(event) is not SimpleEvent or (event.type != Event.EE_BEGINPOS and event.type != Event.EE_BEGINPOS_ROT):
            continue

        games.append(get_ee_game(events, start_move_index))
    return games

ranks_black = ['1', '2', '3', '4', '5', '6', '7', '8']
files_white = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
ranks_white = ranks_black[::-1]
files_black = files_white[::-1]

def make_uci_move(driver, move, is_white):
    if len(move) != 4 and len(move) != 5:
        raise ValueError("invalid uci move")
    
    ranks = ranks_black
    files = files_white
    
    diff_multiplier = 1
    if not is_white:
        diff_multiplier = -1
    start_file_index = files.index(move[0])
    start_rank_index = ranks.index(move[1])
    end_file_index = files.index(move[2])
    end_rank_index = ranks.index(move[3])

    selector = ".square-" + str(start_file_index + 1) + str(start_rank_index + 1)
    elem = driver.find_element(By.CSS_SELECTOR, selector)
    
    square_width = elem.size['width']
    move_offset_x = (end_file_index - start_file_index) * square_width * diff_multiplier
    move_offset_y = (start_rank_index - end_rank_index) * square_width * diff_multiplier

    ac = ActionChains(driver)
    ac.move_to_element(elem).click_and_hold().move_by_offset(move_offset_x, move_offset_y).release()

    if(len(move) == 5):
        move_val = 0
        promotion_piece = move.lower()[4]
        if promotion_piece == 'q':
            pass
        elif promotion_piece == 'n':
            move_val -= square_width
        elif promotion_piece == 'r':
            move_val -= 2 * square_width
            pass
        elif promotion_piece == 'b':
            move_val -= 3 * square_width
            pass
        else:
            raise ValueError("invalid uci move")
        ac = ac.move_by_offset(0, -move_val).click()

    ac.perform()

class AutoScreen:
    def __init__(self):
        self.top_left_x = 236
        self.top_left_y = 187
        self.board_width = 784
        self.square_width = self.board_width / 8
        self.half_square_width = self.square_width / 2
        self.top_left_square_x = self.top_left_x + self.half_square_width
        self.top_left_square_y = self.top_left_y + self.half_square_width

    def __init__(self, screen_x, screen_y):
        self.top_left_x = screen_x
        self.top_left_y = screen_y
        self.board_width = 784
        self.square_width = self.board_width / 8
        self.half_square_width = self.square_width / 2
        self.top_left_square_x = self.top_left_x + self.half_square_width
        self.top_left_square_y = self.top_left_y + self.half_square_width

    def __init__(self, screen_x, screen_y, square_width):
        self.top_left_x = screen_x
        self.top_left_y = screen_y
        self.square_width = square_width
        self.board_width = square_width * 8
        self.half_square_width = self.square_width / 2
        self.top_left_square_x = self.top_left_x + self.half_square_width
        self.top_left_square_y = self.top_left_y + self.half_square_width

    def get_rank_coord(self, rank, is_white):
        ranks = ranks_white
        if not is_white:
            ranks = ranks_black
    
        return self.top_left_square_y + (ranks.index(rank) * self.square_width)
    
    def get_file_coord(self, file, is_white):
        files = files_white
        if not is_white:
            files = files_black
    
        return self.top_left_square_x + (files.index(file) * self.square_width)
    
    
    def make_uci_move(self, move, is_white):
        if len(move) != 4 and len(move) != 5:
            raise ValueError("invalid uci move")
        
        start_x = self.get_file_coord(move[0], is_white)
        start_y = self.get_rank_coord(move[1], is_white)
        end_x = self.get_file_coord(move[2], is_white)
        end_y = self.get_rank_coord(move[3], is_white)
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(end_x, end_y, 0.3)
        pyautogui.mouseUp(button='left')

        if(len(move) != 5):
            return
        
        move_val = 0
        promotion_piece = move.lower()[4]
        if promotion_piece == 'q':
            pass
        elif promotion_piece == 'n':
            move_val += self.square_width
        elif promotion_piece == 'r':
            move_val += 2 * self.square_width
            pass
        elif promotion_piece == 'b':
            move_val += 3 * self.square_width
            pass
        else:
            raise ValueError("invalid uci move")
            
        pyautogui.moveTo(end_x, end_y + move_val, 0.1)
        pyautogui.leftClick()
