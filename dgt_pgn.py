
import argparse
import datetime
import base64
import serial # type: ignore
import time


from dgt_driver import DgtDriver
from dgt_message import DgtMessage
from bw_time import BWTime
from board import Board
from role import Role
from square import Square
from move_parser import MoveParser
from game import Game

class DgtPgn:
    def __init__(self, port_name: str, prefix: str, debug: bool):
        print(f"Connecting to {port_name}")
        self.output_prefix = prefix
        self.port = serial.Serial(port_name, 9600, parity=serial.PARITY_NONE, bytesize=8, stopbits=1)
        if not self.port.is_open:
            raise RuntimeError(f"Failed to open port {port_name}.")

        self.driver = DgtDriver(self.got_message, self.write_bytes)

        if debug:
            self.debug_out = open(f"{prefix}.debug", "w")
            self.start_nanos = time.time_ns()
        else:
            self.debug_out = None

    def get_output_prefix(self) -> str:
        return self.output_prefix

    def is_debug(self) -> bool:
        return self.debug_out is not None

    def init_driver(self, driver: DgtDriver):
        raise NotImplementedError

    def got_message(self, msg: DgtMessage):
        raise NotImplementedError

    def shutdown_hook(self):
        pass

    def run(self):
        import atexit
        atexit.register(self.shutdown_hook)
        self.init_driver(self.driver)
        if self.debug_out is not None:
            print(f"Starting read loop, outputPrefix={self.output_prefix}")
        while True:
            data = self.port.read(self.port.in_waiting)
            if not data:
                time.sleep(0.2)
            else:
                self.debug_write(True, data)
                self.driver.got_bytes(data)

    def write_bytes(self, bytes: bytes):
        try:
            self.debug_write(False, bytes)
            self.port.write(bytes)
        except IOError as e:
            print(f"Failed to write: {e}")

    def debug_write(self, is_input: bool, bytes: bytes):
        if self.debug_out is None:
            return

        time_delta = time.time_ns() - self.start_nanos
        direction = '<' if is_input else '>'
        byte_string = base64.b64encode(bytes).decode()
        self.debug_out.write(f"{time_delta} {direction} {byte_string}\n")
        self.debug_out.flush()

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Record games from DGT board to PGN")
    parser.add_argument("--debug", action="store_true", help="Write debug data to file")
    parser.add_argument("--prefix", type=str, default=datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"),
                        help="Filename prefix for PGN output")
    parser.add_argument("--port", type=str, required=True, help="Name of serial port to connect to")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()

    prefix = args.prefix
    port_name = args.port
    debug = args.debug

    dgt_pgn = DgtPgn(port_name, prefix, debug)
    dgt_pgn.run()

class DgtPgn(DgtPgn):
    def __init__(self, port_name: str, prefix: str, debug: bool):
        super().__init__(port_name, prefix, debug)
        self.parser = MoveParser(self.game_complete)
        self.game_count = 0

    def init_driver(self, driver: DgtDriver):
        driver.board()
        driver.update_nice()

    def got_message(self, msg: DgtMessage):
        print('got message')
        print(msg)
        self.parser.got_message(msg)
        game = self.parser.current_game(None)

        if game is not None and game.moves:
            try:
                self.print_board(self.parser.board_state())
                self.print_moves(game)
                clock_info = game.moves[-1].clock_info
                if clock_info is not None:
                    self.print_clocks(clock_info)
            except IOError as e:
                raise RuntimeError(e)

    def shutdown_hook(self):
        self.parser.end_game()

    def game_complete(self, game: Game):
        try:
            self.game_count += 1
            filename = f"{self.get_output_prefix()}-{self.game_count}.pgn"
            if self.is_debug():
                print(f"Got game, writing to {filename}")
            with open(filename, "w") as writer:
                writer.write("[White \"White\"]\n")
                writer.write("[Black \"Black\"]\n\n")
                writer.write(game.pgn(True))
        except IOError as e:
            raise RuntimeError(e)

    def print_board(self, board: Board):
        self.clear_screen()

        # Board frame
        self.at(1, 1, "+--------+")
        for row in range(2, 10):
            self.at(row, 1, "|")
            self.at(row, 10, "|")
        self.at(10, 1, "+--------+")

        # Pieces
        for square, piece in board.piece_map().items():
            rank = Square.rank(square)
            file = Square.file(square)
            symbol = piece.role.symbol
            if piece.role == Role.PAWN:
                symbol = "P"
            self.at(9 - rank, file + 2, symbol.lower() if not piece.white else symbol)

    def print_moves(self, game: Game):
        moves = []
        for i in range((len(game.moves) + 1) // 2):
            white = game.moves[2 * i].san
            black = game.moves[2 * i + 1].san if 2 * i + 1 < len(game.moves) else ""
            moves.append(f"{i + 1:3}. {white:7} {black:7}")

        cur_row = 1
        cur_col = 12
        for move in moves:
            self.at(cur_row, cur_col, move)
            cur_row += 1

    def print_clocks(self, clocks: BWTime):
        white_time = clocks.left_time_string()
        black_time = clocks.right_time_string()
        self.at(11, 1, white_time)
        self.at(12, 4, black_time)

    def at(self, x: int, y: int, s: str):
        print(f"\u001B[{x};{y}H{s}", end="")

    def clear_screen(self):
        print("\u001B[1,1H\u001B[2J", end="")

if __name__ == "__main__":
    main()

