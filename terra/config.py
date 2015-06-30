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

from terra.handlers import TerraHandler

# Define strings and regular expressions for handling section names.
# TODO: Use nested values, instead of special section names.
SCREEN_NAME_PREFIX = 'layout-screen-'
SCREEN_NAME_REGEX = '^layout-screen-(\d+)$'


# TODO: Remove config manager once the migration is finished.
class ConfigManager:
    defaults = TerraHandler.config.defaults
    """:type: dict"""

    # TODO: Move to MainHandler
    use_fake_transparency = False
    """:type: bool"""
    disable_losefocus_temporary = False
    """:type: bool"""

    # Holds a reference tot the config handler.
    handler = None
    """:type: terra.handlers.ConfigHandler"""

    def __init__(self):
        pass

    @staticmethod
    def get_sections():
        return sorted(TerraHandler.config.keys())

    @staticmethod
    def get_conf(section, option):
        # TODO: Fix!
        if section.find(SCREEN_NAME_PREFIX) == 0 and section not in TerraHandler.config:
            TerraHandler.config[section] = TerraHandler.config['layout'].copy()
            return TerraHandler.config['layout'][option]

        # TODO: Cleanup layout config.
        if section not in TerraHandler.config:
            return None
        if option not in TerraHandler.config[section]:
            return None

        return TerraHandler.config[section][option]

    @staticmethod
    def set_conf(section, option, value):
        if section not in TerraHandler.config:
            TerraHandler.config[section] = {}

        TerraHandler.config[section][option] = value

    @staticmethod
    def del_conf(section):
        if section in TerraHandler.config:
            del TerraHandler.config[section]

    @staticmethod
    def save_config():
        TerraHandler.config.save()
