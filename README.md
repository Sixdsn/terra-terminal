Terra Terminal Emulator
========

Terra is GTK+3.0 based terminal emulator with useful user interface, it also supports multiple terminals with splitting screen horizontally or vertically. New features will be added soon. It's very new and experimental project. I'ts written in python with python-gobject.

Terra is now able to be displayed on multi-screens at the same time.
You will get independant windows by screen.

Features added based on upstream (https://code.launchpad.net/~ozcanesen/terra/trunk):
- Use Terra Terminal on a multi-screen configuration
- Use multiple Terra Terminals on one screen
- Combine both configurations from above:
  * Multiple Terra Terminal on Multiple Screens
- Open a new Terra Terminal

- Start a specific program on each frame, saved in your layout.
- Save Tab Names correctly for all Apps.

Features to come:
- Save your layout configuration.
  * Working correctly but needs some adjustements

- Start a graphical program instead of a term program.
  * Might need much time if this is possible

If you want to contribute just checkout and try.
Feel free to open issues for bug report or new features.

Build and Install:
```
$> ./setup.py build
$> sudo ./setup install
```
You might need to specify --prefix=/usr/local on the install command if your version of python installed in /usr/local

