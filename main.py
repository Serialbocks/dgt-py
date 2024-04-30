import sys, os, time
import serial # type: ignore
import chess # type: ignore

from utils import *
from dgt_constants import *

ser = None

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