"""
Iternationalizatio handler for terra terminal.
"""

try:
    from gettext import gettext as t
except ImportError:
    def dummy_trans(text):
        return text
    t = dummy_trans
