import time, os, sys
import pyautogui # type: ignore

def move_cursor(y, x):
    print("\033[%d;%dH" % (y, x))

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

ranks_black = ['1', '2', '3', '4', '5', '6', '7', '8']
files_white = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
ranks_white = ranks_black[::-1]
files_black = files_white[::-1]

top_left_x = 236
top_left_y = 187
board_width = 784
square_width = board_width / 8
half_square_width = square_width / 2

top_left_square_x = top_left_x + half_square_width
top_left_square_y = top_left_y + half_square_width

is_white = True

def get_rank_coord(rank):
    ranks = ranks_white
    if not is_white:
        ranks = ranks_black

    return top_left_square_y + (ranks.index(rank) * square_width)

def get_file_coord(file):
    files = files_white
    if not is_white:
        files = files_black

    return top_left_square_x + (files.index(file) * square_width)


def make_uci_move(move):
    if len(move) != 4:
        raise ValueError("invalid uci move")
    
    start_x = get_file_coord(move[0])
    start_y = get_rank_coord(move[1])
    end_x = get_file_coord(move[2])
    end_y = get_rank_coord(move[3])
    pyautogui.moveTo(start_x, start_y)
    pyautogui.mouseDown(button='left')
    pyautogui.moveTo(end_x, end_y, 0.3)
    pyautogui.mouseUp(button='left')

def main():
    make_uci_move('e2e4')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)