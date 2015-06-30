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

import sys, time

from gi.repository import Gtk

import terra.globalhotkeys

import terra.terra_utils as terra_utils
from terra.config import ConfigManager
from terra.dbusservice import DbusService
from terra.interfaces.terminal import TerminalWin


class TerminalWinContainer:
    def __init__(self):
        terra.globalhotkeys.init()
        tries = 0
        while True:
            try:
                self.hotkey = terra.globalhotkeys.GlobalHotkey()
            except SystemError as e:
                tries +=1
                if (tries >= 2):
                    raise Exception("Can't get GlobalHotkey instance")
                time.sleep(1)
            else:
                break

        global_key_string = ConfigManager.get_conf('shortcuts', 'global_key')
        if global_key_string:
            if not self.hotkey.bind(global_key_string, lambda w: self.show_hide()):
                raise Exception("Can't bind Global Keys: Another Instance of Terra is probably running")
        self.apps = []
        self.old_apps = []
        self.screen_id = 0
        self.on_doing = False
        self.is_running = False

    def show_hide(self):
        if not self.on_doing:
            self.on_doing = True
            for app in self.apps:
                app.show_hide()
            self.on_doing = False

    def update_ui(self):
        if not self.on_doing:
            self.on_doing = True
            for app in self.apps:
                app.update_ui()
            self.on_doing = False

    def get_screen_name(self):
        return str('layout-screen-%d' % self.screen_id)

    def save_conf(self):
        for app in self.apps:
            app.save_conf()
        for app in self.old_apps:
            app.save_conf(False)

    def app_quit(self):
        for app in self.apps:
            app.quit()
        sys.stdout.flush()
        sys.stderr.flush()
        if self.is_running:
            Gtk.main_quit()

    def remove_app(self, ext):
        if ext in self.apps:
            self.apps.remove(ext)
        self.old_apps.append(ext)
        if len(self.apps) == 0:
            self.app_quit()

    def create_app(self, screen_name='layout'):
        monitor = terra_utils.get_screen(screen_name)

        if screen_name == 'layout':
            screen_name = self.get_screen_name()

        if monitor is not None:
            app = TerminalWin(screen_name, monitor)
            app.hotkey = self.hotkey
            if len(self.apps) == 0:
                DbusService(app)
            self.apps.append(app)
            self.screen_id = max(self.screen_id, int(screen_name.split('-')[2])) + 1
        else:
            print('Cannot find {}'.format(screen_name))

    def get_apps(self):
        return self.apps

    def start(self):
        self.is_running = True
        Gtk.main()
