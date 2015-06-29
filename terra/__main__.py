# -*- coding: utf-8; -*-
"""
Copyright (C) 2013 - Arnaud SOURIOUX <six.dsn@gmail.com>
Copyright (C) 2012 - Ozcan ESEN <ozcanesen~gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>

"""

import os
import sys

# Disabled overlay scrollbars.
os.putenv('LIBOVERLAY_SCROLLBAR', '0')

from terra.config import ConfigManager
from terra.handler import TerraHandler
from terra.terminal import TerminalWinContainer

# Add the script root the the PYTHONPATH environment variable.
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(ROOT)


def main(project_root=ROOT):
    if len(sys.argv) > 1:
        sys.exit("Terra Doesn't support any argument")

    # Initialize the TerraHandler class variables.
    TerraHandler(project_root)
    ConfigManager()  # TODO: Initialization should not be required!

    TerraHandler.Wins = TerminalWinContainer()

    for section in ConfigManager.get_sections():
        if section.find('layout-screen-') != 0:
            continue

        if not ConfigManager.get_conf(section, 'disabled'):
            TerraHandler.Wins.create_app(section)

    if len(TerraHandler.Wins.get_apps()) == 0:
        TerraHandler.Wins.create_app()

    if len(TerraHandler.Wins.get_apps()) == 0:
        sys.exit('Cannot initiate any screen')

    TerraHandler.Wins.start()
