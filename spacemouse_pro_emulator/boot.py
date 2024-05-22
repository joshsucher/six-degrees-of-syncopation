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
	0x05, 0x01,        #     Usage Page (Generic Desktop Ctrls)
	0x05, 0x09,        #     Usage Page (Button)
	0x19, 0x01,        #     Usage Minimum (0x01)
	0x29, 0x03,        #     Usage Maximum (0x03)
	0x15, 0x00,        #     Logical Minimum (0)
	0x25, 0x01,        #     Logical Maximum (1)
	0x35, 0x00,        #     Physical Minimum (0)
	0x45, 0x01,        #     Physical Maximum (1)
	0x75, 0x01,        #     Report Size (1)
	0x95, 0x03,        #     Report Count (3)
	0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x95, 0x01,        #     Report Count (1)
	0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x19, 0x05,        #     Usage Minimum (0x05)
	0x29, 0x06,        #     Usage Maximum (0x06)
	0x95, 0x02,        #     Report Count (2)
	0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x95, 0x02,        #     Report Count (2)
	0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x09, 0x09,        #     Usage (0x09)
	0x95, 0x01,        #     Report Count (1)
	0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x95, 0x03,        #     Report Count (3)
	0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x19, 0x0D,        #     Usage Minimum (0x0D)
	0x29, 0x10,        #     Usage Maximum (0x10)
	0x95, 0x04,        #     Report Count (4)
	0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x95, 0x06,        #     Report Count (6)
	0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x19, 0x17,        #     Usage Minimum (0x17)
	0x29, 0x1B,        #     Usage Maximum (0x1B)
	0x95, 0x05,        #     Report Count (5)
	0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0x95, 0x15,        #     Report Count (21)
	0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
	0xC0,              #   End Collection
    0xC0,              # End Collection
))

spaceball = usb_hid.Device(
    report_descriptor=SPACEBALL_2003_DESCRIPTOR,
    usage_page=0x01,  # Generic Desktop Control
    usage=0x08,  # Multi-axis Controller
    report_ids=(1, 2, 3),  # Descriptor uses report IDs 1, 2, 3, 4, and 5
    in_report_lengths=(6, 6, 6),  # Translation, rotation, buttons, mouse buttons, consumer control
    out_report_lengths=(0, 0, 0),  # It does not receive any reports
)

usb_hid.enable((
    spaceball,
))