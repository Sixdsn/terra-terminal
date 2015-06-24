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

from base64 import b64encode, b64decode
import ConfigParser
import os

from gi.repository import Gdk

from terra import (__version__)
from terra.defaults import ConfigDefaults
from terra.handler import TerraHandler

__terra_app_directory__ = '/usr/local/share/applications/'


class ConfigManager:
    version = __version__
    config_file_name = 'main.cfg'

    defaults = ConfigDefaults
    config = ConfigDefaults

    callback_list = []
    use_fake_transparency = False
    disable_losefocus_temporary = False

    @classmethod
    def __init__(cls):
        # Load the user config, if any.
        config_path = TerraHandler.get_config_path()
        if os.path.exists(config_path):
            config_file_path = os.path.join(config_path, cls.config_file_name)
            if os.path.exists(config_file_path):
                cls.config.read(config_file_path)

        # TODO: Remove once the code no longer requires the config files!
        # Now save the config file.
        cls.save_config()

    @classmethod
    def get_sections(cls):
        # TODO: Remove! For some reason, on my setup the `sections()` method
        # raises a "tuple assignment index out of range" exception.
        # Reading items from the config seems to solve the issue.
        cls.config.options('general')

        return cls.config.sections()

    @staticmethod
    def get_conf(section, option):
        try:
            value = ConfigManager.config.get(section, option)
        except ConfigParser.Error:
            print ("[DEBUG] Config section '%s' has no option named '%s'." %
                    (section, option))
            return None

        if option == 'select_by_word':
            return b64decode(value)

        if value == 'True':
            return True
        elif value == 'False':
            return False

        try:
            return int(value)
        except ValueError:
            return value

    @staticmethod
    def set_conf(section, option, value):
        if option == 'select_by_word':
            value = b64encode(value)
        try:
            ConfigManager.config.set(section, option, str(value))
        except ConfigParser.NoSectionError:
            print ("[DEBUG] No section '%s'."% (section))
            ConfigManager.config.add_section(section)
            ConfigManager.config.set(section, option, str(value))
        except ConfigParser.Error:
            print ("[DEBUG] Config section '%s' has no option named '%s'." %
                    (section, option))
            return

    @staticmethod
    def del_conf(section):
        try:
            ConfigManager.config.remove_section(section)
        except ConfigParser.NoSectionError:
            print ("[DEBUG] No section '%s'."% (section))
        except ConfigParser.Error:
            print ("[DEBUG] No section '%s'."% (section))
            return

    @classmethod
    def save_config(cls):
        config_path = TerraHandler.get_config_path()
        if not os.path.exists(config_path):
            os.mkdir(config_path)

        config_file_path = os.path.join(config_path, cls.config_file_name)
        with open(config_file_path, 'wb') as configfile:
            # @TODO: Only save overridden values?!?
            cls.config.write(configfile)

    @staticmethod
    def add_callback(method):
        if not method in ConfigManager.callback_list:
            ConfigManager.callback_list.append(method)

    @staticmethod
    def remove_callback(method):
        if method in ConfigManager.callback_list:
            for i in xrange(len(ConfigManager.callback_list)):
                if ConfigManager.callback_list[i] == method:
                    del ConfigManager.callback_list[i]
                    return

    @staticmethod
    def callback():
        for method in ConfigManager.callback_list:
            method()

    @staticmethod
    def key_event_compare(conf_name, event):
        key_string = ConfigManager.get_conf('shortcuts', conf_name)

        if ((Gdk.ModifierType.CONTROL_MASK & event.state) == Gdk.ModifierType.CONTROL_MASK) != ('<Control>' in key_string):
            return False

        if ((Gdk.ModifierType.MOD1_MASK & event.state) == Gdk.ModifierType.MOD1_MASK) != ('<Alt>' in key_string):
            return False

        if ((Gdk.ModifierType.SHIFT_MASK & event.state) == Gdk.ModifierType.SHIFT_MASK) != ('<Shift>' in key_string):
            return False

        if ((Gdk.ModifierType.SUPER_MASK & event.state) == Gdk.ModifierType.SUPER_MASK) != ('<Super>' in key_string):
            return False

        key_string = key_string.replace('<Control>', '')
        key_string = key_string.replace('<Alt>', '')
        key_string = key_string.replace('<Shift>', '')
        key_string = key_string.replace('<Super>', '')

        if (key_string.lower() != Gdk.keyval_name(event.keyval).lower()):
            return False

        return True
