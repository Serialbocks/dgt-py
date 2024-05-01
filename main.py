import argparse

import sys, os, time
import serial
import chess

from utils import *
from dgt_constants import *

ser = None

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Show game following chess rules from DGT board to console")
    parser.add_argument("--port", type=str, default="COM7", help="Name of serial port to connect to")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port

    ser = serial.Serial(port=port, baudrate=9600)
    board_reset(ser)
    board = chess.Board()
    legal_moves = legal_fens(board)
    fen_history = list()
    cls()
    print_board(board)
    
    while True:
        request_board_state(ser)
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