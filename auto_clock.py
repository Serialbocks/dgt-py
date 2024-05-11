import sys, os, glob, subprocess, time
import serial
import chess
from datetime import timedelta

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
        self.white_time_expired = False
        self.black_time_expired = False
        self.increment_ms = increment_ms
        self.board = chess.Board()
        self.running = False

        self.serial = serial.Serial(port=self.port, baudrate=9600)

        self.board_fen = dgt_message_to_fen(get_dgt_board_state(self.serial))
        self.legal_moves = legal_fens(self.board)
        self.white_to_move = True

    def ms_to_hh_mm_ss(self, ms):
        td_str = str(timedelta(milliseconds=ms))
        result = ''

        td_split = td_str.split(":")
        hours = td_split[0]
        minutes = td_split[1]
        seconds = td_split[2]

        has_hours = len(hours) > 1 or hours[0] != '0'
        if has_hours:
            result += hours + ":"
        
        if(has_hours or minutes[0] != '0'):
            result += minutes + ":"
        else:
            result += minutes[1] + ":"

        result += seconds[0:2]

        return result


    def run_clock(self):
        current_time = current_milli_time()
        if self.board_fen in self.legal_moves:
            if not self.running:
                self.white_start_time = current_time
                self.black_start_time = current_time

            move = self.legal_moves[self.board_fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.white_to_move = not self.white_to_move
            if self.white_to_move:
                self.black_time -= (current_time - self.black_start_time)
                self.black_time += self.increment_ms
                self.white_start_time = current_time
            else:
                self.white_time -= (current_time - self.white_start_time)
                if self.running:
                    self.white_time += self.increment_ms
                self.black_start_time = current_time

            self.running = True

        white_time = self.white_time
        black_time = self.black_time

        if self.running:
            if self.white_to_move:
                white_time -= (current_time - self.white_start_time)
            else:
                black_time -= (current_time - self.black_start_time)

        if(white_time <= 0):
            white_time = 0
            self.white_time = 0
            self.running = False
            self.white_time_expired = True
        if(black_time <= 0):
            black_time = 0
            self.black_time = 0
            self.running = False
            self.black_time_expired = True

        return {
            "white": self.ms_to_hh_mm_ss(white_time),
            "black": self.ms_to_hh_mm_ss(black_time),
            "running": self.running,
            "white_to_move": self.white_to_move,
            "white_time_expired": self.white_time_expired,
            "black_time_expired": self.black_time_expired
        }

    def run_board(self):
        s = get_dgt_board_state(self.serial)
        fen = dgt_message_to_fen(s)
        self.board_fen = fen

    def start_pause_timer(self):
        current_time = current_milli_time()
        if self.running:
            if self.white_to_move:
                self.white_time -= (current_time - self.white_start_time)
            else:
                self.black_time -= (current_time - self.black_start_time)
        else:
            self.white_start_time = current_time
            self.black_start_time = current_time

        self.running = not self.running
        