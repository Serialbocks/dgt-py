import sys, os, time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from utils import *
from dgt_constants import *

def main():
    driver = webdriver.Chrome()
    driver.get("https://www.chess.com/analysis")
    driver.maximize_window()
    body = driver.find_element(By.CSS_SELECTOR, "body")
    body.send_keys(Keys.CONTROL + Keys.HOME)
    
    fen = get_fen_from_browser(driver)
    print(fen)
    assert fen == STARTING_FEN

    make_uci_move(driver, 'd2d4', True)
    
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