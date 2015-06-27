"""
Utilities for terra terminal.
"""

import os

from pkg_resources import DistributionNotFound, Requirement, resource_filename, resource_isdir

from terra import (__version__)

class TerraHandler:
    version = __version__
    __root_path = ''
    __config_path = ''

    # @TODO: Remove and cleanup TerminalWin.update_ui()!? Use the Wins dictionary instead?
    __ui_event_handlers = []

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

    @classmethod
    def add_ui_event_handler(cls, callable_handler):
        if callable_handler not in cls.__ui_event_handlers:
            cls.__ui_event_handlers.append(callable_handler)

    @classmethod
    def remove_ui_event_handler(cls, callable_handler):
        if callable_handler in cls.__ui_event_handlers:
            for i in xrange(len(cls.__ui_event_handlers)):
                if cls.__ui_event_handlers[i] == callable_handler:
                    del cls.__ui_event_handlers[i]
                    return

    @classmethod
    def execute_ui_event_handlers(cls):
        for callable_handler in cls.__ui_event_handlers:
            callable_handler()
