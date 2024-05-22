import usb_hid

SPACEBALL_2003_DESCRIPTOR = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x08,        # Usage (Multi-axis Controller)
    0xA1, 0x01,        # Collection (Application)
    0xA1, 0x00,        #   Collection (Physical)
    0x85, 0x01,        #     Report ID (1)
    0x16, 0xA2, 0xFE,  #     Logical Minimum (-350)
    0x26, 0x5E, 0x01,  #     Logical Maximum (350)
    0x36, 0x88, 0xFA,  #     Physical Minimum (-1400)
    0x46, 0x78, 0x05,  #     Physical Maximum (1400)
    0x55, 0x0C,        #     Unit Exponent (-4)
    0x65, 0x11,        #     Unit (System: SI Linear, Length: Centimeter)
    0x09, 0x30,        #     Usage (X)
    0x09, 0x31,        #     Usage (Y)
    0x09, 0x32,        #     Usage (Z)
    0x75, 0x10,        #     Report Size (16)
    0x95, 0x03,        #     Report Count (3)
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,              #   End Collection
    0xA1, 0x00,        #   Collection (Physical)
    0x85, 0x02,        #     Report ID (2)
    0x09, 0x33,        #     Usage (Rx)
    0x09, 0x34,        #     Usage (Ry)
    0x09, 0x35,        #     Usage (Rz)
    0x75, 0x10,        #     Report Size (16)
    0x95, 0x03,        #     Report Count (3)
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,              #   End Collection
    0xA1, 0x02,        #   Collection (Logical)
    0x85, 0x03,        #     Report ID (3)
    0x05, 0x09,        #     Usage Page (Button)  
    0x19, 0x01,        #     Usage Minimum (Button 1)
    0x29, 0x08,        #     Usage Maximum (Button 8)
    0x15, 0x00,        #     Logical Minimum (0)
    0x25, 0x01,        #     Logical Maximum (1)
    0x75, 0x01,        #     Report Size (1)
    0x95, 0x08,        #     Report Count (8)
    0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,              #   End Collection
    0xC0,              # End Collection
))

usb_hid.enable((usb_hid.Device.CONSUMER_CONTROL,
                usb_hid.Device.MOUSE,
                # usb_hid.Device.KEYBOARD,
                usb_hid.Device.GAMEPAD,
                usb_hid.Device.VENDOR_DEFINED_DEVICE),
               report_descriptor=SPACEBALL_2003_DESCRIPTOR)