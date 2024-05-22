from . import find_device

try:
    from typing import Sequence
    import usb_hid
except ImportError:
    pass


class Mouse:
    """Send USB HID mouse reports."""

    LEFT_BUTTON = 1
    """Left mouse button."""
    RIGHT_BUTTON = 2
    """Right mouse button."""
    MIDDLE_BUTTON = 4
    """Middle mouse button."""
    BACK_BUTTON = 8
    """Back mouse button."""
    FORWARD_BUTTON = 16
    """Forward mouse button."""

    def __init__(self, devices: Sequence[usb_hid.Device], timeout: int = None) -> None:
        self._mouse_device = find_device(
            devices, usage_page=0x1, usage=0x02, timeout=timeout
        )
        self.report = bytearray(4)

    def press(self, buttons: int) -> None:
        self.report[0] |= buttons
        self._send_no_move()

    def release(self, buttons: int) -> None:
        self.report[0] &= ~buttons
        self._send_no_move()

    def release_all(self) -> None:
        """Release all the mouse buttons."""
        self.report[0] = 0
        self._send_no_move()

    def click(self, buttons: int) -> None:
        self.press(buttons)
        self.release(buttons)

    def move(self, x: int = 0, y: int = 0, wheel: int = 0) -> None:
        # Send multiple reports if necessary to move or scroll requested amounts.
        while x != 0 or y != 0 or wheel != 0:
            partial_x = self._limit(x)
            partial_y = self._limit(y)
            partial_wheel = self._limit(wheel)
            self.report[1] = partial_x & 0xFF
            self.report[2] = partial_y & 0xFF
            self.report[3] = partial_wheel & 0xFF
            self._mouse_device.send_report(self.report)
            x -= partial_x
            y -= partial_y
            wheel -= partial_wheel

    def _send_no_move(self) -> None:
        """Send a button-only report."""
        self.report[1] = 0
        self.report[2] = 0
        self.report[3] = 0
        self._mouse_device.send_report(self.report)

    @staticmethod
    def _limit(dist: int) -> int:
        return min(127, max(-127, dist))
