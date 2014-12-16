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

from gi.repository import Gtk, Vte, GLib, Gdk, GdkX11, GObject
import os
import re

from preferences import Preferences
from config import ConfigManager
from terminal_dialog import ProgDialog
from win_dialog import WinDialog
from i18n import t

import threading

import terra_utils
import terra_main


# this regex strings taken from pantheon-terminal
# thanks munchor and voldyman
USERCHARS = "-[:alnum:]"
USERCHARS_CLASS = "[" + USERCHARS + "]"
PASSCHARS_CLASS = "[-[:alnum:]\\Q,?;.:/!%$^*&~\"#'\\E]"
HOSTCHARS_CLASS = "[-[:alnum:]]"
HOST = HOSTCHARS_CLASS + "+(\\." + HOSTCHARS_CLASS + "+)*"
PORT = "(?:\\:[[:digit:]]{1,5})?"
PATHCHARS_CLASS = "[-[:alnum:]\\Q_$.+!*,;@&=?/~#%\\E]"
PATHTERM_CLASS = "[^\\Q]'.}>) \t\r\n,\"\\E]"
SCHEME = """(?:news:|telnet:|nntp:|file:\/|https?:|ftps?:|sftp:|webcal:|irc:|sftp:|ldaps?:|nfs:|smb:|rsync:|ssh:|rlogin:|telnet:|git:|git\+ssh:|bzr:|bzr\+ssh:|svn:|svn\+ssh:|hg:|mailto:|magnet:)"""
USERPASS = USERCHARS_CLASS + "+(?:" + PASSCHARS_CLASS + "+)?"
URLPATH =  "(?:(/" + PATHCHARS_CLASS + "+(?:[(]" + PATHCHARS_CLASS + "*[)])*" + PATHCHARS_CLASS + "*)*" + PATHTERM_CLASS + ")?"

regex_strings =[SCHEME + "//(?:" + USERPASS + "\\@)?" + HOST + PORT + URLPATH,
    "(?:www|ftp)" + HOSTCHARS_CLASS + "*\\." + HOST + PORT + URLPATH,
    "(?:callto:|h323:|sip:)" + USERCHARS_CLASS + "[" + USERCHARS + ".]*(?:" + PORT + "/[a-z0-9]+)?\\@" + HOST,
    "(?:mailto:)?" + USERCHARS_CLASS + "[" + USERCHARS+ ".]*\\@" + HOSTCHARS_CLASS + "+\\." + HOST,
    "(?:news:|man:|info:)[[:alnum:]\\Q^_{|}~!\"#$%&'()*+,./;:=?`\\E]+"]

class VteObjectContainer(Gtk.HBox):
    def __init__(self, parent, bare=False, progname=ConfigManager.get_conf('general', 'start_shell_program'), pwd=None):
        super(VteObjectContainer, self).__init__()
        if not bare:
            self.parent = parent
            self.vte_list = []
            self.active_terminal = None
            self.append_terminal(VteObject(), progname, pwd=pwd)
            self.pack_start(self.active_terminal, True, True, 0)
            self.show_all()

    def close_page(self):
        terminalwin = self.get_toplevel()
        for button in terminalwin.buttonbox:
            if button != terminalwin.radio_group_leader and button.get_active():
                return terminalwin.page_close(None, button)

    def append_terminal(self, term, progname, pwd=None):
        term.set_pwd(self.active_terminal, pwd)
        term.fork_process(progname)
        self.active_terminal = term
        self.vte_list.append(self.active_terminal)

    @staticmethod
    def handle_id(setter=0):
        if not hasattr(VteObjectContainer.handle_id, "counter"):
            VteObjectContainer.handle_id.counter = 0
        if (setter != 0):
            ret_id = setter
        else:
            ret_id = VteObjectContainer.handle_id.counter
        VteObjectContainer.handle_id.counter = max(VteObjectContainer.handle_id.counter, setter) + 1
        return (ret_id)

class VteObject(Gtk.VBox):
    def __init__(self, term_id=0):
        super(Gtk.VBox, self).__init__()
        ConfigManager.add_callback(self.update_ui)

        self.id = VteObjectContainer.handle_id(term_id)
        self.parent = 0
        self.pwd = None
        self.pid = (0, 0)
        self.progname = ""

        self.title = Gtk.Label(terra_utils.get_running_cmd(self))
        self.title.set_line_wrap(True)
        self.pack_start(self.title, False, False, 0)

        self.hbox = Gtk.HBox()
        self.vte = Vte.Terminal()
        self.hbox.pack_start(self.vte, True, True, 0)
        self.vscroll = Gtk.VScrollbar(self.vte.get_vadjustment())
        self.hbox.pack_start(self.vscroll, False, False, 0)
        self.pack_start(self.hbox, True, True, 0)


        for regex_string in regex_strings:
            regex_obj = GLib.Regex.new(regex_string, 0, 0)
            tag = self.vte.match_add_gregex(regex_obj, 0)
            self.vte.match_set_cursor_type(tag, Gdk.CursorType.HAND2)

        self.vte.connect('scroll-event', self.scroll_event)
        self.vte.connect('child-exited', self.on_child_exited)
        self.vte.connect('button-release-event', self.on_button_release)
        self.vte.connect('increase-font-size', self.change_font_size, 0.1)
        self.vte.connect('decrease-font-size', self.change_font_size, -0.1)
        self.vte.connect('contents-changed', self.update_content)

        self.prefs = Preferences()
        self.update_ui()

    def update_content(self, widget):
        self.update_ui()

    def set_pwd(self, parent=None, pwd=None):
        if (parent):
            self.parent = parent.id
        start_directory = ConfigManager.get_conf('general', 'start_directory')
        if start_directory == '$home$':
            run_dir = os.environ['HOME']
        elif start_directory == '$pwd$':
            if (pwd):
                run_dir = pwd
            else:
                pid = None
                if (parent):
                    pid = parent.pid[1]
                elif (self.get_container()):
                    pid = terra_utils.get_paned_parent(self.get_container().vte_list, self.parent).pid[1]
                run_dir = terra_utils.get_pwd(pid)
                if (not run_dir):
                    run_dir = os.getcwd()
        else:
            run_dir = start_directory
        self.pwd = run_dir

    def fork_process(self, progname):
        if (not self.pwd):
            self.set_pwd()
        if (not progname):
            progname = ConfigManager.get_conf('general', 'start_shell_program')
        self.progname = progname

        if hasattr(self.vte, 'fork_command_full'):
            fork = self.vte.fork_command_full
        elif hasattr(self.vte, 'spawn_sync'):
            fork = self.vte.spawn_sync
        else:
            raise Exception('no symbols in libVte to fork program')

        self.pid = fork(
            Vte.PtyFlags.DEFAULT,
            self.pwd,
            self.progname.split(),
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None)

    def scroll_event(self, widget, event):
        if (Gdk.ModifierType.CONTROL_MASK & event.state) == Gdk.ModifierType.CONTROL_MASK:
            state, direction = event.get_scroll_direction()
            if state == False:
                return

            if direction == Gdk.ScrollDirection.UP:
                self.change_font_size(None, 0.1)
            elif direction == Gdk.ScrollDirection.DOWN:
                self.change_font_size(None, -0.1)

    def change_font_size(self, sender, factor):
        current_font = self.vte.get_font()
        current_size = current_font.get_size()
        factor = factor + 1
        new_size = int(current_size * factor)

        if new_size < 2048 or new_size > 60000:
            return

        current_font.set_size(new_size)
        self.vte.set_font(current_font)

    def on_child_exited(self, event):
        self.fork_process(ConfigManager.get_conf('general', 'start_shell_program'))

    def update_ui(self):
        if ConfigManager.get_conf('terminal', 'show_scrollbar'):
            self.vscroll.set_no_show_all(False)
        else:
            self.vscroll.set_no_show_all(True)
            self.vscroll.hide()

        if ConfigManager.get_conf('terminal', 'scrollback_unlimited'):
            self.vte.set_scrollback_lines(-1)
        else:
            self.vte.set_scrollback_lines(ConfigManager.get_conf('terminal', 'scrollback_lines'))

        self.vte.set_scroll_on_output(ConfigManager.get_conf('terminal', 'scroll_on_output'))

        self.vte.set_scroll_on_keystroke(ConfigManager.get_conf('terminal', 'scroll_on_keystroke'))

        if hasattr(self.vte, 'set_background_saturation'):
            self.vte.set_background_saturation(ConfigManager.get_conf('terminal', 'background_transparency') / 100.0)
        if hasattr(self.vte, 'set_background_transparent'):
            self.vte.set_background_transparent(ConfigManager.use_fake_transparency)
        if hasattr(self.vte, 'set_background_image_file'):
            self.vte.set_background_image_file(
                ConfigManager.get_conf('terminal', 'background_image'))

        transparency_value = int(ConfigManager.get_conf('terminal', 'background_transparency'))
        self.vte.set_opacity((100 - transparency_value) / 100.0 * 65535)

        if hasattr(self.vte, 'set_word_chars'):
            self.vte.set_word_chars(ConfigManager.get_conf('general', 'select_by_word'))

        try:
            self.vte.set_colors(
                Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_text')),
                Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_background')),
                [])
        except:
            alpha = (100 - transparency_value)/100.0
            bg = Gdk.RGBA.from_color(Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_background')))
            m = re.match(r'rgb\((\d+),(\d+),(\d+)\)', Gdk.RGBA.to_string(bg))
            Gdk.RGBA.parse(bg, 'rgba(' + m.group(1) + ',' + m.group(2) + ',' + m.group(3) + ',' + str(alpha) + ')')
            self.vte.set_colors(
                Gdk.RGBA.from_color(Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_text'))),
                bg,
                [])

        if not ConfigManager.get_conf('terminal', 'use_system_font'):
            self.vte.set_font_from_string(ConfigManager.get_conf('terminal', 'font_name'))
        if (self.pid != 0):
            self.title.set_label(terra_utils.get_running_cmd(self))

        self.show_all()

    def submenu_item_connect_hack(self, menu_item, callback, *args_for_callback):
        only_once = threading.Semaphore(1)

        def handle_event(menu_item, event=None):
            if only_once.acquire(False):
                GObject.idle_add(callback, *args_for_callback)

        menu_item.connect('button-press-event', handle_event)
        menu_item.connect('activate', handle_event)


    def on_button_release(self, widget, event):
        self.get_container().active_terminal = self

        self.matched_value = ''
        matched_string = self.vte.match_check(int(event.x / self.vte.get_char_width()), int(event.y / self.vte.get_char_height()))
        value, tag = matched_string

        if event.button == 3:
            self.menu = Gtk.Menu()
            self.menu.connect('deactivate', lambda w: setattr(ConfigManager, 'disable_losefocus_temporary', False))

            if value:
                self.menu_open_link = Gtk.MenuItem(t("Open Link"))
                self.menu_open_link.connect("activate", lambda w: Gtk.show_uri(self.get_screen(), value, GdkX11.x11_get_server_time(self.get_window())))
                self.menu.append(self.menu_open_link)

                self.menu_copy_link = Gtk.MenuItem(t("Copy Link Address"))
                self.menu_copy_link.connect("activate", lambda w: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(value, -1))
                self.menu.append(self.menu_copy_link)

                self.menu.append(Gtk.SeparatorMenuItem.new())

            else:
                self.menu_copy = Gtk.MenuItem(t("Copy"))
                self.menu_copy.connect("activate", lambda w: self.vte.copy_clipboard())
                self.menu.append(self.menu_copy)

                self.menu_paste = Gtk.MenuItem(t("Paste"))
                self.menu_paste.connect("activate", lambda w: self.vte.paste_clipboard())
                self.menu.append(self.menu_paste)


            self.menu_select_all = Gtk.MenuItem(t("Select All"))
            self.menu_select_all.connect("activate", lambda w: self.vte.select_all())
            self.menu.append(self.menu_select_all)

            self.menu.append(Gtk.SeparatorMenuItem.new())

            self.menu_v_split = Gtk.MenuItem(t("Split Vertical"))
            self.menu_v_split.connect("activate", self.split_axis, 'h')
            self.menu.append(self.menu_v_split)

            self.menu_h_split = Gtk.MenuItem(t("Split Horizontal"))
            self.menu_h_split.connect("activate", self.split_axis, 'v')
            self.menu.append(self.menu_h_split)

            self.term_menu = Gtk.Menu()

            self.term = Gtk.MenuItem(t("Terminals"))
            self.term.set_submenu(self.term_menu)

            self.menu_new = Gtk.MenuItem(t("New Terminal"))
            self.submenu_item_connect_hack(self.menu_new, self.new_app, self.menu_new)

            self.set_new_prog = Gtk.MenuItem(t("Set ProgName"))
            self.submenu_item_connect_hack(self.set_new_prog, self.save_progname, self.set_new_prog)

            self.reset_prog = Gtk.MenuItem(t("Reset Default Progname"))
            self.submenu_item_connect_hack(self.reset_prog, self.reset_progname, self.reset_prog)

            self.term_menu.append(self.menu_new)
            self.term_menu.append(self.set_new_prog)
            self.term_menu.append(self.reset_prog)
            self.menu.append(self.term)

            self.win_props = Gtk.MenuItem(t("Window Properties"))
            self.win_props.connect("activate", self.win_prefs)
            self.menu.append(self.win_props)

            self.menu_new = Gtk.MenuItem(t("Save Configuration"))
            self.menu_new.connect("activate", self.save_conf)
            self.menu.append(self.menu_new)

            self.menu_close = Gtk.MenuItem(t("Close"))
            self.menu_close.connect("activate", self.close_node)
            self.menu.append(self.menu_close)

            self.menu.append(Gtk.SeparatorMenuItem.new())

            self.menu_preferences = Gtk.MenuItem(t("Preferences"))
            self.menu_preferences.connect("activate", self.open_preferences)
            self.menu.append(self.menu_preferences)

            self.menu_quit = Gtk.MenuItem(t("Quit"))
            self.menu_quit.connect("activate", lambda w: self.get_toplevel().exit())
            self.menu.append(self.menu_quit)

            self.menu.show_all()

            ConfigManager.disable_losefocus_temporary = True
            self.menu.popup(None, None, None, None, event.button, event.time)
        elif value:
            Gtk.show_uri(self.get_screen(), value, GdkX11.x11_get_server_time(self.get_window()))

    def save_progname(self, widget):
        ConfigManager.disable_losefocus_temporary = True
        ProgDialog(self, self)

    def win_prefs(self, widget):
        ConfigManager.disable_losefocus_temporary = True
        WinDialog(self, self)

    def reset_progname(self, widget):
        self.progname = ConfigManager.get_conf('general', 'start_shell_program')
        self.fork_process(self.progname)

    def new_app(self, widget):
        terra_main.create_app()

    def save_conf(self, widget):
        terra_main.save_conf()

    def open_preferences(self, widget):
        ConfigManager.disable_losefocus_temporary = True
        self.prefs.show()

    def close_node(self, widget):
        parent = self.get_parent()

        if (self in self.get_container().vte_list):
            self.get_container().vte_list.remove(self)
        else:
            print("Issue Close Node")

        if type(parent) == VteObjectContainer:
            return self.get_container().close_page()

        container = parent

        while type(container) != VteObjectContainer:
            container = container.get_parent()

        if parent.get_child1() == self:
            sibling = parent.get_child2()
        else:
            sibling = parent.get_child1()

        ConfigManager.remove_callback(self.update_ui)
        parent.remove(sibling)
        top_level = parent.get_parent()

        if type(top_level) == VteObjectContainer:
            top_level.remove(parent)
            top_level.pack_start(sibling, True, True, 0)
        else:
            if top_level.get_child1() == parent:
                top_level.remove(parent)
                top_level.pack1(sibling, True, True)
            else:
                top_level.remove(parent)
                top_level.pack2(sibling, True, True)

        while type(sibling) != VteObject:
            sibling = sibling.get_child1()

        container.active_terminal = sibling
        sibling.grab_focus()

    def get_container(self):
        container = self.get_parent()
        while type(container) != VteObjectContainer and container:
            container = container.get_parent()
        return container

    def split_axis(self, widget, axis='h', split=-1, progname=None, term_id=0, pwd=None):
        parent = self.get_parent()

        if type(parent) != VteObjectContainer:
            if parent.get_child1() == self:
                mode = 1
            else:
                mode = 2
        else:
            mode = 0

        display = self.get_allocation()
        if axis == 'h':
            paned = Gtk.HPaned()
            size = display.width
            if split == -1:
                split = self.get_allocation().width / 2
            else:
                split = size * split / 10000
        elif axis == 'v':
            paned = Gtk.VPaned()
            size = display.height
            if split == -1:
                split = self.get_allocation().height / 2
            else:
                split = size * split / 10000
        paned.set_position(split)

        parent.remove(self)
        new_terminal = VteObject(term_id=term_id)
        new_terminal.parent = self.id
        paned.pack1(self, True, False)
        paned.pack2(new_terminal, True, False)
        paned.show_all()

        if mode == 0:
            parent.pack_start(paned, True, True, 0)
        elif mode == 1:
            parent.pack1(paned, True, False)
        else:
            parent.pack2(paned, True, False)

        self.get_container().append_terminal(new_terminal, progname, pwd)
        parent.show_all()
        new_terminal.grab_focus()


    # direction
    # 1 = up (default)
    # 2 = down
    # 3 = left
    # 4 = right
    def move(self, direction=1):
        child = self
        parent = self.get_parent()
        vpath, hpath = [], []
        while True:
            if type(parent) == VteObjectContainer:
                break

            if type(parent) == Gtk.VPaned:
                if parent.get_child1() == child:
                    vpath.append(1)
                else:
                    vpath.append(2)
            elif type(parent) == Gtk.HPaned:
                if parent.get_child1() == child:
                    hpath.append(1)
                else:
                    hpath.append(2)

            child = parent
            parent = parent.get_parent()

        if direction == 1:
            changed = False
            new_vpath = []
            for i in vpath:
                if i == 1 and changed:
                    new_vpath.append(1)
                elif i == 2:
                    if not changed:
                        new_vpath.append(1)
                        changed = True
                    else:
                        new_vpath.append(2)

            vpath = new_vpath[::-1]
            hpath = hpath[::-1]
        elif direction == 2:
            changed = False
            new_vpath = []
            for i in vpath:
                if i == 2 and changed:
                    new_vpath.append(2)
                elif i == 1:
                    if not changed:
                        new_vpath.append(2)
                        changed = True
                    else:
                        new_vpath.append(1)

            vpath = new_vpath[::-1]
            hpath = hpath[::-1]
        elif direction == 3:
            changed = False
            new_hpath = []
            for i in hpath:
                if i == 1 and changed:
                    new_hpath.append(1)
                elif i == 2:
                    if not changed:
                        new_hpath.append(1)
                        changed = True
                    else:
                        new_hpath.append(2)
            vpath = vpath[::-1]
            hpath = new_hpath[::-1]
        elif direction == 4:
            changed = False
            new_hpath = []
            for i in hpath:
                if i == 2 and changed:
                    new_hpath.append(2)
                elif i == 1:
                    if not changed:
                        new_hpath.append(2)
                        changed = True
                    else:
                        new_hpath.append(1)

            hpath = new_hpath[::-1]
            vpath = vpath[::-1]

        if direction < 3 and vpath == []:
            return
        elif direction > 2 and hpath == []:
            return

        obj = parent.get_children()[0]

        while type(obj) != VteObject:
            if type(obj) == Gtk.VPaned:
                if len(vpath) == 0:
                    if direction == 1:
                        obj = obj.get_child2()
                    else:
                        obj = obj.get_child1()
                else:
                    pick = vpath[0]
                    vpath = vpath[1:]

                    if pick == 1:
                        obj = obj.get_child1()
                    else:
                        obj = obj.get_child2()
            elif type(obj) == Gtk.HPaned:
                if len(hpath) == 0:
                    if direction == 3:
                        obj = obj.get_child2()
                    else:
                        obj = obj.get_child1()
                else:
                    pick = hpath[0]
                    hpath = hpath[1:]

                    if pick == 1:
                        obj = obj.get_child1()
                    else:
                        obj = obj.get_child2()

        obj.grab_focus()
        self.get_container().active_terminal = obj

    def grab_focus(self):
        self.vte.grab_focus()

    def select_all(self):
        self.vte.select_all()

    def copy_clipboard(self):
        self.vte.copy_clipboard()

    def paste_clipboard(self):
        self.vte.paste_clipboard()
