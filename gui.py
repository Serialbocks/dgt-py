import sys, os, glob, subprocess, time
import serial
from PyQt5 import QtWidgets, uic, QtCore

from chess_dot_com import *
from dgt_constants import *
from auto_clock import *

DEFAULT_URL = "https://www.chess.com/play/computer"

PAGE_MAIN_MENU = 0
PAGE_CLOCK_SETUP = 1
PAGE_CLOCK = 2

BLACK_TIME_DEFAULT_X = 120
WHITE_TIME_DEFAULT_X = 530
DEFAULT_Y = 110
PLAYER_TURN_STYLESHEET = ""
OPPONENT_TURN_STYLESHEET = "color: rgb(159, 159, 159)"

class Gui:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)

        self.window = uic.loadUi("ui/main.ui")

        # init UI
        ports = self.serial_ports()
        serialPort = self.window.serialPort
        serialPort.addItems(ports)
        serialPort.currentIndexChanged.connect(self.serial_index_changed)
        self.window.connectBoard.clicked.connect(self.connect_button_pressed)
        self.window.startClock.clicked.connect(self.start_clock_pressed)

        self.chess_dot_com_timer = QtCore.QTimer()
        self.chess_dot_com_timer.timeout.connect(self.run_chess_dot_com)
        self.chess_dot_com_timer.setInterval(33) # ~30fps

        self.clock_timer = QtCore.QTimer()
        self.clock_timer.timeout.connect(self.run_clock)
        self.clock_timer.setInterval(33) # ~30fps

        self.board_timer = QtCore.QTimer()
        self.board_timer.timeout.connect(self.run_board)
        self.board_timer.setInterval(33) # ~30fps

        self.window.show()
        app.exec()

    def run_chess_dot_com(self):
        self.game.run()

    def run_clock(self):
        result = self.clock.run_clock()
        white = result['white']
        black = result['black']
        white_x = WHITE_TIME_DEFAULT_X
        black_x = BLACK_TIME_DEFAULT_X

        if len(white) >= 8:
            white_x -= 100
        elif len(white) >= 7:
            white_x -= 70
        elif len(white) >= 5:
            white_x -= 30

        if len(black) >= 8:
            black_x -= 100
        elif len(black) >= 7:
            black_x -= 70
        elif len(black) >= 5:
            black_x -= 30

        if(result['white_to_move']):
            self.window.whiteTimer.setStyleSheet(PLAYER_TURN_STYLESHEET)
            self.window.blackTimer.setStyleSheet(OPPONENT_TURN_STYLESHEET)
        else:
            self.window.blackTimer.setStyleSheet(PLAYER_TURN_STYLESHEET)
            self.window.whiteTimer.setStyleSheet(OPPONENT_TURN_STYLESHEET)

        self.window.whiteTimer.move(white_x, DEFAULT_Y)
        self.window.blackTimer.move(black_x, DEFAULT_Y)

        self.window.whiteTimer.setText(white)
        self.window.blackTimer.setText(black)

    def run_board(self):
        self.clock.run_board()

    def start_clock_pressed(self):
        minutes = self.window.minutes.value()
        seconds = self.window.seconds.value()
        if minutes == 0 and seconds == 0:
            return
        start_time_ms = (minutes * 60000) + (seconds * 1000)
        increment_ms = (self.window.increment.value() * 1000)
        port = self.window.serialPort.currentText()
        self.clock = AutoClock(port, start_time_ms, increment_ms)
        self.clock_timer.start()
        self.board_timer.start()
        self.run_clock() # set labels before showing page
        self.window.page.setCurrentIndex(PAGE_CLOCK)

    def connect_button_pressed(self):
        port = self.window.serialPort.currentText()
        url = DEFAULT_URL
        is_white = self.window.white.isChecked()
        fullscreen = self.window.fullscreen.isChecked()
        fen = FULL_STARTING_FEN
        use_board_state = self.window.boardState.isChecked()
        analysis = self.window.analysis.isChecked()
        clock = self.window.clock.isChecked()
        use_game = None
        color = 'black'
        if is_white:
            color = 'white'
        fen = FULL_STARTING_FEN
        debug = True # might as well always show the output in the console

        if(clock):
            self.window.page.setCurrentIndex(PAGE_CLOCK_SETUP)
            return
        
        self.game = Game(port, url, fullscreen, fen, use_board_state, analysis, use_game, color, debug)
        self.chess_dot_com_timer.start()

    def serial_index_changed(self, i):
        if i >= 0:
            self.window.connectBoard.setEnabled(True)
        else:
            self.window.connectBoard.setEnabled(False)

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            subprocess.Popen(['sh', "./open-bt-connection.sh"])
            time.sleep(5)
            ports = ['/dev/rfcomm0']
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

def main():
    gui = Gui()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)