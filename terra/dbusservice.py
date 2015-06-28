# -*- coding: utf-8; -*-
"""
Copyright (C) 2013 - Ozcan ESEN <ozcanesen~gmail.com>

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

import dbus
import dbus.service
import dbus.glib

DBUS_PATH = '/org/terraterminal/RemoteControl'
DBUS_NAME = 'org.terraterminal.RemoteControl'


class DbusService(dbus.service.Object):
    def __init__(self, app):
        self.app = app
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(DBUS_NAME, bus=self.bus)
        super(DbusService, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def show_hide(self):
        self.app.show_hide()
