import os, time
import pyautogui

from dgt_constants import DgtConstants

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
    match piece_byte:
        case DgtConstants.EMPTY:
            return ''
        case DgtConstants.WPAWN:
            return 'P'
        case DgtConstants.WROOK:
            return 'R'
        case DgtConstants.WKNIGHT:
            return 'N'
        case DgtConstants.WBISHOP:
            return 'B'
        case DgtConstants.WKING:
            return 'K'
        case DgtConstants.WQUEEN:
            return 'Q'
        case DgtConstants.BPAWN:
            return 'p'
        case DgtConstants.BROOK:
            return 'r'
        case DgtConstants.BKNIGHT:
            return 'n'
        case DgtConstants.BBISHOP:
            return 'b'
        case DgtConstants.BKING:
            return 'k'
        case DgtConstants.BQUEEN:
            return 'q'
        case _:
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
        c = ser.read(1)
        s += c
        bytes_read += 1
    return s

def get_dgt_board_state(ser):
    request_board_state(ser)
    time.sleep(0.3)
    return receive_board_message(ser)

def get_piece_on_browser_square(driver, file, rank):
    selector = '.piece.square-' + file + rank
    try:
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        pieceStr = elem.get_attribute('class')[6:8]
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
        match move.lower()[4]:
            case 'q':
                pass
            case 'n':
                move_val += square_width
            case 'r':
                move_val += 2 * square_width
                pass
            case 'b':
                move_val += 3 * square_width
                pass
            case _:
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
        match move.lower()[4]:
            case 'q':
                pass
            case 'n':
                move_val += self.square_width
            case 'r':
                move_val += 2 * self.square_width
                pass
            case 'b':
                move_val += 3 * self.square_width
                pass
            case _:
                raise ValueError("invalid uci move")
            
        pyautogui.moveTo(end_x, end_y + move_val, 0.1)
        pyautogui.leftClick()
