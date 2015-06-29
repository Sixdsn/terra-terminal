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

from terra.defaults import ConfigDefaults
from terra.handlers import TerraHandler


class ConfigManager:
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
        return cls.config.sections()

    @staticmethod
    def get_conf(section, option):
        try:
            value = ConfigManager.config.get(section, option)
        except ConfigParser.Error:
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
            ConfigManager.config.add_section(section)
            ConfigManager.config.set(section, option, str(value))
        except ConfigParser.Error:
            print("[DEBUG] Config section '%s' has no option named '%s'." % (section, option))
            return

    @staticmethod
    def del_conf(section):
        try:
            ConfigManager.config.remove_section(section)
        except ConfigParser.NoSectionError:
            print("[DEBUG] No section '%s'." % section)
        except ConfigParser.Error:
            print("[DEBUG] No section '%s'." % section)
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
