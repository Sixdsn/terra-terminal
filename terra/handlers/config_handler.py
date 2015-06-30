"""
Contains a config handler for terra.
"""

import yaml
import os
import sys


class ConfigHandler(dict):
    defaults = {}
    """:type: dict"""

    file = None
    """:type: str"""

    def __init__(self, config_defaults=None, config_file='', *args, **kw):
        """
        Initialize the standard dictionary and also read default config and
        user config.

        :type config_file: str
        :type config_defaults: dict
        """
        super(ConfigHandler, self).__init__(*args, **kw)

        if config_defaults:
            # Store defaults for later usage.
            self.defaults = config_defaults.copy()

            # Set default values for each option in each section.
            for section_name in self.defaults:
                # Add all default sections.
                self[section_name] = {}

                for option, value in self.defaults[section_name].iteritems():
                    self[section_name].setdefault(option, value)

        if config_file == '':
            config_file = os.path.expanduser('~/.config/terra/main.yaml')
        self.file = config_file

        # Load the user config.
        try:
            if os.path.exists(config_file):
                print('[DEBUG] Reading config file: {}'.format(config_file))

                with open(self.file, 'r') as config_file:
                    # Load the config file.
                    user_config = yaml.load(config_file)
                    """:type: dict"""

                if user_config:
                    self.__parse_user_config(user_config)

                # print('[DEBUG] User config loaded:')
                # print(yaml.dump(user_config, default_flow_style=False, indent=2))
            else:
                print('[DEBUG] No config file: {}'.format(config_file))

        except IOError:
            sys.exit('[ERROR] Could not read config file: {}'.format(config_file))
        except yaml.YAMLError:
            sys.exit('[ERROR] Malformed config file: {}'.format(config_file))

    def __parse_user_config(self, user_config):
        """
        Parse config loaded from a user's config YAML file and merge them with
        the default config values.

        :type user_config: dict
        """
        for section_name in user_config:
            for option, value in user_config[section_name].iteritems():
                if value is None:
                    del self[section_name][option]
                else:
                    if section_name not in self:
                        self[section_name] = {}
                    self[section_name][option] = value

    def save(self):
        """
        Save the active configuration to the user config file.
        """
        directory = os.path.dirname(self.file)
        if not os.path.exists(directory):
            os.mkdir(directory)

        with open(self.file, 'wb') as config_file:
            config_data = self.copy()

            # Save the configuration to file.
            yaml.dump(config_data, config_file, default_flow_style=False, indent=2)
