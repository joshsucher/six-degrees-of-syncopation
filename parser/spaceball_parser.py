import hid
import struct
import threading
import time
from flask import Flask, jsonify

# Constants for the device (replace with actual values)
VENDOR_ID = 0x239a  # Replace with your device's Vendor ID
PRODUCT_ID = 0x80cc  # Replace with your device's Product ID

# State tracking for buttons and axes
last_button_states = [0] * 9
last_axis_states = {'X': 127, 'Y': 127, 'Z': 127, 'Rx': 127, 'Ry': 127, 'Rz': 127}

app = Flask(__name__)

@app.route('/state')
def get_state():
    return jsonify({
        'buttons': last_button_states,
        'axes': last_axis_states
    })

def read_device(vendor_id, product_id):
    # Open the device
    try:
        device = hid.Device(vendor_id, product_id)
        print(f"Device opened: {device.manufacturer} {device.product}")

        # Read and parse reports
        while True:
            # This will block until it reads a report
            data = device.read(9)  # Read 9 bytes; as per your descriptor
            if data:
                parse_report(data)

    except IOError as e:
        print(f"Could not open device: {e}")
    finally:
        if device:
            device.close()

def parse_report(data):
    global last_button_states, last_axis_states

    # Assuming report ID 4 with 6 axes and 9 buttons
    report_id = data[0]
    if report_id == 4:
        # Parse the button states
        buttons_byte0 = data[1]
        buttons_byte1 = data[2]

        # Decode button states
        button_states = [(buttons_byte0 >> i) & 1 for i in range(8)]
        button9 = (buttons_byte1 & 0x01)
        button_states.append(button9)  # Adding Button 9

        # Parse the axis values (6 axes)
        x, y, z, rx, ry, rz = struct.unpack('<6B', bytes(data[3:9]))

        # Print button states if changed
        button_labels = [
            'Genres 1', 'Genres 2', 'Genres 3', 'Genres 4',
            'Genres 5', 'Genres 6', 'Genres 7', 'Genres 8', 'Play/Pause'
        ]
        for i, state in enumerate(button_states):
            if state and not last_button_states[i]:
                print(button_labels[i])
            last_button_states[i] = state

        # Print axis values at min or max if changed
        axis_labels = ['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz']
        axis_values = {'X': x, 'Y': y, 'Z': z, 'Rx': rx, 'Ry': ry, 'Rz': rz}
        
        for label, value in axis_values.items():
            if value == 0 and last_axis_states[label] != 0:
                print(f"{label}: Min")
            elif value == 254 and last_axis_states[label] != 254:
                print(f"{label}: Max")
            last_axis_states[label] = value

if __name__ == '__main__':
    # Start HID reading in a separate thread
    hid_thread = threading.Thread(target=read_device, args=(VENDOR_ID, PRODUCT_ID))
    hid_thread.start()

    # Start Flask server
    app.run(debug=True, use_reloader=False)
