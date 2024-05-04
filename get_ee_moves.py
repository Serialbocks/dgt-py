import argparse
import sys, os, time, datetime
import serial
import chess
from utils import *

def save_game(game, folder, game_index):
    filename = folder + str(game_index) + '.game'
    game_fen = game.fen()

    moves = []
    print(game.fen())
    while game.fen() != FULL_STARTING_FEN:
        moves.append(game.pop())

    with open(filename, 'w') as file:
        for move in moves:
            file.write(move.uci() + '\n')
        file.write(game_fen)

def save_games(events):
    print('saving games...')
    folder = time.strftime("logs/%Y-%m-%d_%H.%M.%S/")
    os.makedirs(folder)

    # wait for first starting position message
    game_index = 0
    for game in get_ee_games(events):
        game_index += 1
        save_game(game, folder, game_index)
    print('saved ' + str(game_index) + ' games to ' + folder)

def print_events(events):
    for event in events:
        print(event)

def default_argument_parser(for_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(for_name, description="Test pulling games off board EEPROM")
    parser.add_argument("--port", type=str, default="COM9", help="Name of serial port to connect to")
    parser.add_argument('--save', action=argparse.BooleanOptionalAction, help="Save games to files")
    return parser

def main():
    parser = default_argument_parser("dgtpgn")
    args = parser.parse_args()
    port = args.port
    save = args.save
    ser = serial.Serial(port=port, baudrate=9600)
    time.sleep(0.1)
    board_reset(ser)
    time.sleep(0.1)
    events = get_ee_events(ser)

    if save:
        save_games(events)
    else:
        print_events(events)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)