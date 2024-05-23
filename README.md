# Six Degrees of Syncopation

Six Degrees of Syncopation is a Spotify remote that tweaks song recommendations across six axes, using the Spacetec Spaceball 2003 six-degrees-of-freedom CAD mouse (circa 1991) as input.

## How does it work?

6DOS is a Python/Flask app that reads and parses USB HID reports from a Spaceball 2003 (converted from serial to USB via an Adafruit QT Py). 

Six axes of data (X, Y, Z, Rx, Ry, Rz) get converted to six Spotify audio features (danceability, energy, acousticness, duration, valence, popularity), nudging up (or down) the specified audio feature before requesting a recommendation from the Spotify Web API via spotipy.

The Spaceball's buttons control song recommendations based on the user's top tracks. We sort by date, filter for unique artists, and then use that track as the recommendation seed for a given button. The Spaceball's rezero button (hidden on the ball) is used for play/pause.

A simple WebGL visualization jiggles a cube and shifts its hue based on frequency and the specified axis / button.

## Further reading

 - [Six Degrees of Syncopation](https://thingswemake.com/six-degrees-of-syncopation/) blog write-up


## Also in the box

This project began with an effort to convert the Spaceball's serial input into USB HID, building off of vputz's prior art. Various iterations on a driver are included. Some require a custom build of CircuitPython, in which case the uf2 file is in the directory. The following experimental variants exist:

- 2D mouse (just x/y axes, and z for scroll)
- 8Bitdo (mimicks the USB HID report of an 8Bitdo SN30)
- PS4 Dualshock
- Spacemouse Pro (recognized by 3dconnexion's native drivers)
- Generic USB HID gamepad

The custom builds of CircuitPython were required to customize the product, manufacturer, version, VID and PID strings of the USB HID report. (Version is changed in line 92 of supervisor/shared/usb_desc.c where it's labeled bcdDevice; the other strings are in /ports/atmel-samd/boards/qtpy_m0/mpconfigboard.mk.) Also, the custom builds restore the CircuitPython default allowing six distinct USB HID reports (a limit of 1 is imposed via the stock build, due to memory limitations on the QT Py).

I've also included reference PDFs that helped me along my way (including the Spaceball's serial packet documentation) as well as a Python script that reads, parses and prints the content of each USB HID report.

## Acknowledgements

 - [Orbotron 9000](https://github.com/thingotron/orb9k_circuitpython) by vputz
 - [spaceball code fixes](https://github.com/abzman/spaceball-code-fixes) by abzman
 - [spaceball 2003 and a bit of pyserial](https://blog.adafruit.com/2022/04/14/spaceball-2003-and-a-bit-of-pyserial/) by ladyada
  - [playlist-viz](https://github.com/lilyszhang/playlist-viz) by lilyszhang
