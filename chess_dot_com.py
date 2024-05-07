import argparse
import sys, os, time, logging
import enum
import serial
import traceback
from pathlib import Path
import chess
import pickle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from utils import *
from dgt_constants import *

COOKIE_FILE = 'cookies.pkl'

class GameState(enum.Enum):
    PRE_GAME = 0
    PLAYER_TURN = 1
    OPPONENT_TURN = 2
    WAIT_PLAYER_UPDATE_OPPONENT = 3

class Game():
    def __init__(self, port, url, fullscreen, starting_fen, use_board_state, analysis, use_game, color, debug):
        self.port = port
        self.debug = debug
        self.url = url
        self.fullscreen = fullscreen
        self.starting_fen = starting_fen
        self.use_board_state = use_board_state
        self.use_game = use_game
        self.saved_game_filename = None
        self.analysis = analysis
        self.color = color
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
        log_filename = time.strftime("logs/%Y-%m-%d_%H.%M.%S.log")
        logging.basicConfig(filename=log_filename, filemode='w', level=logging.INFO)

        self.board_reset_msg_sent = False
        self.serial = serial.Serial(port=self.port, baudrate=9600)

        if(self.use_board_state):
            self.set_fen_to_last_ee_game()
        elif(self.use_game):
            self.set_game_to_game_file()

        if(self.analysis):
            self.url = "https://chess.com/analysis"

        self.reset_game(self.starting_fen)
        options = Options()
        options.headless = True
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        self.driver = webdriver.Chrome(options)
        
        self.driver.get(self.url)
        my_file = Path(COOKIE_FILE)
        if my_file.is_file():
            cookies = pickle.load(open(COOKIE_FILE, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        self.driver.get(self.url)

        # maximize to full screen and check for board
        self.driver.maximize_window()
        body = self.driver.find_element(By.CSS_SELECTOR, "body")
        if self.fullscreen:
            self.driver.fullscreen_window()
        body.send_keys(Keys.CONTROL + Keys.HOME)

        self.set_state(GameState.PRE_GAME)

    def set_game_to_game_file(self):
        moves = ''
        game = chess.Board()
        with open(self.use_game) as file:
            file.readline()
            while move := file.readline():
                game.push_uci(move)
                if len(moves) > 0:
                    moves += ' '
                moves += move

        self.starting_fen = game.fen()
        self.url = 'https://www.chess.com/practice/custom?color=white&fen=' + FULL_STARTING_FEN + '&is960=false&moveList=' + moves
        self.debug_print('Setting fen to ' + self.starting_fen)
        self.debug_print('Setting url to ' + self.url)

    def set_fen_to_last_ee_game(self):
        events = get_ee_events(self.serial)
        games = get_ee_games(events)
        num_games = len(games)
        if num_games <= 0:
            return
        last_game = games[num_games-1]
        self.starting_fen = last_game.fen()
        moves = ''
        while last_game.fen() != FULL_STARTING_FEN:
            if len(moves) > 0:
                moves = ' ' + moves
            moves = last_game.pop().uci() + moves
        self.url = 'https://www.chess.com/practice/custom?color=white&fen=' + FULL_STARTING_FEN + '&is960=false&moveList=' + moves
        self.debug_print('Setting fen to ' + self.starting_fen)
        self.debug_print('Setting url to ' + self.url)

    def reset_game(self, starting_fen, state=GameState.PRE_GAME):
        if(self.saved_game_filename is not None):
            if self.board is not None:
                with open(self.saved_game_filename, 'a') as file:
                    file.write(self.board.fen())

        saved_games_dir = 'saved_games/'
        game_index = len([name for name in os.listdir(saved_games_dir) if os.path.isfile(os.path.join(saved_games_dir, name))])
        self.saved_game_filename = saved_games_dir + str(game_index) + '.game'
        with open(self.saved_game_filename, 'a') as file:
            file.write(time.strftime("%Y-%m-%d_%H.%M.%S\n"))

        self.board = chess.Board(starting_fen)
        self.legal_moves = legal_fens(self.board)
        self.set_state(state)

    def debug_print(self, text):
        self.logged_this_state = True
        logging.info(text)
        if self.debug:
            print(text)

    def close(self):
        if self.serial.is_open:
            self.serial.close()

    def set_state(self, state):
        if state == None:
            raise ValueError('State being set to None?')
        
        # if we're in analysis mode, the player is always moving the pieces
        if self.analysis and state == GameState.OPPONENT_TURN:
            state = GameState.PLAYER_TURN

        self.logged_this_state = False
        self.state = state
        self.debug_print(self.state)
        self.logged_this_state = False
        self.state_iterations = 0
        pickle.dump(self.driver.get_cookies(), open(COOKIE_FILE, "wb"))

    def make_move(self, uci_move):
        self.board.push_uci(uci_move)
        with open(self.saved_game_filename, 'a') as file:
            file.write(uci_move + '\n')
    
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
        if self.color == None:
            color_in = input("Enter color to begin (W/b): ")
            if len(color_in) > 0 and color_in[0].lower() == 'b':
                self.is_white = False
        elif len(self.color) > 0 and self.color[0] == 'b':
            self.is_white = False

        # pickle.dump(self.driver.get_cookies(), open(COOKIE_FILE, "wb"))

        if is_white_to_move(self.board) == self.is_white:
            self.set_state(GameState.PLAYER_TURN)
        else:
            self.set_state(GameState.OPPONENT_TURN)

    def state_player_turn(self):
        s = get_dgt_board_state(self.serial)
        fen = dgt_message_to_fen(s)
        if not self.logged_this_state:
            self.debug_print("DGT FEN: " + fen)
            self.debug_print("Internal State FEN: " + self.board.fen())
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.make_move(move)
            self.legal_moves = legal_fens(self.board)
            make_uci_move(self.driver, move, self.is_white)
            self.set_state(GameState.OPPONENT_TURN)
            if(self.board.is_checkmate()):
                self.reset_game(FULL_STARTING_FEN)

    def state_opponent_turn(self):
        fen = get_fen_from_browser(self.driver)
        if self.state_iterations == 0:
            self.debug_print("Browser FEN: " + fen)
        if fen in self.legal_moves:
            move = self.legal_moves[fen]
            self.make_move(move)
            self.legal_moves = legal_fens(self.board)
            self.set_state(GameState.WAIT_PLAYER_UPDATE_OPPONENT)
            if(self.board.is_checkmate()):
                self.reset_game(FULL_STARTING_FEN)
        
    def state_wait_player_update_opponent(self):
        s = get_dgt_board_state(self.serial)
        board_fen = dgt_message_to_fen(s)
        game_fen = fen_from_board(self.board)
        if not self.logged_this_state:
            self.debug_print("DGT FEN: " + board_fen)
            self.debug_print("Internal State FEN: " + self.board.fen())
            
        if board_fen == game_fen:
            self.set_state(GameState.PLAYER_TURN)

    def run(self):
        if self.state == GameState.PRE_GAME:
            self.state_pre_game()
        elif self.state == GameState.PLAYER_TURN:
            self.state_player_turn()
        elif self.state == GameState.OPPONENT_TURN:
            self.state_opponent_turn()
        elif self.state == GameState.WAIT_PLAYER_UPDATE_OPPONENT:
            self.state_wait_player_update_opponent()
        else:
            raise ValueError('Game got into an invalid state: ' + str(self.state))
        self.state_iterations += 1

game = None

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Play game on chess.com in browser")
    parser.add_argument("--port", type=str, default="COM10", help="Name of serial port to connect to")
    parser.add_argument("--url", type=str, default="https://www.chess.com/play/computer", help="Starting URL")
    parser.add_argument("--fen", type=str, default=FULL_STARTING_FEN, help="Starting FEN to play from")
    parser.add_argument('--fullscreen', action=argparse.BooleanOptionalAction, help="Automatically set browser window to fullscreen")
    parser.add_argument('--useBoardState', action=argparse.BooleanOptionalAction, help="Use board's current state as starting position")
    parser.add_argument('--useGame', type=str, help="Use saved game as starting position")
    parser.add_argument('--analysis', action=argparse.BooleanOptionalAction, help="Play in analysis mode")
    parser.add_argument("--color", type=str, help="Color of the pieces. If not specified, will ask through stdio.")
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, help="Print debug text to console")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    debug = args.debug
    url = args.url
    fen = args.fen
    use_board_state = args.useBoardState
    use_game = args.useGame
    analysis = args.analysis
    fullscreen = args.fullscreen
    color = args.color
    game = Game(port, url, fullscreen, fen, use_board_state, analysis, use_game, color, debug)

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
