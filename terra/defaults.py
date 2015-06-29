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

import os

# @TODO: Rename and regroup settings.
ConfigDefaults = {
    'general': {
        # General
        # 'run_on_startup': False,
        'prompt_on_quit': True,
        'spawn_term_on_last_close': False,

        'separator_size': '2',

        'hide_from_taskbar': False,
        'hide_on_start': False,

        'select_by_word': 'LUEtWmEtejAtOSwuLz8lJiM6Xw==',  # base64 encoded
        'start_shell_program': os.getenv('SHELL', '/bin/sh'),
        'start_directory': '$home$',
    },

    'window': {
        # Window - General
        'use_border': True,
        'always_on_top': False,
        'hide_on_losefocus': False,

        # Window - Animation
        'use_animation': False,
        'animation_step_count': 20,
        'animation_step_time': 10,
    },

    'terminal': {
        # Terminal - General
        'use_system_font': True,
        'font_name': 'Monospace 10',

        # Terminal - Appearance
        'color_text': '#ffffffffffff',
        'color_background': '#000000000000',
        'background_image': '',
        'background_transparency': 10,

        # Terminal - Scrolling
        'show_scrollbar': True,
        'scrollback_unlimited': False,
        'scrollback_lines': 2048,
        'scroll_on_output': False,
        'scroll_on_keystroke': True,

    },

    'shortcuts': {
        # Shortcuts - General
        'global_key': 'F12',
        'fullscreen_key': 'F11',
        'toggle_scrollbars_key': '<Control><Shift>S',
        'quit_key': '<Control>q',
        'select_all_key': '<Control>a',
        'copy_key': '<Control><Shift>C',
        'paste_key': '<Control><Shift>V',

        # Shortcuts - Tabs
        'new_page_key': '<Control>n',
        'rename_page_key': 'F2',
        'close_page_key': '<Control>W',
        'prev_page_key': '<Control>Page_Up',
        'next_page_key': '<Control>Page_Down',
        'move_page_left_key': '<Control><Shift>Page_Up',
        'move_page_right_key': '<Control><Shift>Page_Down',

        # Shortcuts - Terminal
        'split_h_key': '<Control><Shift>H',
        'split_v_key': '<Control><Shift>J',
        'close_node_key': '<Control><Shift>K',
        'move_up_key': '<Control><Shift>Up',
        'move_down_key': '<Control><Shift>Down',
        'move_left_key': '<Control><Shift>Left',
        'move_right_key': '<Control><Shift>Right',
        'move_left_screen_key': '<Super><Shift>Left',
        'move_right_screen_key': '<Super><Shift>Right',
    },

    'layout': {
        # Layout default settings.
        'disabled': False,
        'width': 1280,
        'height': 1024,
        'posx': 0,
        'posy': 0,
        'fullscreen': False,
        'horizontal-position': 150,
        'vertical-position': 150,
        'id': 0,
        'hide-tab-bar-fullscreen': True,
        'hide-tab-bar': False,
    },
}
