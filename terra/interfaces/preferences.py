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

import os
import sys
import shutil

from gi.repository import Gtk, Gdk, GdkPixbuf, GdkX11

from terra.config import ConfigManager
from terra.handlers import TerraHandler
from terra.i18n import t


class Preferences:
    def __init__(self):
        # TODO: Only initialize the UI once. Find a way to hide the window.
        self.init_ui()

    def init_ui(self):
        preferences_ui_file = os.path.join(TerraHandler.get_resources_path(), 'ui/preferences.ui')
        if not os.path.exists(preferences_ui_file):
            msg = 'ERROR: UI data file is missing: {}'.format(preferences_ui_file)
            sys.exit(msg)

        self.is_running = True
        builder = Gtk.Builder()
        builder.set_translation_domain('terra')
        builder.add_from_file(preferences_ui_file)

        self.window = builder.get_object('preferences_window')
        self.window.connect('destroy', self.on_cancel_clicked)
        self.window.set_keep_above(True)

        self.btn_cancel = builder.get_object('btn_cancel')
        self.btn_cancel.connect('clicked', self.on_cancel_clicked)

        self.btn_apply = builder.get_object('btn_apply')
        self.btn_apply.connect('clicked', self.on_apply_clicked)

        self.btn_ok = builder.get_object('btn_ok')
        self.btn_ok.connect('clicked', self.on_ok_clicked)

        # TAB: General
        boolean_options = [
            # 'run_on_startup',
            'prompt_on_quit',
            'spawn_term_on_last_close',
            'hide_from_taskbar',
            'hide_on_start',
        ]

        for option in boolean_options:
            setattr(self, option, builder.get_object(option))
            getattr(self, option).set_active(ConfigManager.get_conf('general', option))

        self.run_on_startup = builder.get_object('run_on_startup')
        self.run_on_startup.set_active(os.path.exists(os.environ['HOME'] + '/.config/autostart/terra.desktop'))

        self.separator_size = builder.get_object('separator_size')
        self.separator_size.set_value(int(ConfigManager.get_conf('general', 'separator_size')) * 1.0)

        self.select_by_word = builder.get_object('select_by_word')
        self.select_by_word.set_text(ConfigManager.get_conf('general', 'select_by_word'))

        self.start_shell_program = builder.get_object('start_shell_program')
        self.start_shell_program.set_text(ConfigManager.get_conf('general', 'start_shell_program'))

        self.dir_custom = builder.get_object('dir_custom')
        self.radio_home = builder.get_object('radio_home')
        self.radio_pwd = builder.get_object('radio_pwd')
        self.radio_dir_custom = builder.get_object('radio_dir_custom')
        self.radio_dir_custom.connect('toggled', lambda w: self.toggle_sensitive(self.radio_dir_custom, [self.dir_custom]))

        start_directory = ConfigManager.get_conf('general', 'start_directory')
        if start_directory == '$home$':
            self.radio_home.set_active(True)
        elif start_directory == '$pwd$':
            self.radio_pwd.set_active(True)
        else:
            self.radio_dir_custom.set_active(True)
            self.dir_custom.set_text(start_directory)
            self.dir_custom.set_sensitive(True)

        # TAB: Window
        boolean_options = [
            'use_border',
            'always_on_top',
            'hide_on_losefocus',
            'use_animation',
        ]
        for option in boolean_options:
            setattr(self, option, builder.get_object(option))
            getattr(self, option).set_active(ConfigManager.get_conf('window', option))

        self.animation_step_count = builder.get_object('animation_step_count')
        self.animation_step_count.set_text(str(ConfigManager.get_conf('window', 'animation_step_count')))

        self.animation_step_time = builder.get_object('animation_step_time')
        self.animation_step_time.set_text(str(ConfigManager.get_conf('window', 'animation_step_time')))

        # TAB: Terminal
        boolean_options = [
            'use_system_font',
            'show_scrollbar',
            'scrollback_unlimited',
            'scroll_on_output',
            'scroll_on_keystroke',
        ]

        for option in boolean_options:
            setattr(self, option, builder.get_object(option))
            getattr(self, option).set_active(ConfigManager.get_conf('terminal', option))

        self.font_name = builder.get_object('font_name')
        self.font_name.set_font_name(ConfigManager.get_conf('terminal', 'font_name'))
        self.font_name.set_sensitive(not ConfigManager.get_conf('terminal', 'use_system_font'))

        self.use_system_font.connect('toggled', lambda w: self.toggle_sensitive(self.use_system_font, [self.font_name]))

        self.color_text = builder.get_object('color_text')
        self.color_text.set_color(Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_text')))

        self.color_background = builder.get_object('color_background')
        self.color_background.set_color(Gdk.color_parse(ConfigManager.get_conf('terminal', 'color_background')))

        self.background_image = builder.get_object('background_image')
        self.background_image.set_filename(ConfigManager.get_conf('terminal', 'background_image'))

        self.clear_background_image = builder.get_object('clear_background_image')
        self.clear_background_image.connect('clicked', lambda w: self.background_image.unselect_all())

        self.background_transparency = builder.get_object('background_transparency')
        self.background_transparency.set_value(int(ConfigManager.get_conf('terminal', 'background_transparency')) * 1.0)

        self.scrollback_lines = builder.get_object('scrollback_lines')
        self.scrollback_lines.set_text(str(ConfigManager.get_conf('terminal', 'scrollback_lines')))

        self.scrollback_unlimited.connect('toggled', lambda w: self.toggle_sensitive(self.scrollback_unlimited, [self.scrollback_lines]))

        # TAB: Keyboard Shortcuts
        # Store all keyboard shortcut entry boxes in array for connecting signals together.
        key_entries = [
            # General
            'global_key',
            'fullscreen_key',
            'toggle_scrollbars_key',
            'quit_key',
            'select_all_key',
            'copy_key',
            'paste_key',

            # Tabs
            'new_page_key',
            'rename_page_key',
            'close_page_key',
            'prev_page_key',
            'next_page_key',
            'move_page_left_key',
            'move_page_right_key',

            # Shortcuts - Terminal
            'split_h_key',
            'split_v_key',
            'close_node_key',
            'move_up_key',
            'move_down_key',
            'move_left_key',
            'move_right_key',
            'move_left_screen_key',
            'move_right_screen_key',
        ]
        for key in key_entries:
            setattr(self, key, builder.get_object(key))
            widget = getattr(self, key)
            widget.set_text(ConfigManager.get_conf('shortcuts', key))
            widget.connect('button-press-event', self.clear_key_entry)
            widget.connect('key-press-event', self.generate_key_string)

        self.restore_defaults = builder.get_object('restore_defaults')
        self.restore_defaults.connect('clicked', lambda w: self.restore_defaults_cb())

        # TAB: About
        self.logo = builder.get_object('terra_logo')
        logo_path = os.path.join(TerraHandler.get_resources_path(), 'terra.svg')
        self.logo_buffer = GdkPixbuf.Pixbuf.new_from_file_at_size(logo_path, 64, 64)
        self.logo.set_from_pixbuf(self.logo_buffer)

        self.version = builder.get_object('version')
        self.version.set_label(t("Version: ") + TerraHandler.version)

        self.webpage = builder.get_object('webpage')
        self.webpage.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'http://terraterminal.org', GdkX11.x11_get_server_time(self.window.get_window())))

        self.open_translation_page = builder.get_object('open_translation_page')
        self.open_translation_page.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'https://translations.launchpad.net/terra', GdkX11.x11_get_server_time(self.window.get_window())))

        self.report_bug = builder.get_object('report_bug')
        self.report_bug.connect('clicked', lambda w: Gtk.show_uri(self.window.get_screen(), 'https://github.com/Sixdsn/terra-terminal/issues', GdkX11.x11_get_server_time(self.window.get_window())))

    def clear_key_entry(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            widget.set_text("")

    def toggle_sensitive(self, source_object, target_objects):
        for target_object in target_objects:
            target_object.set_sensitive(not source_object.get_active())

    def restore_defaults_cb(self):
        for key in TerraHandler.config['shortcuts']:
            widget = getattr(self, key)
            widget.set_text(TerraHandler.config['shortcuts'][key])

    def generate_key_string(self, widget, event):
        key_str = ''

        if (Gdk.ModifierType.CONTROL_MASK & event.state) == Gdk.ModifierType.CONTROL_MASK:
            key_str += '<Control>'

        if (Gdk.ModifierType.MOD1_MASK & event.state) == Gdk.ModifierType.MOD1_MASK:
            key_str += '<Alt>'

        if (Gdk.ModifierType.SHIFT_MASK & event.state) == Gdk.ModifierType.SHIFT_MASK:
            key_str += '<Shift>'

        if (Gdk.ModifierType.SUPER_MASK & event.state) == Gdk.ModifierType.SUPER_MASK:
            key_str += '<Super>'

        key_str = key_str + Gdk.keyval_name(event.keyval)

        widget.set_text(key_str)

    def show(self):
        if not self.is_running:
            self.init_ui()
        self.window.show_all()

    def on_apply_clicked(self, widget):
        # TODO: Clean!

        # TAB: General
        boolean_options = [
            # 'run_on_startup',
            'prompt_on_quit',
            'spawn_term_on_last_close',
            'hide_from_taskbar',
            'hide_on_start',
        ]

        for option in boolean_options:
            ConfigManager.set_conf('general', option, getattr(self, option).get_active())

        desktop_file_source = os.path.join(TerraHandler.get_resources_path(), 'terra.desktop')
        if not os.path.exists(desktop_file_source):
            msg = 'ERROR: Desktop file is missing: {}'.format(desktop_file_source)
            sys.exit(msg)

        # TODO: Properly determine the running desktop environment.
        autostart_directory = None
        if os.path.isdir(os.path.expanduser('~/.config/autostart')):
            autostart_directory = os.path.expanduser('~/.config/autostart')
        elif os.path.isdir(os.path.expanduser('~/.kde4/Autostart')):
            autostart_directory = os.path.expanduser('~/.kde4/Autostart')

        # TODO: Catch errors.
        if autostart_directory:
            autostart_file_path = os.path.join(autostart_directory, 'terra.desktop')
            if self.run_on_startup.get_active():
                if not os.path.exists(autostart_file_path):
                    shutil.copyfile(desktop_file_source, autostart_file_path)
            else:
                if os.path.exists(autostart_file_path):
                    os.remove(autostart_file_path)
        else:
            msg = "[DEBUG] Desktop environment autostart missing: {}."
            print(msg.format(autostart_directory))

        ConfigManager.set_conf('general', 'separator_size', int(self.separator_size.get_value()))

        ConfigManager.set_conf('general', 'select_by_word', self.select_by_word.get_text())

        ConfigManager.set_conf('general', 'start_shell_program', self.start_shell_program.get_text())

        if self.radio_home.get_active():
            ConfigManager.set_conf('general', 'start_directory', '$home$')
        elif self.radio_pwd.get_active():
            ConfigManager.set_conf('general', 'start_directory', '$pwd$')
        else:
            ConfigManager.set_conf('general', 'start_directory', self.dir_custom.get_text())

        # TAB: Window
        boolean_options = [
            'use_border',
            'always_on_top',
            'hide_on_losefocus',
            'use_animation',
        ]
        for option in boolean_options:
            ConfigManager.set_conf('window', option, getattr(self, option).get_active())

        ConfigManager.set_conf('window', 'use_animation', self.use_animation.get_active())

        try:
            step_count = int(self.animation_step_count.get_text())
            if not step_count > 0:
                step_count = 20
        except ValueError:
            step_count = 20
        ConfigManager.set_conf('window', 'animation_step_count', step_count)

        try:
            step_time = int(self.animation_step_time.get_text())
            if not step_time > 0:
                step_time = 20
        except ValueError:
            step_time = 10
        ConfigManager.set_conf('window', 'animation_step_time', step_time)

        # TAB: Terminal
        boolean_options = [
            'use_system_font',
            'show_scrollbar',
            'scroll_on_output',
            'scroll_on_keystroke',
            'scrollback_unlimited',
        ]
        for option in boolean_options:
            ConfigManager.set_conf('terminal', option, getattr(self, option).get_active())

        ConfigManager.set_conf('terminal', 'font_name', self.font_name.get_font_name())

        ConfigManager.set_conf('terminal', 'color_text', self.color_text.get_color().to_string())

        ConfigManager.set_conf('terminal', 'color_background', self.color_background.get_color().to_string())

        ConfigManager.set_conf('terminal', 'background_image', self.background_image.get_filename())

        ConfigManager.set_conf('terminal', 'background_transparency', int(self.background_transparency.get_value()))

        try:
            scrollback_line = int(self.scrollback_lines.get_text())
        except ValueError:
            scrollback_line = 2048

        ConfigManager.set_conf('terminal', 'scrollback_lines', str(scrollback_line))

        # TAB: Shortcuts
        for key in TerraHandler.config['shortcuts']:
            widget = getattr(self, key)
            TerraHandler.config['shortcuts'][key] = widget.get_text()

        ConfigManager.save_config()
        TerraHandler.execute_ui_event_handlers()
        self.window.present()

    def on_ok_clicked(self, widget):
        self.is_running = False
        self.on_apply_clicked(self.btn_ok)
        self.window.hide()
        ConfigManager.disable_losefocus_temporary = False

    def on_cancel_clicked(self, widget):
        self.is_running = False
        self.window.hide()
        ConfigManager.disable_losefocus_temporary = False
