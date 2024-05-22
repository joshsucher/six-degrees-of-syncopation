import sys

if sys.implementation.version[0] < 3:
    raise ImportError(
        "{0} is not supported in CircuitPython 2.x or lower".format(__name__)
    )

# pylint: disable=wrong-import-position
import struct
from . import find_device

try:
    from typing import Sequence
    import usb_hid
except ImportError:
    pass


class ConsumerControl:

    def __init__(self, devices: Sequence[usb_hid.Device], timeout: int = None) -> None:
        self._consumer_device = find_device(
            devices, usage_page=0x0C, usage=0x01, timeout=timeout
        )

        # Reuse this bytearray to send consumer reports.
        self._report = bytearray(2)

    def send(self, consumer_code: int) -> None:
        self.press(consumer_code)
        self.release()

    def press(self, consumer_code: int) -> None:
        struct.pack_into("<H", self._report, 0, consumer_code)
        self._consumer_device.send_report(self._report)

    def release(self) -> None:
        self._report[0] = self._report[1] = 0x0
        self._consumer_device.send_report(self._report)
