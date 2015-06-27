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

from gi.repository import Gtk, Gdk

from terra.config import ConfigManager
from terra.handler import TerraHandler


class WinDialog:
    def __init__(self, sender, active_terminal):
        win_pref_ui_file = os.path.join(TerraHandler.get_resources_path(), 'ui/win_pref.ui')
        if not os.path.exists(win_pref_ui_file):
            msg = 'ERROR: UI data file is missing: {}'.format(win_pref_ui_file)
            sys.exit(msg)

        ConfigManager.disable_losefocus_temporary = True
        self.sender = sender
        self.active_terminal = active_terminal

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('terra')
        self.builder.add_from_file(win_pref_ui_file)
        self.dialog = self.builder.get_object('win_dialog')

        self.window = self.sender.get_container().parent
        self.dialog.v_align = self.builder.get_object('v_align')
        self.dialog.v_align.set_active(int(ConfigManager.get_conf(self.window.name, 'vertical-position')) / 50)

        self.dialog.h_align = self.builder.get_object('h_align')
        self.dialog.h_align.set_active(int(ConfigManager.get_conf(self.window.name, 'horizontal-position')) / 50)

        self.chk_hide_tab_bar = self.builder.get_object('chk_hide_tab_bar')
        self.chk_hide_tab_bar.set_active(ConfigManager.get_conf(self.window.name, 'hide-tab-bar'))

        self.chk_hide_tab_bar_fullscreen = self.builder.get_object('chk_hide_tab_bar_fullscreen')
        self.chk_hide_tab_bar_fullscreen.set_active(ConfigManager.get_conf(self.window.name, 'hide-tab-bar-fullscreen'))

        self.dialog.btn_cancel = self.builder.get_object('btn_cancel')
        self.dialog.btn_ok = self.builder.get_object('btn_ok')

        self.dialog.btn_cancel.connect('clicked', lambda w: self.close())
        self.dialog.btn_ok.connect('clicked', lambda w: self.update())

        self.dialog.connect('delete-event', lambda w, x: self.close())
        self.dialog.connect('destroy', lambda w: self.close())

        self.dialog.show_all()

    def on_keypress(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Return':
            self.update()

    def close(self):
        self.dialog.destroy()
        self.active_terminal.grab_focus()
        ConfigManager.disable_losefocus_temporary = False
        del self

    def update(self):
        ConfigManager.set_conf(self.window.name, 'vertical-position', self.dialog.v_align.get_active() * 50)
        ConfigManager.set_conf(self.window.name, 'horizontal-position', self.dialog.h_align.get_active() * 50)
        ConfigManager.set_conf(self.window.name, 'hide-tab-bar', self.chk_hide_tab_bar.get_active())
        ConfigManager.set_conf(self.window.name, 'hide-tab-bar-fullscreen', self.chk_hide_tab_bar_fullscreen.get_active())
        self.window.update_ui()
        ConfigManager.disable_losefocus_temporary = False
        self.close()
