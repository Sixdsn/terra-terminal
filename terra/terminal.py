#!/usr/bin/python
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

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GdkX11

import terra.globalhotkeys
import terra.terra_utils as terra_utils
from terra.config import ConfigManager
from terra.dbusservice import DbusService
from terra.handler import TerraHandler
from terra.i18n import t
from terra.rename_dialog import RenameDialog
from terra.VteObject import VteObjectContainer, VteObject


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
        if self.on_doing == False:
            self.on_doing = True
            for app in self.apps:
                app.show_hide()
            self.on_doing = False

    def update_ui(self):
        if self.on_doing == False:
            self.on_doing = True
            for app in self.apps:
                app.update_ui()
            self.on_doing = False

    def get_screen_name(self):
        screenname = str('layout-screen-%d' % self.screenid)

        if ConfigManager.get_conf('layout', 'hide-tab-bar'):
            ConfigManager.set_conf(screenname, 'hide-tab-bar', True)
        else:
            ConfigManager.set_conf(screenname, 'hide-tab-bar', False)

        if ConfigManager.get_conf('layout', 'hide-tab-bar-fullscreen'):
            ConfigManager.set_conf(screenname, 'hide-tab-bar-fullscreen', True)
        else:
            ConfigManager.set_conf(screenname, 'hide-tab-bar-fullscreen', False)

        if ConfigManager.get_conf('layout', 'vertical-position'):
            ConfigManager.set_conf(screenname, 'vertical-position', vertical_position)
        else:
            ConfigManager.set_conf(screenname, 'vertical-position', 150)

        if ConfigManager.get_conf('layout', 'horizontal-position'):
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
            if (app.quit() == False):
                return
        sys.stdout.flush()
        sys.stderr.flush()
        if (self.is_running):
            Gtk.main_quit()

    def remove_app(self, ext):
        if ext in self.apps:
            self.apps.remove(ext)
        self.old_apps.append(ext)
        if (len(self.apps) == 0):
            self.app_quit()

    def create_app(self, screenName='layout'):
        monitor = terra_utils.get_screen(screenName)
        if (screenName == 'layout'):
            screenName = self.get_screen_name()
        if (monitor != None):
            app = TerminalWin(screenName, monitor)
            if (not self.bind_success):
                terra_utils.cannot_bind(app)
                raise Exception("Can't bind Global Keys")
            app.hotkey = self.hotkey
            if (len(self.apps) == 0):
                DbusService(app)
            self.apps.append(app)
            self.screenid = max(self.screenid, int(screenName.split('-')[2])) + 1
        else:
            print("Cannot find %s"% screenName)

    def get_apps(self):
        return (self.apps)

    def start(self):
        self.is_running = True
        Gtk.main()

class TerminalWin(Gtk.Window):
    def __init__(self, name, monitor):
        main_ui_file = os.path.join(TerraHandler.get_resources_path(), 'ui/main.ui')
        if not os.path.exists(main_ui_file):
            msg = 'ERROR: UI data file is missing: {}'.format(main_ui_file)
            sys.exit(msg)

        super(TerminalWin, self).__init__()

        self.set_keep_above(True)

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('terra')
        self.builder.add_from_file(main_ui_file)

        self.name = name
        self.screen_id = int(name.split('-')[2])
        # Allow UI to be updated by other events.
        TerraHandler.add_ui_event_handler(self.update_ui)

        self.screen = self.get_screen()
        self.screen.connect('monitors-changed', self.check_visible)
        self.monitor = monitor

        self.init_transparency()
        self.init_ui()
        self.update_ui()

        if not ConfigManager.get_conf('general', 'hide_on_start'):
            self.show_all()
        self.paned_childs = []

    def init_ui(self):
        self.set_title(t('Terra Terminal Emulator'))

        if ConfigManager.get_conf(self.name, 'fullscreen'):
            self.is_fullscreen = True
        else:
            self.is_fullscreen = False

        self.slide_effect_running = False
        self.losefocus_time = 0
        self.set_has_resize_grip(False)

        self.resizer = self.builder.get_object('resizer')
        self.resizer.unparent()
        self.resizer.connect('motion-notify-event', self.on_resize)
        self.resizer.connect('button-release-event', self.update_resizer)

        self.logo = self.builder.get_object('logo')
        logo_path = os.path.join(TerraHandler.get_resources_path(), 'terra.svg')
        self.logo_buffer = GdkPixbuf.Pixbuf.new_from_file_at_size(logo_path, 32, 32)
        self.logo.set_from_pixbuf(self.logo_buffer)

        self.set_icon(self.logo_buffer)

        self.notebook = self.builder.get_object('notebook')
        self.notebook.set_name('notebook')

        self.tabbar = self.builder.get_object('tabbar')
        self.buttonbox = self.builder.get_object('buttonbox')

        # radio group leader, first and hidden object of buttonbox
        # keeps all other radio buttons in a group
        self.radio_group_leader = Gtk.RadioButton()
        self.buttonbox.pack_start(self.radio_group_leader, False, False, 0)
        self.radio_group_leader.set_no_show_all(True)

        self.new_page = self.builder.get_object('btn_new_page')
        self.new_page.connect('clicked', lambda w: self.add_page())

        self.btn_fullscreen = self.builder.get_object('btn_fullscreen')
        self.btn_fullscreen.connect('clicked', lambda w: self.toggle_fullscreen())

        self.connect('destroy', lambda w: self.quit())
        self.connect('delete-event', lambda w, x: self.quit())
        self.connect('key-press-event', self.on_keypress)
        self.connect('focus-out-event', self.on_window_losefocus)
        self.connect('configure-event', self.on_window_move)
        self.add(self.resizer)

        self.set_default_size(self.monitor.width, self.monitor.height)

        added = False
        for section in ConfigManager.get_sections():
            tabs = str('layout-Tabs-%d'% self.screen_id)
            if (section.find(tabs) == 0 and not ConfigManager.get_conf(section, 'disabled')):
                self.add_page(page_name=str(section))
                added = True
        if (not added):
            self.add_page()

        for button in self.buttonbox:
            if button == self.radio_group_leader:
                continue
            else:
                button.set_active(True)
                break

    def check_visible(self):
        if (not terra_utils.is_on_visible_screen(self)):
            active_monitor = self.screen.get_monitor_workarea(self.screen.get_primary_monitor())
            terra_utils.set_new_size(self, active_monitor, self.monitor)

    def on_window_losefocus(self, window, event):
        if self.slide_effect_running:
            return
        if ConfigManager.disable_losefocus_temporary:
            return
        if not ConfigManager.get_conf('window', 'hide_on_losefocus'):
            return

        if self.get_property('visible'):
            self.losefocus_time = GdkX11.x11_get_server_time(self.get_window())
            if ConfigManager.get_conf('window', 'use_animation'):
                self.slide_up()
            self.unrealize()
            self.hide()

    def on_window_move(self, window, event):
        winpos = self.get_position()
        if not self.is_fullscreen and winpos[0] > 0 and winpos[1] > 0:
            self.monitor.x = winpos[0]
            self.monitor.y = winpos[1]
            ConfigManager.set_conf(self.name, 'posx', winpos[0])
            ConfigManager.set_conf(self.name, 'posy', winpos[1])

    def exit(self):
        if ConfigManager.get_conf('general', 'prompt_on_quit'):
            ConfigManager.disable_losefocus_temporary = True
            msgtext = t("Do you really want to quit?")
            msgbox = Gtk.MessageDialog(self, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, msgtext)
            response = msgbox.run()
            msgbox.destroy()
            ConfigManager.disable_losefocus_temporary = False

            if response != Gtk.ResponseType.YES:
                return False

        TerraHandler.Wins.app_quit()

    def save_conf(self, keep=True):
        tabs = str('layout-Tabs-%d'% self.screen_id)
        if (not keep):
            for section in ConfigManager.get_sections():
                if (section.find(tabs) == 0):
                    ConfigManager.del_conf(section)
            ConfigManager.del_conf(self.name)
        else:
            ConfigManager.set_conf(self.name, 'width', self.monitor.width)
            ConfigManager.set_conf(self.name, 'height', self.monitor.height)
            ConfigManager.set_conf(self.name, 'fullscreen', self.is_fullscreen)

            #we delete all tabs first to avoid unused
            #we delete all layouts first to avoid unused
            for section in ConfigManager.get_sections():
                if (section.find("layout-Tabs-%d"% (self.screen_id)) == 0):
                    # we won't delete those who are set as disabled
                    if not ConfigManager.get_conf(section, 'disabled'):
                        ConfigManager.del_conf(section)
                if (section.find("layout-Child-%d"% (self.screen_id)) == 0):
                    ConfigManager.del_conf(section)

            #We add them all
            tabid = 0
            for button in self.buttonbox:
                if button != self.radio_group_leader:
                    section = str('layout-Tabs-%d-%d'% (self.screen_id, tabid))
                    ConfigManager.set_conf(section, 'name', button.get_label())
                    tabid = tabid + 1

            tabid = 0
            for container in self.notebook.get_children():
                childid = 0
                self.set_paned_parents(container)
                for child in terra_utils.my_sorted(container.vte_list):
                    section = str('layout-Child-%d-%d-%d'% (self.screen_id, tabid, childid))
                    print("Id: %d ParId: %d Pos: %d"% (child.id, child.parent, child.pos))
                    ConfigManager.set_conf(section, 'id', child.id)
                    ConfigManager.set_conf(section, 'parent', child.parent)
                    ConfigManager.set_conf(section, 'axis', child.axis)
                    ConfigManager.set_conf(section, 'pos', child.pos)
                    ConfigManager.set_conf(section, 'prog', child.progname)
                    ConfigManager.set_conf(section, 'pwd', child.pwd)
                    childid += 1
                tabid = tabid + 1

        ConfigManager.save_config()

    def use_child(self, child, parent, axis, pos):
        child.pos = -1
        child.axis = axis
        child.pwd = terra_utils.get_pwd(child.pid[1])
        if (parent):
            child.pos = pos
            child.parent = parent.id

    #there is a very small issue if the tabbar is visible
    def get_paned_pos(self, tree):
        pos = tree.get_position()
        if isinstance(tree, Gtk.HPaned):
            size = tree.get_allocation().width
        else:
            size = tree.get_allocation().height
        percentage = int(float(pos) / float(size) * float(10000))
        return (percentage)

    def rec_parents(self, tree, container):
        if not tree:
            TerminalWin.rec_parents.im_func._parent = None
            TerminalWin.rec_parents.im_func._first_child = None
            TerminalWin.rec_parents.im_func._axis = 'v'
            TerminalWin.rec_parents.im_func._pos = -1
            return None

        if isinstance(tree, Gtk.Paned):
            child1 = tree.get_child1()
            child2 = tree.get_child2()
            if (child1):
                if (isinstance(child1, Gtk.Paned)):
                    TerminalWin.rec_parents.im_func._pos = self.get_paned_pos(tree)
                    self.rec_parents(child1, container)
                if isinstance(child1, VteObject):
                    if not terra_utils.get_paned_parent(container.vte_list, child1.parent):
                        self.use_child(child1, TerminalWin.rec_parents.im_func._parent, TerminalWin.rec_parents.im_func._axis, TerminalWin.rec_parents.im_func._pos)
                    else:
                        self.use_child(child1, terra_utils.get_paned_parent(container.vte_list, child1.parent), TerminalWin.rec_parents.im_func._axis, TerminalWin.rec_parents.im_func._pos)
                    if not TerminalWin.rec_parents.im_func._first_child:
                        if child1 in container.vte_list:
                            container.vte_list.remove(child1)
                        if len(container.vte_list) and container.vte_list[0].id == 0:
                            container.vte_list.pop(0)
                        for item in container.vte_list:
                            if (item.parent == child1.id):
                                item.parent = 0
                        child1.id = 0
                        child1.parent = 0
                        container.vte_list.append(child1)
                        TerminalWin.rec_parents.im_func._first_child = child1
                    TerminalWin.rec_parents.im_func._parent = child1
            if (child2):
                if isinstance(tree, Gtk.HPaned):
                    TerminalWin.rec_parents.im_func._axis = 'h'
                else:
                    TerminalWin.rec_parents.im_func._axis = 'v'
                if (isinstance(child2, Gtk.Paned)):
                    TerminalWin.rec_parents.im_func._pos = self.get_paned_pos(tree)
                    self.rec_parents(child2, container)
                if isinstance(child2, VteObject):
                    if not terra_utils.get_paned_parent(container.vte_list, child2.parent):
                        self.use_child(child2, TerminalWin.rec_parents.im_func._parent, TerminalWin.rec_parents.im_func._axis, self.get_paned_pos(tree))
                    else:
                        self.use_child(child2, terra_utils.get_paned_parent(container.vte_list, child2.parent), TerminalWin.rec_parents.im_func._axis, self.get_paned_pos(tree))

        elif not TerminalWin.rec_parents.im_func._first_child and isinstance(tree, VteObject):
            if tree in container.vte_list:
                container.vte_list.remove(tree)
            if len(container.vte_list) and container.vte_list[0].id == 0:
                container.vte_list.pop(0)
            tree.id = 0
            tree.parent = 0
            tree.pos = -1
            tree.axis = 'v'
            container.vte_list.append(tree)
            TerminalWin.rec_parents.im_func._first_child = tree

    def set_paned_parents(self, container):
        self.rec_parents(None, None)
        for tree in container.get_children():
            self.rec_parents(tree, container)

    def quit(self):
        TerraHandler.remove_ui_event_handler(self.update_ui)
        ConfigManager.save_config()
        TerraHandler.Wins.remove_app(self)
        self.destroy()

    def on_resize(self, widget, event):
        if Gdk.ModifierType.BUTTON1_MASK & event.get_state() != 0:
            mouse_y = event.device.get_position()[2]
            new_height = mouse_y - self.get_position()[1]
            mouse_x = event.device.get_position()[1]
            new_width = mouse_x - self.get_position()[0]
            if new_height > 0 and new_width > 0:
                self.monitor.height = new_height
                self.monitor.width = new_width
                self.resize(self.monitor.width, self.monitor.height)
                self.show()

    def update_resizer(self, widget, event):
        self.resizer.set_position(self.monitor.height)
        self.resizer.set_position(self.monitor.width)
        self.resizer.set_property('position', int(self.monitor.height))
        self.resizer.queue_resize()

    def add_page(self, page_name=None):
        container = None
        if (page_name):
            section=str('layout-Child-%s-0'%(page_name[len('layout-Tabs-'):]))
            progname = ConfigManager.get_conf(section, 'prog')
            pwd = ConfigManager.get_conf(section, 'pwd')
            container = VteObjectContainer(self, progname=progname, pwd=pwd)
        if (not container):
            container = VteObjectContainer(self)

        self.notebook.append_page(container, None)
        self.notebook.set_current_page(-1)
        self.get_active_terminal().grab_focus()

        page_count = 0
        for button in self.buttonbox:
            if button != self.radio_group_leader:
                page_count += 1

        tab_name = ConfigManager.get_conf(page_name, 'name')
        if page_name == None or tab_name == None:
            tab_name = t("Terminal ") + str(page_count+1)

        new_button = Gtk.RadioButton.new_with_label_from_widget(self.radio_group_leader, tab_name)
        new_button.set_property('draw-indicator', False)
        new_button.set_active(True)
        new_button.show()
        new_button.connect('toggled', self.change_page)
        new_button.connect('button-release-event', self.page_button_mouse_event)

        self.buttonbox.pack_start(new_button, False, True, 0)

        self.update_ui()

        if page_name:
            for section in ConfigManager.get_sections():
                child = str('layout-Child-%s'%(page_name[len('layout-Tabs-'):]))
                if (section.find(child) == 0 and section[-1:] != '0'):
                    axis = ConfigManager.get_conf(section, "axis")[0]
                    prog = ConfigManager.get_conf(section, "prog")
                    pos = ConfigManager.get_conf(section, "pos")
                    pwd = ConfigManager.get_conf(section, "pwd")
                    term_id = int(ConfigManager.get_conf(section, "id"))
                    parent_vte = terra_utils.get_paned_parent(container.vte_list, int(ConfigManager.get_conf(section, "parent")))
                    parent_vte.split_axis(parent_vte, axis=axis, split=pos, progname=prog, term_id=term_id, pwd=pwd)
                    self.update_ui()

    def get_active_terminal(self):
        return self.notebook.get_nth_page(self.notebook.get_current_page()).active_terminal

    def change_page(self, button):
        if button.get_active() == False:
            return

        page_no = 0
        for i in self.buttonbox:
            if i != self.radio_group_leader:
                if i == button:
                    self.notebook.set_current_page(page_no)
                    self.get_active_terminal().grab_focus()
                    return
                page_no = page_no + 1

    def page_button_mouse_event(self, button, event):
        if event.button != 3:
            return

        self.menu = self.builder.get_object('page_button_menu')
        self.menu.connect('deactivate', lambda w: setattr(ConfigManager, 'disable_losefocus_temporary', False))

        self.menu_close = self.builder.get_object('menu_close')
        self.menu_rename = self.builder.get_object('menu_rename')

        try:
            self.menu_rename.disconnect(self.menu_rename_signal)
            self.menu_close.disconnect(self.menu_close_signal)

            self.menu_close_signal = self.menu_close.connect('activate', self.page_close, button)
            self.menu_rename_signal = self.menu_rename.connect('activate', self.page_rename, button)
        except:
            self.menu_close_signal = self.menu_close.connect('activate', self.page_close, button)
            self.menu_rename_signal = self.menu_rename.connect('activate', self.page_rename, button)

        self.menu.show_all()

        ConfigManager.disable_losefocus_temporary = True
        self.menu.popup(None, None, None, None, event.button, event.time)
        self.get_active_terminal().grab_focus()

    def page_rename(self, menu, sender):
        RenameDialog(sender, self.get_active_terminal())

    def page_close(self, menu, sender):
        button_count = len(self.buttonbox.get_children())

        # don't forget "radio_group_leader"
        if button_count <= 2:
            if (ConfigManager.get_conf('general', 'spawn_term_on_last_close')):
                self.add_page()
            else:
                return self.quit()

        page_no = 0
        for i in self.buttonbox:
            if i != self.radio_group_leader:
                if i == sender:
                    self.notebook.remove_page(page_no)
                    self.buttonbox.remove(i)

                    last_button = self.buttonbox.get_children()[-1]
                    last_button.set_active(True)
                    return True
                page_no = page_no + 1

    def get_screen_rectangle(self):
        display = self.screen.get_display()
        return self.screen.get_monitor_workarea(self.screen.get_monitor_at_point(self.monitor.x, self.monitor.y))

    # @TODO: Cleanup!
    def update_ui(self):
        self.unmaximize()
        self.stick()
        self.override_gtk_theme()
        self.set_keep_above(ConfigManager.get_conf('window', 'always_on_top'))
        self.set_decorated(ConfigManager.get_conf('window', 'use_border'))
        self.set_skip_taskbar_hint(ConfigManager.get_conf('general', 'hide_from_taskbar'))

        #hide/show tabbar
        if ConfigManager.get_conf(self.name, 'hide-tab-bar'):
            self.tabbar.hide()
            self.tabbar.set_no_show_all(True)
        else:
            self.tabbar.set_no_show_all(False)
            self.tabbar.show()

        self.check_visible()

        if self.is_fullscreen:
            win_rect = self.get_screen_rectangle()
            self.reshow_with_initial_size()
            self.move(win_rect.x, win_rect.y)
            self.fullscreen()

            # hide resizer
            if self.resizer.get_child2() != None:
                self.resizer.remove(self.resizer.get_child2())

            # hide tab bar
            if ConfigManager.get_conf(self.name, 'hide-tab-bar-fullscreen'):
                self.tabbar.set_no_show_all(True)
                self.tabbar.hide()
        else:
            # show resizer
            if self.resizer.get_child2() == None:
                self.resizer.add2(Gtk.Box())
                self.resizer.get_child2().show_all()

            vertical_position = self.monitor.y
            horizontal_position = self.monitor.x
            screen_rectangle = self.get_screen_rectangle()
            vert = ConfigManager.get_conf(self.name, 'vertical-position')
            if vert != None and vert <= 100:
                height = self.monitor.height
                vertical_position = vert * screen_rectangle.height / 100
                #top
                if vertical_position - (height / 2) < 0:
                    vertical_position = screen_rectangle.y + 0
                #bottom
                elif vertical_position + (height / 2) > screen_rectangle.height:
                    vertical_position = screen_rectangle.y + screen_rectangle.height - height
                #center
                else:
                    vertical_position = screen_rectangle.y + vertical_position - (height / 2)

            horiz = ConfigManager.get_conf(self.name, 'horizontal-position')
            if horiz != None and horiz <= 100:
                width = self.monitor.width - 1
                horizontal_position = horiz * screen_rectangle.width / 100
                #left
                if horizontal_position - (width / 2) < 0:
                    horizontal_position = screen_rectangle.x + 0
                #right
                elif horizontal_position + (width / 2) > screen_rectangle.width:
                    horizontal_position = screen_rectangle.x + screen_rectangle.width - width
                #center
                else:
                    horizontal_position = screen_rectangle.x + horizontal_position - (width / 2)
            self.unfullscreen()
            self.reshow_with_initial_size()
            self.resize(self.monitor.width, self.monitor.height)
            self.move(horizontal_position, vertical_position)

    def override_gtk_theme(self):
        css_provider = Gtk.CssProvider()

        bg = Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_background'))
        bg_hex =  '#%02X%02X%02X' % (int((bg.red/65536.0)*256), int((bg.green/65536.0)*256), int((bg.blue/65536.0)*256))

        css_provider.load_from_data('''
            #notebook GtkPaned {
                -GtkPaned-handle-size: %i;
            }
            GtkVScrollbar {
                -GtkRange-slider-width: 5;
            }
            GtkVScrollbar.trough {
                background-image: none;
                background-color: %s;
                border-width: 0;
                border-radius: 0;
            }
            GtkVScrollbar.slider, GtkVScrollbar.slider:prelight, GtkVScrollbar.button {
                background-image: none;
                border-width: 0;
                background-color: alpha(#FFF, 0.4);
                border-radius: 10px;
                box-shadow: none;
            }
            ''' % (ConfigManager.get_conf('general', 'separator_size'), bg_hex))

        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(self.screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def on_keypress(self, widget, event):
        if ConfigManager.key_event_compare('toggle_scrollbars_key', event):
            # Toggle value
            ConfigManager.set_conf('terminal', 'show_scrollbar', not ConfigManager.get_conf('terminal', 'show_scrollbar'))
            ConfigManager.save_config()
            TerraHandler.execute_ui_event_handlers()
            return True

        if ConfigManager.key_event_compare('move_up_key', event):
            self.get_active_terminal().move(direction=1)
            return True

        if ConfigManager.key_event_compare('move_down_key', event):
            self.get_active_terminal().move(direction=2)
            return True

        if ConfigManager.key_event_compare('move_left_key', event):
            self.get_active_terminal().move(direction=3)
            return True

        if ConfigManager.key_event_compare('move_right_key', event):
            self.get_active_terminal().move(direction=4)
            return True

        if ConfigManager.key_event_compare('move_left_screen_key', event):
            terra_utils.move_left_screen(self)
            return True

        if ConfigManager.key_event_compare('move_right_screen_key', event):
            terra_utils.move_right_screen(self)
            return True

        if ConfigManager.key_event_compare('quit_key', event):
            self.quit()
            return True

        if ConfigManager.key_event_compare('select_all_key', event):
            self.get_active_terminal().select_all()
            return True

        if ConfigManager.key_event_compare('copy_key', event):
            self.get_active_terminal().copy_clipboard()
            return True

        if ConfigManager.key_event_compare('paste_key', event):
            self.get_active_terminal().paste_clipboard()
            return True

        if ConfigManager.key_event_compare('split_v_key', event):
            self.get_active_terminal().split_axis(None, 'h')
            return True

        if ConfigManager.key_event_compare('split_h_key', event):
            self.get_active_terminal().split_axis(None, 'v')
            return True

        if ConfigManager.key_event_compare('close_node_key', event):
            self.get_active_terminal().close_node(None)
            return True

        if ConfigManager.key_event_compare('fullscreen_key', event):
            self.toggle_fullscreen()
            return True

        if ConfigManager.key_event_compare('new_page_key', event):
            self.add_page()
            return True

        if ConfigManager.key_event_compare('rename_page_key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_rename(None, button)
                    return True

        if ConfigManager.key_event_compare('close_page_key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_close(None, button)
                    return True

        if ConfigManager.key_event_compare('next_page_key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if (page_button_list[i].get_active() == True):
                    if (i + 1 < len(page_button_list)):
                        page_button_list[i+1].set_active(True)
                    else:
                        page_button_list[0].set_active(True)
                    return True


        if ConfigManager.key_event_compare('prev_page_key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if page_button_list[i].get_active():
                    if i > 0:
                        page_button_list[i-1].set_active(True)
                    else:
                        page_button_list[-1].set_active(True)
                    return True

        if ConfigManager.key_event_compare('move_page_left_key', event):
            i = 0
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    if (i - 1) > 0:
                        self.notebook.reorder_child(self.notebook.get_nth_page(i - 1), i - 2)
                        self.buttonbox.reorder_child(button, i - 1)
                        return True
                    else:
                        return False
                i += 1

        if ConfigManager.key_event_compare('move_page_right_key', event):
            i = 0
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    if (i + 1) < len(self.buttonbox):
                        self.notebook.reorder_child(self.notebook.get_nth_page(i - 1), i)
                        self.buttonbox.reorder_child(button, i + 1)
                        return True
                    else:
                        return False
                i += 1

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.update_ui()

    def init_transparency(self):
        self.set_app_paintable(True)
        visual = self.screen.get_rgba_visual()
        if visual != None and self.screen.is_composited():
            self.set_visual(visual)
        else:
            ConfigManager.use_fake_transparency = True

    def update_events(self):
        while Gtk.events_pending():
            Gtk.main_iteration()
        Gdk.flush()

    def slide_up(self, i=0):
        self.slide_effect_running = True
        step = ConfigManager.get_conf('window', 'animation_step_count')
        if not self.is_fullscreen:
            win_rect = self.monitor
        else:
            win_rect = self.get_allocation()
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step+1:
            self.resize(win_rect.width, win_rect.height - int(((win_rect.height/step) * i)))
            self.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('window', 'animation_step_time'), self.slide_up, i+1)
        else:
            self.hide()
            self.unrealize()
        if self.get_window() != None:
            self.get_window().configure_finished()
        self.slide_effect_running = False

    def slide_down(self, i=1):
        self.slide_effect_running = True
        step = ConfigManager.get_conf('window', 'animation_step_count')
        if not self.is_fullscreen:
            win_rect = self.monitor
        else:
            win_rect = self.get_screen_rectangle()
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step + 1:
            self.resize(win_rect.width, int(((win_rect.height/step) * i)))
            self.queue_resize()
            self.resizer.set_property('position', int(((win_rect.height/step) * i)))
            self.resizer.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('window', 'animation_step_time'), self.slide_down, i+1)
        if self.get_window() != None:
            self.get_window().configure_finished()
        self.slide_effect_running = False

    def show_hide(self):
        if self.slide_effect_running:
            return
        event_time = self.hotkey.get_current_event_time()
        if(self.losefocus_time and self.losefocus_time >= event_time):
            return

        if self.get_visible():
            if ConfigManager.get_conf('window', 'use_animation'):
                self.slide_up()
            else:
                self.hide()
            return
        else:
            if ConfigManager.get_conf('window', 'use_animation'):
                self.slide_down()
            self.update_ui()
            self.show()
