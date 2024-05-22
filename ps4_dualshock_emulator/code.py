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
scale = 127

report = bytearray(20)
last_report = bytearray(20)
buttons = [0] * 9  # Assuming no button pressed initially

# Mapping of Spaceball buttons to gamepad 4 buttons
button_map = {
    4: 0,   # Spaceball button 5 -> gamepad 4 Square
    5: 1,   # Spaceball button 6 -> gamepad 4 X
    6: 2,   # Spaceball button 7 -> gamepad 4 Circle
    7: 3,   # Spaceball button 8 -> gamepad 4 Triangle
    8: 8    # Spaceball button 9 -> gamepad 4 Share
}

# Function to determine hat switch value
def get_hat_switch_value(buttons):
    if buttons[0] and not buttons[1] and not buttons[2] and not buttons[3]:
        return 0  # Up
    elif buttons[0] and buttons[1] and not buttons[2] and not buttons[3]:
        return 1  # Up-Right
    elif not buttons[0] and buttons[1] and not buttons[2] and not buttons[3]:
        return 2  # Right
    elif not buttons[0] and buttons[1] and buttons[2] and not buttons[3]:
        return 3  # Down-Right
    elif not buttons[0] and not buttons[1] and buttons[2] and not buttons[3]:
        return 4  # Down
    elif not buttons[0] and not buttons[1] and buttons[2] and buttons[3]:
        return 5  # Down-Left
    elif not buttons[0] and not buttons[1] and not buttons[2] and buttons[3]:
        return 6  # Left
    elif buttons[0] and not buttons[1] and not buttons[2] and buttons[3]:
        return 7  # Up-Left
    else:
        return 8  # Neutral


def parse_ball_data(data):
    x, y, z, rx, ry, rz = unpack('>hhhhhh', data[:12])
    print(f"Raw data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
    x = max(min(x, clamp), -clamp)
    y = max(min(y, clamp), -clamp)
    z = max(min(z, clamp), -clamp)
    rx = max(min(rx, clamp), -clamp)
    ry = max(min(ry, clamp), -clamp)
    rz = max(min(rz, clamp), -clamp)

    # Scale and offset values to 0-255 range
    x = int((x / clamp) * scale + 127.5)
    y = int((y / clamp) * scale + 127.5)
    z = int((z / clamp) * scale + 127.5)
    rx = int((rx / clamp) * scale + 127.5)
    ry = 255 - int((ry / clamp) * scale + 127.5)  # Reversed rx
    rz = int((rz / clamp) * scale + 127.5)

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

def send_gamepad_report(x, y, z, rx, ry, rz, buttons):
    # Ensure the report is correctly sized
    report[:] = bytearray(20)

    # Pack joystick positions
    pack_into('<BBBB', report, 0, x, y, z, rz)
    
    # Pack hat switch
    hat_switch_value = get_hat_switch_value(buttons)
    report[4] = (hat_switch_value & 0x0F)
        
    # Pack buttons into the high nibble of byte 5 and the bytes 6 and 7
    for spaceball_btn, ds4_btn in button_map.items():
        if buttons[spaceball_btn]:
            if ds4_btn < 4:
                report[4] |= 1 << (ds4_btn + 4)  # Buttons 1-4 in high nibble of byte 5
            elif ds4_btn < 16:
                report[6] |= 1 << (ds4_btn - 8)
            else:
                report[7] |= 1 << (ds4_btn - 16)
    
    # Pack remaining axes
    pack_into('<BB', report, 18, rx, ry)
    
    if report != last_report:
        usb_hid.devices[0].send_report(report, 1)
        last_report[:] = report
        
while True:
    gc.collect()
    packet = read_packet()
    if len(packet) > 0:
        packet_type = chr(packet[0])
        
        if packet_type == 'D':
            data = packet[3:]
            x, y, z, rx, ry, rz = parse_ball_data(data)
            print(f"Ball data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")

            send_gamepad_report(rz, rx, ry, x, y, z, buttons)
            
        elif packet_type == 'K':
            data = packet[1:]
            buttons = parse_button_data(data)
            print(f"Button data: {buttons}")

            send_gamepad_report(scale, scale, scale, scale, scale, scale, buttons)