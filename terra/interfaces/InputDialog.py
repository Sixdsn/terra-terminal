"""
This files contains a custom Gtk Dialog widget.
"""


from gi.repository import Gtk


class InputDialog(Gtk.Dialog):
    def __init__(self, parent, title, label, entry_text):
        Gtk.Dialog.__init__(
            self, title, parent, 0,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY,
            )
        )

        # Set the default widget.
        self.set_default_response(Gtk.ResponseType.APPLY)

        # Get the content area of the dialog.
        box = self.get_content_area()
        """:type: Gtk.Box"""

        # Set the content area spacing.
        box.set_spacing(16)
        box.set_border_width(16)

        # Add a grid in the content area.
        grid = Gtk.Grid(column_spacing=8, row_spacing=16)
        box.add(grid)

        # Add a label in the content grid.
        label = Gtk.Label(label)
        grid.add(label)

        # Add an entry in the content grid.
        entry = Gtk.Entry()
        grid.attach_next_to(entry, label, Gtk.PositionType.RIGHT, 2, 1)

        # Set the entry text.
        entry.set_text(entry_text)

        # Select the entry text.
        entry.set_can_focus(True)

        # Activate the default widget when pressing enter.
        entry.set_activates_default(True)

        # Store a reference for later usage.
        self.entry = entry

        self.show_all()

    def get_entry_text(self):
        return self.entry.get_text()
