import argparse
import sys, os, time
import enum
import serial
import chess
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from utils import *
from dgt_constants import *

class GameState(enum.Enum):
    PRE_GAME = 0
    PLAYER_TURN = 1
    OPPONENT_TURN = 2
    WAIT_PLAYER_UPDATE_OPPONENT = 3

class Game():
    def __init__(self, screen_x, screen_y, port, url, fullscreen, debug=False):
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.port = port
        self.debug = debug
        self.url = url
        self.fullscreen = fullscreen
        self.init_game()

    def init_game(self):
        self.board_reset_msg_sent = False
        self.serial = serial.Serial(port=self.port, baudrate=9600)
        board_reset(self.serial)
        self.board = chess.Board()
        self.legal_moves = legal_fens(self.board)
        options = Options()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        self.driver = webdriver.Chrome(options)
        self.driver.get(self.url)

        # maximize to full screen and check for board
        self.driver.maximize_window()
        body = self.driver.find_element(By.CSS_SELECTOR, "body")
        if self.fullscreen:
            self.driver.fullscreen_window()
        body.send_keys(Keys.CONTROL + Keys.HOME)

        self.state = GameState.PRE_GAME

    def debug_print(self, text):
        if self.debug:
            print(text)

    def close(self):
        if self.serial.is_open:
            self.serial.close()

    def get_board_state(self):
        request_board_state(self.serial)
        time.sleep(0.3)
        s = b''
        bytes_read = 0
        while(self.serial.in_waiting > 0):
            c = self.serial.read(1)
            s += c
            bytes_read += 1
        return s
    
    def state_pre_game(self):
        s = self.get_board_state()
        fen = dgt_message_to_fen(s)
        if fen != STARTING_FEN:
            if not self.board_reset_msg_sent:
                self.board_reset_msg_sent = True
                print('Waiting for board to be reset...')
            return
        self.is_white = True
        color_in = input("Enter color to begin (W/b): ")
        if len(color_in) > 0 and color_in[0].lower() == 'b':
            self.is_white = False

        # check board location and dimensions for auto screen
        selector = ".square-18"
        if not self.is_white:
            selector = ".square-81"
        e = self.driver.find_element(By.CSS_SELECTOR, selector)
        self.debug_print(e.location)
        self.auto_screen = AutoScreen(e.location['x'] + self.screen_x, e.location['y'] + self.screen_y, e.size['width'])

        if self.is_white:
            self.state = GameState.PLAYER_TURN
        else:
            self.state = GameState.OPPONENT_TURN
        

    def state_player_turn(self):
        s = self.get_board_state()
        fen = dgt_message_to_fen(s)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.auto_screen.make_uci_move(move, self.is_white)
            self.state = GameState.OPPONENT_TURN
            if(self.board.is_checkmate()):
                self.state = GameState.PRE_GAME

    def state_opponent_turn(self):
        fen = get_fen_from_browser(self.driver)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.state = GameState.WAIT_PLAYER_UPDATE_OPPONENT
            if(self.board.is_checkmate()):
                self.state = GameState.PRE_GAME
        
    def state_wait_player_update_opponent(self):
        s = self.get_board_state()
        board_fen = dgt_message_to_fen(s)
        game_fen = fen_from_board(self.board)
        if board_fen == game_fen:
            self.state = GameState.PLAYER_TURN

    def run(self):
        match self.state:
            case GameState.PRE_GAME:
                self.state_pre_game()
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
    parser.add_argument("--port", type=str, default="COM10", help="Name of serial port to connect to")
    parser.add_argument("--screen_x", type=int, default=0, help="Horizontal screen offset")
    parser.add_argument("--screen_y", type=int, default=0, help="Vertical screen offset")
    parser.add_argument("--url", type=str, default="https://www.chess.com/play/computer", help="Starting URL")
    parser.add_argument('--fullscreen', action=argparse.BooleanOptionalAction, help="Automatically set browser window to fullscreen")
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, help="Print debug text to console")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    screen_x = args.screen_x
    screen_y = args.screen_y
    debug = args.debug
    url = args.url
    fullscreen = args.fullscreen
    game = Game(screen_x, screen_y, port, url, fullscreen, debug)
    
    previous_state = GameState.OPPONENT_TURN
    while True:
        game.run()
        time.sleep(0.033) # ~30fps
        if game.state != previous_state:
            game.debug_print(game.state)
            previous_state = game.state

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