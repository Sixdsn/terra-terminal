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
from terra.handlers import TerraHandler


class ProgDialog:
    def __init__(self, sender, active_terminal):
        terminal_ui_file = os.path.join(TerraHandler.get_resources_path(), 'terminal.ui')
        if not os.path.exists(terminal_ui_file):
            msg = 'ERROR: UI data file is missing: {}'.format(terminal_ui_file)
            sys.exit(msg)

        ConfigManager.disable_losefocus_temporary = True
        self.sender = sender
        self.active_terminal = active_terminal

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('terra')
        self.builder.add_from_file(terminal_ui_file)
        self.dialog = self.builder.get_object('progname_dialog')

        self.dialog.entry_new_progname = self.builder.get_object('progname-entry_new_name')
        if hasattr(self.sender, 'progname') and self.sender.progname:
            self.dialog.entry_new_progname.set_text(self.sender.progname)
        else:
            self.dialog.entry_new_progname.set_text("")

        self.dialog.btn_cancel = self.builder.get_object('progname-btn_cancel')
        self.dialog.btn_ok = self.builder.get_object('progname-btn_ok')

        self.dialog.btn_cancel.connect('clicked', lambda w: self.close())
        self.dialog.btn_ok.connect('clicked', lambda w: self.rename())
        self.dialog.entry_new_progname.connect('key-press-event', lambda w, x: self.on_keypress(w, x))

        self.dialog.connect('delete-event', lambda w, x: self.close())
        self.dialog.connect('destroy', lambda w: self.close())

        self.dialog.show_all()

    def on_keypress(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Return':
            self.rename()

    def close(self):
        self.dialog.destroy()
        self.active_terminal.grab_focus()
        ConfigManager.disable_losefocus_temporary = False
        del self

    def rename(self):
        self.sender.progname = self.dialog.entry_new_progname.get_text()
        self.sender.fork_process(self.sender.progname)
        ConfigManager.disable_losefocus_temporary = False
        self.close()
