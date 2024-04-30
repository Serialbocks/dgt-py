import argparse
import os, sys, time
from utils import *

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Show game following chess rules from DGT board to console")
    parser.add_argument("--color", type=str, default="white", help="Color of the player's pieces: 'white' or 'black'")
    parser.add_argument("--screen_x", type=int, default=236, help="Horizontal screen coordinate of top left of chess board")
    parser.add_argument("--screen_y", type=int, default=187, help="Vertical screen coordinate of top left of chess board")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    color = args.color
    screen_x = args.screen_x
    screen_y = args.screen_y
    auto_screen = AutoScreen(color, screen_x, screen_y)

    auto_screen.make_uci_move('e2e4', color)
    time.sleep(1)
    auto_screen.make_uci_move('e7e5', color)
    time.sleep(1)
    auto_screen.make_uci_move('d1h5', color)
    time.sleep(1)
    auto_screen.make_uci_move('b8c6', color)
    time.sleep(1)
    auto_screen.make_uci_move('f1c4', color)
    time.sleep(1)
    auto_screen.make_uci_move('g8f6', color)
    time.sleep(1)
    auto_screen.make_uci_move('h5f7', color)
    time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)