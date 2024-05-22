import board
import busio
import usb_hid
from struct import unpack, pack_into
import time
import gc

# Initialize serial communication with SpaceBall 2003
uart = busio.UART(board.TX, board.RX, baudrate=9600, bits=8, parity=None, stop=1)

uart.write(b"\rCB?\rN7D0t\rP00010001\rMSS\rZ\rBc\r")    

# uart.write(b"\rCB\rNAt\rFTp\rFRp\rFBp\rP00010001\rMSS\rZ\rBc\r")    
# uart_source.uart.write(b"\rCB\rNT\rFT?\rFR?\rP@r@r\rMSSV\rZ\rBcCcCcC\r") # default

clamp = 1000
scale = 350

report = bytearray(6)
last_t_report = bytearray(6)
last_r_report = bytearray(6)

def parse_ball_data(data):
    x, y, z, rx, ry, rz = unpack('>hhhhhh', data[:12])
    print(f"Raw data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
    x = max(min(x, clamp), -clamp)
    y = max(min(y, clamp), -clamp)
    z = max(min(z, clamp), -clamp)
    rx = max(min(rx, clamp), -clamp)
    ry = max(min(ry, clamp), -clamp)  # Adjust scaling factor for ry
    rz = max(min(rz, clamp), -clamp)

    # Scale clamped values to the range of -32767 to 32767
    x = int((x / clamp) * scale)
    y = int((y / clamp) * scale)
    z = int((z / clamp) * scale)
    rx = int((rx / clamp) * scale)
    ry = int((ry / clamp) * scale)
    rz = int((rz / clamp) * scale)

    return x, y, z, rx, ry, rz

def parse_button_data(data):
    buttons = [0] * 9
    buttons[0] = (data[1] & 0x01)  # Button 1
    buttons[1] = (data[1] & 0x02) >> 1  # Button 2
    buttons[2] = (data[1] & 0x04) >> 2  # Button 3
    buttons[3] = (data[1] & 0x08) >> 3  # Button 4
    buttons[4] = (data[0] & 0x01)  # Button 5
    buttons[5] = (data[0] & 0x02) >> 1  # Button 6
    buttons[6] = (data[0] & 0x04) >> 2  # Button 7
    buttons[7] = (data[0] & 0x08) >> 3  # Button 8
    buttons[8] = (data[0] & 0x10) >> 4  # Rezero button, right-shifted correctly
    return buttons

def read_packet():
    packet = bytearray()
    while True:
        byte = uart.read(1)
        if byte is None:
            continue
        if byte[0] == ord('^'):
            next_byte = uart.read(1)
            if next_byte is None:
                continue
            if next_byte[0] == ord('Q'):
                packet.append(0x11)  # XON
            elif next_byte[0] == ord('S'):
                packet.append(0x13)  # XOFF
            elif next_byte[0] == ord('M'):
                packet.append(0x0D)  # CR
            elif next_byte[0] == ord('^'):
                packet.append(ord('^'))
                
        else:
            packet.append(byte[0])
        if byte[0] == 0x0D or (len(packet) >= 2 and packet[-2] == 0x0D and packet[-1] == 0x0A):
            return packet

def send_translation_report(x, y, z):
    pack_into('<hhh', report, 0, y*-1, x*-1, z*-1)
    #print(f"Sending rotation report: {report}")
    if report != last_t_report:
        usb_hid.devices[0].send_report(report, 1)
        last_t_report[:] = report

def send_rotation_report(rx, ry, rz):
    pack_into('<hhh', report, 0, rx, ry, rz)
    #print(f"Sending rotation report: {report}")
    if report != last_r_report:
        usb_hid.devices[0].send_report(report, 2)
        last_r_report[:] = report

def send_button_report(buttons):
    button_report = bytearray(6)  # Create a byte array of length 4

    # Map buttons to the correct bits in the report
    if buttons[0]:
        button_report[1] |= 0x10  # Button 1
    if buttons[1]:
        button_report[1] |= 0x20  # Button 2
    if buttons[2]:
        button_report[2] |= 0x40  # Button 3
    if buttons[3]:
        button_report[3] |= 0x80  # Button 4
    if buttons[4]:
        button_report[2] |= 0x80  # Button 5
    if buttons[5]:
        button_report[3] |= 0x02  # Button 6
    if buttons[6]:
        button_report[3] |= 0x01  # Button 7
    if buttons[7]:
        button_report[2] |= 0x40  # Button 8
    if buttons[8]:
        button_report[0] |= 0x01  # Button 9

    # Print the button report for debugging
    print(f"Sending button report: {button_report}")
    usb_hid.devices[0].send_report(button_report, 3)

while True:
    gc.collect()
    packet = read_packet()
    if len(packet) > 0:
        packet_type = chr(packet[0])
        
        if packet_type == 'D':
            data = packet[3:]
            x, y, z, rx, ry, rz = parse_ball_data(data)
            print(f"Ball data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")

            send_translation_report(z*-1, x, y)
            send_rotation_report(rx, rz*-1, ry*-1)
            
        elif packet_type == 'K':
            data = packet[1:]
            buttons = parse_button_data(data)
            print(f"Button data: {buttons}")
            
            send_button_report(buttons)