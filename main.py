import serial
import dgt_constants

ser = serial.Serial(port='COM7', baudrate=9600, timeout=3)
print(ser)
ser.write(bytes([dgt_constants.DGT_SEND_BRD]))
ser.write(bytes([dgt_constants.DGT_SEND_UPDATE_NICE]))
s = ser.read(1000)

print(s)

ser.close()