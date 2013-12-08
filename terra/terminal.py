#!/usr/bin/python
# -*- coding: utf-8; -*-
"""
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

from gi.repository import Gtk, Vte, GLib, Gdk, GdkPixbuf, GObject, GdkX11

from terra import globalhotkeys

from VteObject import VteObjectContainer
from config import ConfigManager
from layout import LayoutManager
from dialogs import RenameDialog
from dbusservice import DbusService
from i18n import _

from math import floor
import os
import time
import sys

apps = []
hotkey = None
bind_success = False

class TerminalWin(Gtk.Window):

    def __init__(self, name, monitor):
        super(TerminalWin, self).__init__()

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('terra')
        self.builder.add_from_file(ConfigManager.data_dir + 'ui/main.ui')
        self.name = name

        ConfigManager.add_callback(self.update_ui)
        
        self.screen = self.get_screen()
        self.monitor = monitor

        self.init_transparency()
        self.init_ui()
        self.update_ui()

        if not ConfigManager.get_conf('hide-on-start'):
            self.show_all()

    def init_ui(self):
        self.set_title(_('Terra Terminal Emulator'))

        if LayoutManager.get_conf(self.name, 'fullscreen'):
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
        self.logo_buffer = GdkPixbuf.Pixbuf.new_from_file_at_size(ConfigManager.data_dir  + 'image/terra.svg', 32, 32)
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
        self.connect('delete-event', lambda w, x: self.delete_event_callback())
        self.connect('key-press-event', self.on_keypress)
        self.connect('focus-out-event', self.on_window_losefocus)
        self.add(self.resizer)

        screen_id = LayoutManager.get_conf(self.name, 'id')
        tabs = LayoutManager.get_conf(self.name, 'tabs')
        if (tabs == None or tabs == 0):
            self.add_page()
        for tab in range(tabs):
            tab_name =  LayoutManager.get_conf(str("Tabs-%d-%d"% (screen_id, tab)), 'name')
            self.add_page(page_name=tab_name)

            for button in self.buttonbox:
                if button == self.radio_group_leader:
                    continue
                else:
                    button.set_active(True)
                    break

    def delete_event_callback(self):
        self.hide()
        return True

    def on_window_losefocus(self, window, event):
        if self.slide_effect_running:
            return
        if ConfigManager.disable_losefocus_temporary:
            return
        if not ConfigManager.get_conf('losefocus-hiding'):
            return

        if self.get_property('visible'):
            self.losefocus_time = GdkX11.x11_get_server_time(self.get_window())
            if ConfigManager.get_conf('use-animation'):
                self.slide_up()
            self.unrealize()
            self.hide()

    def exit(self):
        if ConfigManager.get_conf('prompt-on-quit'):
            ConfigManager.disable_losefocus_temporary = True
            msgtext = _("Do you really want to quit?")
            msgbox = Gtk.MessageDialog(self, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO, msgtext)
            response = msgbox.run()
            msgbox.destroy()
            ConfigManager.disable_losefocus_temporary = False

            if response != Gtk.ResponseType.YES:
                return False
        app_quit()

    def quit(self):
        if LayoutManager.get_conf(self.name, 'tabs'):
            tabid = 0
            screenid = LayoutManager.get_conf(self.name, 'id')
            for button in self.buttonbox:
                if button != self.radio_group_leader:
                    LayoutManager.set_conf(str("Tabs-%d-%d"% (screenid, tabid)), 'name', button.get_label())
                    tabid = tabid + 1
            LayoutManager.set_conf(self.name, 'tabs', tabid)
        ConfigManager.save_config()
        LayoutManager.save_config()
        remove_app(self)
        self.destroy()

    def on_resize(self, widget, event):
        if Gdk.ModifierType.BUTTON1_MASK & event.get_state() != 0:
            mouse_y = event.device.get_position()[2]
            new_height = mouse_y - self.get_position()[1]
            if new_height > 0:
                self.monitor.height = new_height
                self.resize(self.monitor.width, self.monitor.height)
                self.show()

    def update_resizer(self, widget, event):
        self.resizer.set_position(self.monitor.height)

        if not self.is_fullscreen:
            new_percent = self.monitor.height
            LayoutManager.set_conf(self.name, 'height', str(self.monitor.height))
            LayoutManager.save_config()

    def add_page(self, page_name=None):
        self.notebook.append_page(VteObjectContainer(), None)
        self.notebook.set_current_page(-1)
        self.get_active_terminal().grab_focus()

        page_count = 0
        for button in self.buttonbox:
            if button != self.radio_group_leader:
                page_count += 1

        if page_name == None:
            page_name = _("Terminal ") + str(page_count+1)

        new_button = Gtk.RadioButton.new_with_label_from_widget(self.radio_group_leader, page_name)
        new_button.set_property('draw-indicator', False)
        new_button.set_active(True)
        new_button.show()
        new_button.connect('toggled', self.change_page)
        new_button.connect('button-release-event', self.page_button_mouse_event)

        self.buttonbox.pack_start(new_button, False, True, 0)

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

    def update_ui(self, resize=True):
        self.unmaximize()
        self.stick()
        self.override_gtk_theme()
        self.set_keep_above(ConfigManager.get_conf('always-on-top'))
        self.set_decorated(ConfigManager.get_conf('use-border'))
        self.set_skip_taskbar_hint(ConfigManager.get_conf('skip-taskbar'))

        win_rect = self.monitor
        if ConfigManager.get_conf('hide-tab-bar'):
            self.tabbar.hide()
            self.tabbar.set_no_show_all(True)
        else:
            self.tabbar.set_no_show_all(False)
            self.tabbar.show()

        if self.is_fullscreen:
            self.fullscreen()
            # hide resizer
            if self.resizer.get_child2() != None:
                self.resizer.remove(self.resizer.get_child2())

            # hide tab bar
            if ConfigManager.get_conf('hide-tab-bar-fullscreen'):
                self.tabbar.set_no_show_all(True)
                self.tabbar.hide()
        else:
            # show resizer
            if self.resizer.get_child2() == None:
                self.resizer.add2(Gtk.Box())
                self.resizer.get_child2().show_all()
            
            # show tab bar
            if ConfigManager.get_conf('hide-tab-bar-fullscreen'):
                self.tabbar.set_no_show_all(False)
                self.tabbar.show()

            self.unfullscreen()

            self.reshow_with_initial_size()
            self.resize(win_rect.width, win_rect.height)
            self.move(win_rect.x, win_rect.y)


    def override_gtk_theme(self):
        css_provider = Gtk.CssProvider()

        bg = Gdk.color_parse(ConfigManager.get_conf('color-background'))
        bg_hex =  '#%02X%02X%02X' % (int((bg.red/65536.0)*256), int((bg.green/65536.0)*256), int((bg.blue/65536.0)*256))

        css_provider.load_from_data('''
            #notebook GtkPaned 
            {
                -GtkPaned-handle-size: %i;
            }
            GtkVScrollbar
            {
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
            ''' % (ConfigManager.get_conf('seperator-size'), bg_hex))

        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(self.screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def on_keypress(self, widget, event):
        if ConfigManager.key_event_compare('toggle-scrollbars-key', event):
            ConfigManager.set_conf('show-scrollbar', not ConfigManager.get_conf('show-scrollbar'))
            ConfigManager.save_config()
            ConfigManager.callback()
            return True

        if ConfigManager.key_event_compare('move-up-key', event):
            self.get_active_terminal().move(direction=1)
            return True

        if ConfigManager.key_event_compare('move-down-key', event):
            self.get_active_terminal().move(direction=2)
            return True

        if ConfigManager.key_event_compare('move-left-key', event):
            self.get_active_terminal().move(direction=3)
            return True

        if ConfigManager.key_event_compare('move-right-key', event):
            self.get_active_terminal().move(direction=4)
            return True

        if ConfigManager.key_event_compare('quit-key', event):
            self.quit()
            return True

        if ConfigManager.key_event_compare('select-all-key', event):
            self.get_active_terminal().select_all()
            return True

        if ConfigManager.key_event_compare('copy-key', event):
            self.get_active_terminal().copy_clipboard()
            return True

        if ConfigManager.key_event_compare('paste-key', event):
            self.get_active_terminal().paste_clipboard()
            return True

        if ConfigManager.key_event_compare('split-v-key', event):
            self.get_active_terminal().split_axis(None, 'v')
            return True

        if ConfigManager.key_event_compare('split-h-key', event):
            self.get_active_terminal().split_axis(None, 'h')
            return True

        if ConfigManager.key_event_compare('close-node-key', event):
            self.get_active_terminal().close_node(None)
            return True

        if ConfigManager.key_event_compare('fullscreen-key', event):
            self.toggle_fullscreen()
            return True

        if ConfigManager.key_event_compare('new-page-key', event):
            self.add_page()
            return True

        if ConfigManager.key_event_compare('rename-page-key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_rename(None, button)
                    return True

        if ConfigManager.key_event_compare('close-page-key', event):
            for button in self.buttonbox:
                if button != self.radio_group_leader and button.get_active():
                    self.page_close(None, button)
                    return True

        if ConfigManager.key_event_compare('next-page-key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if (page_button_list[i].get_active() == True):
                    if (i + 1 < len(page_button_list)):
                        page_button_list[i+1].set_active(True)
                    else:
                        page_button_list[0].set_active(True)
                    return True


        if ConfigManager.key_event_compare('prev-page-key', event):
            page_button_list = self.buttonbox.get_children()[1:]

            for i in range(len(page_button_list)):
                if page_button_list[i].get_active():
                    if i > 0:
                        page_button_list[i-1].set_active(True)
                    else:
                        page_button_list[-1].set_active(True)
                    return True

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
        step = ConfigManager.get_conf('step-count')
        win_rect = self.monitor
        height, width = win_rect.height, win_rect.width
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step+1:
            self.resize(width, height - int(((height/step) * i)))
            self.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('step-time'), self.slide_up, i+1)
        else:
            self.hide()
            self.unrealize()
        if self.get_window() != None:
            self.get_window().configure_finished()
        self.slide_effect_running = False

    def slide_down(self, i=1):
        step = ConfigManager.get_conf('step-count')
        self.slide_effect_running = True
        win_rect = self.monitor
        if self.get_window() != None:
            self.get_window().enable_synchronized_configure()
        if i < step + 1:
            self.resize(win_rect.width, int(((win_rect.height/step) * i)))
            self.queue_resize()
            self.resizer.set_property('position', int(((win_rect.height/step) * i)))
            self.resizer.queue_resize()
            self.update_events()
            GObject.timeout_add(ConfigManager.get_conf('step-time'), self.slide_down, i+1)
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
            if ConfigManager.get_conf('use-animation'):
                self.slide_up()
            return
        else:
            if ConfigManager.get_conf('use-animation'):
                self.update_ui(resize=False)
            else:
                self.update_ui()
            self.show()
            x11_win = self.get_window()
            x11_time = GdkX11.x11_get_server_time(x11_win)
            x11_win.focus(x11_time)
            if ConfigManager.get_conf('use-animation'):
                self.slide_down()

def cannot_bind(app):
    ConfigManager.set_conf('hide-on-start', False)
    ConfigManager.set_conf('losefocus-hiding', False)
    msgtext = _("Another application using '%s'. Please open preferences and change the shortcut key.") % ConfigManager.get_conf('global-key')
    msgbox = Gtk.MessageDialog(app, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, msgtext)
    msgbox.run()
    msgbox.destroy()

def show_hide():
    for app in apps:
        app.show_hide()

def update_ui():
    for app in apps:
        app.update_ui()

def get_screen(name):
    posx = LayoutManager.get_conf(name, 'posx')
    posy = LayoutManager.get_conf(name, 'posy')
    width = LayoutManager.get_conf(name, 'width')
    height = LayoutManager.get_conf(name, 'height')
    if (posx == None or posy == None or width == None or height == None):
        return (None)
    rect = Gdk.Rectangle()
    rect.x = posx
    rect.y = posy
    rect.width = width
    rect.height = height
    return (rect)

def get_nb_screen(name):
    return (LayoutManager.get_conf(name, 'screens'))

def app_quit():
    for app in apps:
        if (app.quit() == False):
            return
    sys.stdout.flush()
    sys.stderr.flush()
    Gtk.main_quit()

def remove_app(ext):
    if ext in apps:
        apps.remove(ext)
    if (len(apps) == 0):
        app_quit()

def create_app(screenName ='DEFAULT', first = False):
    monitor = get_screen(screenName)
    if (monitor != None):
        print("Screen: %s"% screenName)
        app = TerminalWin(screenName, monitor)
        if (not bind_success):
            cannot_bind(app)
        app.hotkey = hotkey
        if (first):
            DbusService(app)
            first = False
        apps.append(app)
    else:
        print("Cannot find %s"% screenName)
    return first

def main():
    global bind_success
    globalhotkeys.init()
    hotkey = globalhotkeys.GlobalHotkey()
    bind_success = hotkey.bind(ConfigManager.get_conf('global-key'), lambda w: show_hide(), None)
    first = True
    for disp in Gdk.DisplayManager.get().list_displays():
        for screen_num in range(disp.get_n_screens()):
            screen = disp.get_screen(screen_num)
            for monitor_num in range(screen.get_n_monitors()):
                rect = screen.get_monitor_geometry(monitor_num)
                glScreenName = str("screen%d.%d-%d:%d-%dx%d"% (screen_num, monitor_num, rect.x, rect.y , rect.width, rect.height))
                nb_screens = get_nb_screen(glScreenName)
                for nb in range(nb_screens):
                    screenName = str("%s-%d"%(glScreenName, nb))
                    first = create_app(screenName, first)

    if (len(apps) == 0):
        create_app('DEFAULT', True)
    update_ui()
    Gtk.main()

if __name__ == "__main__":
    main()
