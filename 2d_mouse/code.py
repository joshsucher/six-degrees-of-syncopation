import board
import busio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import struct
from struct import unpack
import time

# Initialize serial communication with SpaceBall 2003
uart = busio.UART(board.TX, board.RX, baudrate=9600, bits=8, parity=None, stop=1)

uart.write(b"\rCB\rFT?\rFR?\rFB?\rP00010001\rMSS\rZ\rBc\r")    

# uart.write(b"\rCB\rNAt\rFTp\rFRp\rFBp\rP00010001\rMSS\rZ\rBc\r")    
# uart_source.uart.write(b"\rCB\rNT\rFT?\rFR?\rP@r@r\rMSSV\rZ\rBcCcCcC\r") # default

# Create a mouse HID device
mouse = Mouse(usb_hid.devices)
# Create ConsumerControl instance
consumer_control = ConsumerControl(usb_hid.devices)

button_9_pressed_time = 0
scroll_time = 1
prev_ry = 0

# Define a list of Consumer Control codes corresponding to your buttons
control_codes = [
    ConsumerControlCode.BRIGHTNESS_DECREMENT,  # Button 1
    ConsumerControlCode.BRIGHTNESS_INCREMENT,  # Button 2
    ConsumerControlCode.SCAN_PREVIOUS_TRACK,   # Button 3
    ConsumerControlCode.PLAY_PAUSE,            # Button 4
    ConsumerControlCode.SCAN_NEXT_TRACK,       # Button 5
    ConsumerControlCode.MUTE,                  # Button 6
    ConsumerControlCode.VOLUME_DECREMENT,      # Button 7
    ConsumerControlCode.VOLUME_INCREMENT       # Button 8
]

def parse_ball_data(data):
    x, y, z, rx, ry, rz = unpack('>hhhhhh', data[:12])
    print(f"Raw data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
    # Scale the data based on spaceball.c
    x = max(min(x // 2, 350), -350)
    y = max(min(y // 2, 350), -350)
    z = max(min(z // 2, 350), -350)
    rx = max(min(rx // 2, 350), -350)
    ry = max(min(ry // 6, 350), -350)
    rz = max(min(rz // 2, 350), -350)
    
    return rz, rx, ry, z, y, x

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

def interpolate_mouse_movement(x1, y1, x2, y2, steps):
    dx = (x2 + x1) // steps
    dy = (y2 + y1) // steps
    for _ in range(steps):
        mouse.move(dx, dy)

def send_translation_report(x, y, z):
    report = bytearray(8)
    report[0] = 0x01  # Report ID for rotation data
    struct.pack_into('>hhh', report, 1, x, y, z)
    print(f"Sending translation report: {report}")  # Log the report data
    usb_hid.devices[0].send_report(report)

def send_rotation_report(rx, ry, rz):
    report = bytearray(8)
    report[0] = 0x02  # Report ID for rotation data
    struct.pack_into('>hhh', report, 1, rx, ry, rz)
    print(f"Sending rotation report: {report}")  # Log the report data
    usb_hid.devices[0].send_report(report)

prev_x, prev_y = 0, 0

while True:
    packet = read_packet()
    if len(packet) > 0:
        packet_type = chr(packet[0])
        
        if packet_type == 'D':
            data = packet[3:]
            x, y, z, rx, ry, rz = parse_ball_data(data)
            print(f"Ball data: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
            
            prev_ry = ry
            
            if (time.monotonic() - button_9_pressed_time) > 0.1:
                if abs(z) > 4 and abs(y) < 20 and abs(x) < 20:
                    mouse.move(wheel=z*-1)
                    scroll_time = time.monotonic()
                elif scroll_time and scroll_time > 0.1:
                    # Interpolate mouse movement
                    interpolate_mouse_movement(prev_x, prev_y, x, y, 6)
                    prev_x, prev_y = x, y
    
            # Send rotation data as a separate report
            # send_rotation_report(rx, ry, rz)

        elif packet_type == 'K':
            data = packet[1:]
            buttons = parse_button_data(data)
            print(f"Button data: {buttons}")

            for i in range(9):  # Iterate over buttons 1-8
                if i == 8:  # Button 9 (rezero button)
                    if buttons[i] and prev_ry >= -200:
                        mouse.press(Mouse.LEFT_BUTTON)
                        button_9_pressed_time = time.monotonic()
                    elif buttons[i] and prev_ry < -200:
                        mouse.press(Mouse.RIGHT_BUTTON)
                        mouse.release(Mouse.RIGHT_BUTTON)
                    else:
                        mouse.release(Mouse.LEFT_BUTTON)

                else:  # Buttons 1-8
                    if buttons[i]:
                        consumer_control.send(control_codes[i])
