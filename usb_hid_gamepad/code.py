import board
import busio
import usb_hid
from struct import unpack, pack_into
import time
import gc

# Initialize serial communication with SpaceBall 2003
uart = busio.UART(board.TX, board.RX, baudrate=9600, bits=8, parity=None, stop=1)

uart.write(b"\rCB?\rN7D0t\rP00010001\rMSS\rZ\rBc\r")    

clamp = 1000
scale = 127

report = bytearray(6)
last_report = bytearray(6)
buttons = [0] * 9  # Assuming no button pressed initially

# Mapping of Spaceball buttons to gamepad buttons
button_map = {
    0: 0,   # Spaceball button 1 -> gamepad Button 1
    1: 1,   # Spaceball button 2 -> gamepad Button 2
    2: 2,   # Spaceball button 3 -> gamepad Button 3
    3: 3,   # Spaceball button 4 -> gamepad Button 4
    4: 4,   # Spaceball button 5 -> gamepad Button 5
    5: 5,   # Spaceball button 6 -> gamepad Button 6
    6: 6,   # Spaceball button 7 -> gamepad Button 7
    7: 7,   # Spaceball button 8 -> gamepad Button 8
    8: 8    # Spaceball button 9 (Rezero) -> gamepad Button 9
}
def parse_ball_data(data):
    x, y, z, rx, ry, rz = unpack('>hhhhhh', data[:12])
    print(f"Raw data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
    x = max(min(x, clamp), -clamp)
    y = max(min(y, clamp), -clamp)
    z = max(min(z, clamp), -clamp)
    rx = max(min(rx, clamp), -clamp)
    ry = max(min(ry, clamp), -clamp)
    rz = max(min(rz, clamp), -clamp)

    # Scale and offset values to -127 to 127 range
    x = int((x / clamp) * scale + scale)
    y = int((y / clamp) * scale + scale)
    z = int((z / clamp) * scale + scale)
    rx = int((rx / clamp) * scale + scale)
    ry = int((ry / clamp) * scale + scale)  # Reversed ry
    rz = int((rz / clamp) * scale + scale)

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
    report[:] = bytearray(8)

    # Pack buttons into the first two bytes
    button_bytes = 0
    for i in range(9):
        if buttons[i]:
            button_bytes |= 1 << i
    report[0] = button_bytes & 0xFF
    report[1] = (button_bytes >> 8) & 0xFF

    # Pack joystick positions
    report[2] = x
    report[3] = y
    report[4] = z
    report[5] = rx
    report[6] = ry
    report[7] = rz
    
    if report != last_report:
        usb_hid.devices[0].send_report(report, 4)
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

            send_gamepad_report(rz, rx, ry, z, y, x, buttons)
            
        elif packet_type == 'K':
            data = packet[1:]
            buttons = parse_button_data(data)
            print(f"Button data: {buttons}")

            send_gamepad_report(scale, scale, scale, scale, scale, scale, buttons)