import argparse
import sys, os, time
import enum
import serial # type: ignore
import chess # type: ignore
from selenium import webdriver # type: ignore

from utils import *
from dgt_constants import *

class GameState(enum.Enum):
    PLAYER_TURN = 1
    OPPONENT_TURN = 2
    WAIT_PLAYER_UPDATE_OPPONENT = 3

class Game():
    def __init__(self, port):
        self.state = GameState.PLAYER_TURN
        self.is_white = True
        self.auto_screen = AutoScreen()
        self.port = port
        self.init_game()

    def __init__(self, color, screen_x, screen_y, port):
        self.auto_screen = AutoScreen(color, screen_x, screen_y)
        self.is_white = (color == 'white')
        self.state = GameState.PLAYER_TURN
        self.port = port
        if not self.is_white:
            self.state = GameState.OPPONENT_TURN
        self.init_game()

    def init_game(self):
        self.serial = serial.Serial(port=self.port, baudrate=9600)
        board_reset(self.serial)
        self.board = chess.Board()
        self.legal_moves = legal_fens(self.board)
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.chess.com/analysis")

    def close(self):
        if self.serial.is_open:
            self.serial.close()

    def get_board_state(self):
        request_board_state(self.serial)
        time.sleep(0.1)
        s = b''
        bytes_read = 0
        while(self.serial.in_waiting > 0):
            c = self.serial.read(1)
            s += c
            bytes_read += 1
        return s

    def state_player_turn(self):
        s = self.get_board_state()
        fen = dgt_message_to_fen(s)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.auto_screen.make_uci_move(move, self.is_white)
            self.state = GameState.OPPONENT_TURN

    def state_opponent_turn(self):
        fen = get_fen_from_browser(self.driver)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.state = GameState.WAIT_PLAYER_UPDATE_OPPONENT
        
    def state_wait_player_update_opponent(self):
        s = self.get_board_state()
        board_fen = dgt_message_to_fen(s)
        game_fen = fen_from_board(self.board)
        if board_fen == game_fen:
            self.state = GameState.PLAYER_TURN

    def run(self):
        match self.state:
            case GameState.PLAYER_TURN:
                self.state_player_turn()
            case GameState.OPPONENT_TURN:
                self.state_opponent_turn()
            case GameState.WAIT_PLAYER_UPDATE_OPPONENT:
                self.state_wait_player_update_opponent()
            case _:
                raise RuntimeError('Game got into an invalid state')

game = None

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Show game following chess rules from DGT board to console")
    parser.add_argument("--port", type=str, default="COM7", help="Name of serial port to connect to")
    parser.add_argument("--color", type=str, default="white", help="Color of the player's pieces: 'white' or 'black'")
    parser.add_argument("--screen_x", type=int, default=243, help="Horizontal screen coordinate of top left of chess board")
    parser.add_argument("--screen_y", type=int, default=206, help="Vertical screen coordinate of top left of chess board")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    color = args.color
    screen_x = args.screen_x
    screen_y = args.screen_y
    game = Game(color, screen_x, screen_y, port)
    
    while True:
        game.run()
        time.sleep(0.033) # ~30fps
        print(game.state)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        if game is not None:
            game.close()
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)