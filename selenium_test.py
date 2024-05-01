import sys, os, time

from selenium import webdriver
from utils import *
from dgt_constants import *

def main():
    driver = webdriver.Chrome()
    driver.get("https://www.chess.com/analysis")
    
    fen = get_fen_from_browser(driver)
    print(fen)
    assert fen == STARTING_FEN
    time.sleep(15)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)