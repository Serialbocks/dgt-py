import sys, os, glob, subprocess, time
import serial
import chess

from utils import *
from dgt_constants import *

def current_milli_time():
    return round(time.time() * 1000)

class AutoClock():
    def __init__(self, port, start_time_ms, increment_ms):
        self.port = port
        self.white_time = start_time_ms
        self.black_time = start_time_ms
        self.white_start_time = None
        self.black_start_time = None
        self.increment_ms = increment_ms
        self.board = chess.Board()
        self.running = False

        self.serial = serial.Serial(port=self.port, baudrate=9600)

        self.board_fen = dgt_message_to_fen(get_dgt_board_state(self.serial))
        self.legal_moves = legal_fens(self.board)
        self.white_to_move = True

    def run_clock(self):
        if self.board_fen in self.legal_moves:
            current_time = current_milli_time()

            if not self.running:
                self.black_start_time = current_time

            move = self.legal_moves[self.board_fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.white_to_move = ~self.white_to_move
            if self.white_to_move:
                self.black_time -= (self.current_time - self.black_start_time)
                self.white_start_time = current_time
            else:
                self.white_time -= (self.current_time - self.white_start_time)
                self.black_start_time = current_time

            self.running = True

        white_time = self.white_time
        black_time = self.black_time
        if self.running:
            pass

        return {
            "white": "",
            "black": ""
        }

    def run_board(self):
        self.board_fen = dgt_message_to_fen(get_dgt_board_state(self.serial))
        