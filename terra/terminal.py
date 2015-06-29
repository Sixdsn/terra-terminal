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

import sys

from gi.repository import Gtk

import terra.globalhotkeys

import terra.terra_utils as terra_utils
from terra.config import ConfigManager
from terra.dbusservice import DbusService
from terra.interfaces.terminal import TerminalWin


class TerminalWinContainer:
    def __init__(self):
        terra.globalhotkeys.init()
        self.hotkey = terra.globalhotkeys.GlobalHotkey()

        global_key_string = ConfigManager.get_conf('shortcuts', 'global_key')
        if global_key_string:
            self.bind_success = self.hotkey.bind(global_key_string, lambda w: self.show_hide(), None)
        self.apps = []
        self.old_apps = []
        self.screenid = 0
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
        screenname = str('layout-screen-%d' % self.screenid)
        # TODO: Provide default values in the config manager.
        if ConfigManager.get_conf('layout', 'hide-tab-bar'):
            ConfigManager.set_conf(screenname, 'hide-tab-bar', True)
        else:
            ConfigManager.set_conf(screenname, 'hide-tab-bar', False)

        if ConfigManager.get_conf('layout', 'hide-tab-bar-fullscreen'):
            ConfigManager.set_conf(screenname, 'hide-tab-bar-fullscreen', True)
        else:
            ConfigManager.set_conf(screenname, 'hide-tab-bar-fullscreen', False)

        vertical_position = ConfigManager.get_conf('layout', 'vertical-position')
        if vertical_position:
            ConfigManager.set_conf(screenname, 'vertical-position', vertical_position)
        else:
            ConfigManager.set_conf(screenname, 'vertical-position', 150)

        horizontal_position = ConfigManager.get_conf('layout', 'horizontal-position')
        if horizontal_position:
            ConfigManager.set_conf(screenname, 'horizontal-position', horizontal_position)
        else:
            ConfigManager.set_conf(screenname, 'horizontal-position', 150)

        return screenname

    def save_conf(self):
        for app in self.apps:
            app.save_conf()
        for app in self.old_apps:
            app.save_conf(False)

    def app_quit(self):
        for app in self.apps:
            if not app.quit():
                return
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

    def create_app(self, screenName='layout'):
        if not self.bind_success:
            raise Exception("Can't bind Global Keys: Another Instance of Terra is probably running")
        monitor = terra_utils.get_screen(screenName)
        if screenName == 'layout':
            screenName = self.get_screen_name()
        if monitor is not None:
            app = TerminalWin(screenName, monitor)
            app.hotkey = self.hotkey
            if len(self.apps) == 0:
                DbusService(app)
            self.apps.append(app)
            self.screenid = max(self.screenid, int(screenName.split('-')[2])) + 1
        else:
            print("Cannot find %s"% screenName)

    def get_apps(self):
        return self.apps

    def start(self):
        self.is_running = True
        Gtk.main()
