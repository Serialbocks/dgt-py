import argparse
import sys, os, time, logging
import enum
import serial
import traceback
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
    def __init__(self, port, url, fullscreen, starting_fen, debug=False):
        self.port = port
        self.debug = debug
        self.url = url
        self.fullscreen = fullscreen
        self.starting_fen = starting_fen
        self.init_game()

    def __str__(self):
        result = ''

        result += 'Game State: ' + str(self.state)
        result += '\nGame Fen: '
        result += self.board.fen()

        try:
            browser_fen = get_fen_from_browser(self.driver)
            result += '\nBrowser Fen: ' + browser_fen
        except Exception:
            pass

        try:
            dgt_fen = get_dgt_board_state(self.serial)
            result += '\nDGT Fen: ' + dgt_fen
        except Exception:
            pass

        return result

    def init_game(self):
        filename = time.strftime("logs/%Y-%m-%d_%H.%M.%S.log")
        logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG)

        self.board_reset_msg_sent = False
        self.serial = serial.Serial(port=self.port, baudrate=9600)
        self.reset_game(self.starting_fen)
        options = Options()
        options.headless = True
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        self.driver = webdriver.Chrome(options)
        self.driver.get(self.url)

        # maximize to full screen and check for board
        self.driver.maximize_window()
        body = self.driver.find_element(By.CSS_SELECTOR, "body")
        if self.fullscreen:
            self.driver.fullscreen_window()
        body.send_keys(Keys.CONTROL + Keys.HOME)

        self.set_state(GameState.PRE_GAME)

    def reset_game(self, starting_fen):
        board_reset(self.serial)
        self.board = chess.Board(starting_fen)
        self.legal_moves = legal_fens(self.board)
        self.state = self.set_state(GameState.PRE_GAME)

    def debug_print(self, text):
        self.logged_this_state = True
        logging.debug(text)
        if self.debug:
            print(text)

    def close(self):
        if self.serial.is_open:
            self.serial.close()

    def set_state(self, state):
        self.logged_this_state = False
        self.state = state
        self.debug_print(self.state)
        self.logged_this_state = False
    
    def state_pre_game(self):
        s = get_dgt_board_state(self.serial)
        fen = dgt_message_to_fen(s)
        game_fen = fen_from_board(self.board)
        if not self.logged_this_state:
            self.debug_print("DGT FEN: " + fen)
        if fen != game_fen:
            if not self.board_reset_msg_sent:
                self.board_reset_msg_sent = True
                print('Waiting for board to be reset...')
            return
        self.is_white = True
        color_in = input("Enter color to begin (W/b): ")
        if len(color_in) > 0 and color_in[0].lower() == 'b':
            self.is_white = False


        if is_white_to_move(self.board) == self.is_white:
            self.set_state(GameState.PLAYER_TURN)
        else:
            self.set_state(GameState.OPPONENT_TURN)
        

    def state_player_turn(self):
        s = get_dgt_board_state(self.serial)
        fen = dgt_message_to_fen(s)
        if not self.logged_this_state:
            self.debug_print("DGT FEN: " + fen)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            make_uci_move(self.driver, move, self.is_white)
            self.set_state(GameState.OPPONENT_TURN)
            if(self.board.is_checkmate()):
                self.reset_game(STARTING_FEN)

    def state_opponent_turn(self):
        fen = get_fen_from_browser(self.driver)
        if not self.logged_this_state:
            self.debug_print("Browser FEN: " + fen)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.board.push_uci(move)
            self.legal_moves = legal_fens(self.board)
            self.set_state(GameState.WAIT_PLAYER_UPDATE_OPPONENT)
            if(self.board.is_checkmate()):
                self.reset_game(STARTING_FEN)
        
    def state_wait_player_update_opponent(self):
        s = get_dgt_board_state(self.serial)
        board_fen = dgt_message_to_fen(s)
        game_fen = fen_from_board(self.board)
        if not self.logged_this_state:
            self.debug_print("DGT FEN: " + board_fen)
            self.debug_print("Internal State FEN: " + game_fen)
            
        if board_fen == game_fen:
            self.set_state(GameState.PLAYER_TURN)

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
    parser = argparse.ArgumentParser(for_name, description="Play game on chess.com in browser")
    parser.add_argument("--port", type=str, default="COM10", help="Name of serial port to connect to")
    parser.add_argument("--url", type=str, default="https://www.chess.com/play/computer", help="Starting URL")
    parser.add_argument("--fen", type=str, default=STARTING_FEN, help="Starting FEN to play from")
    parser.add_argument('--fullscreen', action=argparse.BooleanOptionalAction, help="Automatically set browser window to fullscreen")
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, help="Print debug text to console")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    debug = args.debug
    url = args.url
    fen = args.fen
    fullscreen = args.fullscreen
    game = Game(port, url, fullscreen, fen, debug)

    try:
        while True:
            game.run()
            time.sleep(0.033) # ~30fps
    except:
        tb = traceback.format_exc()
        game.debug_print('Game crashed! Dumping state.')
        game.debug_print(str(game))
        game.debug_print(tb)

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
