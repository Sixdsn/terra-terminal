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

from gi.repository import Gtk

from terra.ConfigManager import ConfigManager

class VteObjectContainer(Gtk.HBox):
    counter = 0

    def __init__(self, parent, bare=False, progname=None, pwd=None):
        super(VteObjectContainer, self).__init__()

        if bare:
            return

        self.counter = 0
        self.parent = parent
        self.vte_list = []
        self.active_terminal = None

        if not progname:
            progname = ConfigManager.get_conf('general', 'start_shell_program')
        import terra.VteObject
        self.append_terminal(terra.VteObject.VteObject(), progname, pwd=pwd)

        self.pack_start(self.active_terminal, True, True, 0)
        self.show_all()

    def close_page(self):
        terminalwin = self.get_toplevel()
        for button in terminalwin.buttonbox:
            if button != terminalwin.radio_group_leader and button.get_active():
                return terminalwin.page_close(None, button)

    def append_terminal(self, term, progname, pwd=None, term_id=0):
        term.id = self.handle_id(term_id)
        term.set_pwd(self.active_terminal, pwd)
        term.fork_process(progname)
        self.active_terminal = term
        self.vte_list.append(self.active_terminal)

    def handle_id(self, setter=0):
        if setter != 0:
            ret_id = setter
        else:
            ret_id = self.counter
        self.counter = max(self.counter, setter) + 1
        return ret_id
