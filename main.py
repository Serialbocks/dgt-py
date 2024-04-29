import sys, os, time
import serial # type: ignore

from dgt_constants import DgtConstants

ser = None

def main():
    ser = serial.Serial(port='COM7', baudrate=9600)
    ser.write(bytes([DgtConstants.DGT_SEND_RESET]))
    
    while True:
        ser.write(bytes([DgtConstants.DGT_SEND_BRD]))
        time.sleep(0.1)
        s = b''
        bytes_read = 0
        while(ser.in_waiting > 0):
            c = ser.read(1)
            s += c
            bytes_read += 1
        
        print('bytes read: ' + str(bytes_read))
        print(s)
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        if ser is not None and ser.is_open:
            ser.close()
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)