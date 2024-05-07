import sys, os, glob, subprocess, time
import serial
from PyQt5 import QtWidgets, uic, QtCore

from chess_dot_com import *
from dgt_constants import *

DEFAULT_URL = "https://www.chess.com/play/computer"

class Gui:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)

        self.window = uic.loadUi("ui/main.ui")

        ports = self.serial_ports()
        serialPort = self.window.serialPort
        serialPort.addItems(ports)
        serialPort.currentIndexChanged.connect(self.serial_index_changed)

        self.window.connectBoard.clicked.connect(self.connect_button_pressed)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.run)
        self.timer.setInterval(33) # ~30fps

        self.window.show()
        app.exec()

    def run(self):
        self.game.run()

    def connect_button_pressed(self):
        port = self.window.serialPort.currentText()
        url = DEFAULT_URL
        is_white = self.window.white.isChecked()
        fullscreen = self.window.fullscreen.isChecked()
        fen = FULL_STARTING_FEN
        use_board_state = self.window.boardState.isChecked()
        analysis = self.window.analysis.isChecked()
        use_game = None
        color = 'black'
        if is_white:
            color = 'white'
        fen = FULL_STARTING_FEN
        debug = True # might as well always show the output in the console
        
        self.game = Game(port, url, fullscreen, fen, use_board_state, analysis, use_game, color, debug)
        self.timer.start()

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