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

        # Set the default configuration.
        if config_defaults:
            # Store defaults for later usage.
            self.defaults = config_defaults.copy()

            # Set default values for each option in each section.
            for section_name in self.defaults:
                # Add all default sections.
                self[section_name] = {}

                # Set defaults for each section.
                for option, value in self.defaults[section_name].iteritems():
                    self[section_name].setdefault(option, value)

        # Use the main config file, in no file path was provided.
        if config_file == '':
            config_file = os.path.expanduser('~/.config/terra/main.yaml')
        self.file = config_file

        # Load the user config.
        try:
            if os.path.exists(self.file):
                print('[DEBUG] Reading config file: {}'.format(self.file))

                with open(self.file, 'r') as config_file:
                    # Read the config file contents and create a dictionary.
                    config_data = yaml.load(config_file)
                    """:type: dict"""

                    if config_data:
                        self.__parse_config_data(config_data)
            else:
                print('[DEBUG] No config file: {}'.format(self.file))

        except IOError:
            sys.exit('[ERROR] Could not read config file: {}'.format(self.file))
        except yaml.YAMLError:
            sys.exit('[ERROR] Malformed config file: {}'.format(self.file))

    def __parse_config_data(self, config_data):
        """
        Parse the config data loaded from the provided config file.

        :type config_data: dict
        """
        for section_name in config_data:
            for option, value in config_data[section_name].iteritems():
                # Allow the deletion of default values.
                if value is None:
                    del self[section_name][option]
                    continue

                # Create section if it does not exit.
                if section_name not in self:
                    self[section_name] = {}

                # Set the option.
                self[section_name][option] = value

    def save(self):
        """
        Save the active configuration to the config file.
        """

        # Make sure the config directory exists.
        directory = os.path.dirname(self.file)
        if not os.path.exists(directory):
            os.mkdir(directory)

        try:
            # Open the file and save the config data.
            with open(self.file, 'wb') as config_file:
                config_data = self.copy()

                # Save the configuration to file.
                yaml.dump(config_data, config_file, default_flow_style=False, indent=2)
        except IOError:
            print('Could not save the config file: {}'.format(self.file))
