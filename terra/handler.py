"""
Utilities for terra terminal.
"""

import os
import sys

from pkg_resources import DistributionNotFound, Requirement, resource_filename, resource_isdir

from terra import (__version__)

class TerraHandler:
    version = __version__
    __root_path = ''
    __config_path = ''

    Wins = None

    @classmethod
    def __init__(cls, root_path=None):
        if root_path:
            # Set the project root path. Useful for local development, when the
            # project is not installed globally.
            # @see: TerraHandler.get_resources_path()
            cls.__root_path = root_path

        # Set the user config path.
        cls.__config_path = os.path.join(os.environ['HOME'], '.config', 'terra')

    @classmethod
    def get_root_path(cls):
        return cls.__root_path

    @classmethod
    def get_config_path(cls):
        return cls.__config_path

    @classmethod
    def get_resources_path(cls):
        relative_path = os.path.join('terra', 'resources')
        full_path = None

        try:
            # Try to use the pip distribution to determine the template path.
            resource_name = Requirement.parse('terra')

            # Check if the template directory exists in the distribution.
            if resource_isdir(resource_name, relative_path):
                full_path = resource_filename(resource_name, relative_path)

        except DistributionNotFound:
            # Otherwise, just use the script root path.
            tmp_path = os.path.join(cls.get_root_path(), relative_path)

            if os.path.exists(tmp_path):
                full_path = tmp_path

        return full_path
