import sys, os, time
import serial # type: ignore
import chess # type: ignore

from dgt_constants import DgtConstants

ser = None

STARTING_FEN ='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'

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
        raise ValueError("Invalid board state message")
    
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

def main():
    ser = serial.Serial(port='COM7', baudrate=9600)
    ser.write(bytes([DgtConstants.DGT_SEND_RESET]))
    board = chess.Board()
    legal_moves = legal_fens(board)
    fen_history = list()
    cls()
    print_board(board)
    
    while True:
        ser.write(bytes([DgtConstants.DGT_SEND_BRD]))
        time.sleep(0.1)
        s = b''
        bytes_read = 0
        while(ser.in_waiting > 0):
            c = ser.read(1)
            s += c
            bytes_read += 1

        fen = dgt_message_to_fen(s)
        previous_fen = previous_fen_from_history(fen_history)
        if fen == STARTING_FEN and previous_fen != '':
            board = chess.Board()
            legal_moves = legal_fens(board)
            fen_history = list()
            print_board(board)
        elif previous_fen == fen:
            board.pop()
            fen_history.pop()
            legal_moves = legal_fens(board)
            print_board(board)
        elif fen in legal_moves:
            move = legal_moves[fen]
            fen_history.append(fen_from_board(board))
            board.push_uci(move)
            legal_moves = legal_fens(board)
            print_board(board)

        

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        if ser is not None and ser.is_open:
            ser.close()
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)