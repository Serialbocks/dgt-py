import sys, os, time
import serial # type: ignore
import chess # type: ignore

from dgt_constants import DgtConstants

ser = None

def piece_byte_to_ascii(piece_byte):
    match piece_byte:
        case DgtConstants.EMPTY:
            return ''
        case DgtConstants.WPAWN:
            return 'P'
        case DgtConstants.WROOK:
            return 'R'
        case DgtConstants.WKNIGHT:
            return 'N'
        case DgtConstants.WBISHOP:
            return 'B'
        case DgtConstants.WKING:
            return 'K'
        case DgtConstants.WQUEEN:
            return 'Q'
        case DgtConstants.BPAWN:
            return 'p'
        case DgtConstants.BROOK:
            return 'r'
        case DgtConstants.BKNIGHT:
            return 'n'
        case DgtConstants.BBISHOP:
            return 'b'
        case DgtConstants.BKING:
            return 'k'
        case DgtConstants.BQUEEN:
            return 'q'
        case _:
            raise ValueError("Invalid piece detected")

def board_message_to_fen(message):
    stripped_message = message[3:]
    if(len(stripped_message) != 64):
        raise ValueError("Invalid board state message")
    
    result = ''
    empty_count = 0
    for rev_rank in range(0, 8):
        rank = 7 - rev_rank
        if empty_count > 0:
            result += str(empty_count)
        if rev_rank != 0:
            result += '/'
        empty_count = 0
        for rev_file in range(0, 8):
            file = 7 - rev_file
            message_index = (rank * 8) + file
            piece = piece_byte_to_ascii(stripped_message[message_index])
            result += piece
            if len(piece) == 0:
                empty_count += 1
            elif empty_count > 0:
                result += str(empty_count)
                empty_count = 0
            
    return result

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

        print(board_message_to_fen(s))
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