"""
Contains the main handler for terra terminal.
"""

import os

from pkg_resources import DistributionNotFound, Requirement, resource_filename, resource_isdir

from terra import (__version__)
from terra.defaults import ConfigDefaults
from terra.handlers import ConfigHandler


class TerraHandler:
    version = __version__
    """:type: str"""

    config = None
    """:type: terra.handlers.ConfigHandler"""

    Wins = None
    """:type: terra.terminal.TerminalWinContainer"""

    __root_path = ''
    """:type: str"""

    # @TODO: Remove this list and cleanup TerminalWin.update_ui().
    __ui_event_handlers = []
    """:type: list"""

    @classmethod
    def __init__(cls, root_path=None):
        if root_path:
            # Set the project root path. Useful for local development, when the
            # project is not installed globally.
            # @see: TerraHandler.get_resources_path()
            cls.__root_path = root_path

        # Set the user config path.
        cls.config = ConfigHandler(config_defaults=ConfigDefaults)

    @classmethod
    def get_root_path(cls):
        return cls.__root_path

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
