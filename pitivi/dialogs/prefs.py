# Pitivi video editor
#
#       pitivi/dialogs/prefs.py
#
# Copyright (c) 2005, Edward Hervey <bilboed@bilboed.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA 02110-1301, USA.

"""
Dialog box for user preferences.
"""

import os

from gettext import gettext as _

from gi.repository import Gtk

from pitivi.configure import get_ui_dir
from pitivi.settings import GlobalSettings
from pitivi.utils import widgets
from pitivi.utils.loggable import Loggable
from pitivi.utils.ui import SPACING


GlobalSettings.addConfigSection("user-interface")

GlobalSettings.addConfigOption('prefsDialogWidth',
                               section="user-interface",
                               key="prefs-dialog-width",
                               default=600)

GlobalSettings.addConfigOption('prefsDialogHeight',
                               section="user-interface",
                               key="prefs-dialog-height",
                               default=400)


class PreferencesDialog(Loggable):

    """
    Preferences for how the app works.
    """

    prefs = {}
    original_values = {}

    def __init__(self, app):
        Loggable.__init__(self)

        self.settings = app.settings
        self.widgets = {}
        self.resets = {}
        self._current = None

        # Identify the widgets we'll need
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(get_ui_dir(), "preferences.ui"))
        builder.connect_signals(self)
        self.dialog = builder.get_object("dialog1")
        self.model = builder.get_object("liststore1")
        self.treeview = builder.get_object("treeview1")
        self.contents = builder.get_object("box1")
        self.revert_button = builder.get_object("revertButton")
        self.factory_settings = builder.get_object("resetButton")
        self.restart_warning = builder.get_object("restartWarning")

        self.sections = {}
        self.__fillContents()
        req = self.contents.get_preferred_size()[0]
        min_width = req.width
        min_height = req.height
        width = max(min_width, self.settings.prefsDialogWidth)
        height = max(min_height, self.settings.prefsDialogHeight)
        self.dialog.set_transient_for(app.gui)
        self.dialog.set_default_size(width, height)

    def run(self):
        """Run the internal dialog"""
        self.dialog.run()

# Public API

    @classmethod
    def addPreference(cls, attrname, label, description, section=None,
                      widget_class=None, **args):
        """
        Add a user preference. The preferences dialog will try
        to guess the appropriate widget to use based on the type of the
        option, but you can override this by specifying a custom class.

        @param attrname: the id of the setting holding the preference
        @type attrname: C{str}
        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param : user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        @param widget_class: overrides auto-detected widget
        @type widget_class: C{class}
        """
        if not section:
            section = "General"
        if section not in cls.prefs:
            cls.prefs[section] = {}
        cls.prefs[section][attrname] = (label, description, widget_class, args)

    @classmethod
    def addPathPreference(cls, attrname, label, description, section=None):
        """
        Add an auto-generated user preference that will show up as a
        Gtk.FileChooserButton.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.PathWidget)

    @classmethod
    def addNumericPreference(cls, attrname, label, description, section=None,
                             upper=None, lower=None):
        """
        Add an auto-generated user preference that will show up as either a
        Gtk.SpinButton or an horizontal Gtk.Scale, depending whether both the
        upper and lower limits are set.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        @param upper: upper limit for this widget, or None
        @type upper: C{number}
        @param lower: lower limit for this widget, or None
        @type lower: C{number}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.NumericWidget, upper=upper, lower=lower)

    @classmethod
    def addTextPreference(cls, attrname, label, description, section=None, matches=None):
        """
        Add an auto-generated user preference that will show up as either a
        Gtk.SpinButton or an horizontal Gtk.Scale, depending on the upper and
        lower limits

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.TextWidget, matches=matches)

    @classmethod
    def addChoicePreference(cls, attrname, label, description, choices, section=None):
        """
        Add an auto-generated user preference that will show up as either a
        Gtk.ComboBox or a group of radio buttons, depending on the number of
        choices.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param choices: a sequence of (<label>, <value>) pairs
        @type choices: C{[(str, pyobject), ...]}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.ChoiceWidget, choices=choices)

    @classmethod
    def addTogglePreference(cls, attrname, label, description, section=None):
        """
        Add an auto-generated user preference that will show up as a
        Gtk.CheckButton.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.ToggleWidget)

    @classmethod
    def addColorPreference(cls, attrname, label, description, section=None, value_type=int):
        """
        Add an auto-generated user preference for specifying colors. The
        colors can be returned as either int, a string colorspec, or a
        Gdk.Color object. See the Gdk.color_parse() function for info
        on colorspecs.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.ColorWidget, value_type=value_type)

    @classmethod
    def addFontPreference(cls, attrname, label, description, section=None):
        """
        Add an auto-generated user preference that will show up as a
        font selector.

        @param label: user-visible name for this option
        @type label: C{str}
        @param description: a user-visible description documenting this option
        (ignored unless prefs_label is non-null)
        @type description: C{str}
        @param section: user-visible category to which this option
        belongs (ignored unless prefs_label is non-null)
        @type section: C{str}
        """
        cls.addPreference(attrname, label, description, section,
                          widgets.FontWidget)

# Implementation
    def __fillContents(self):
        for section in sorted(self.prefs):
            options = self.prefs[section]
            self.model.append((section,))
            grid = Gtk.Grid()
            grid.set_border_width(SPACING)
            grid.props.column_spacing = SPACING
            grid.props.row_spacing = SPACING / 2
            self.sections[section] = grid

            prefs = []
            for attrname in options:
                label, description, widget_class, args = options[attrname]
                widget = widget_class(**args)
                widget.setWidgetValue(getattr(self.settings, attrname))
                widget.connectValueChanged(
                    self._valueChangedCb, widget, attrname)
                widget.set_tooltip_text(description)
                self.widgets[attrname] = widget
                # Add a semicolon, except for checkbuttons.
                if isinstance(widget, widgets.ToggleWidget):
                    widget.set_label(label)
                    label_widget = None
                else:
                    # Translators: This adds a semicolon to an already
                    # translated name of a preference.
                    label = _("%(preference_label)s:") % {"preference_label": label}
                    label_widget = Gtk.Label(label=label)
                    label_widget.set_tooltip_text(description)
                    label_widget.set_alignment(1.0, 0.5)
                    label_widget.show()
                icon = Gtk.Image()
                icon.set_from_icon_name(
                    "edit-clear-all-symbolic", Gtk.IconSize.MENU)
                revert = Gtk.Button()
                revert.add(icon)
                revert.set_tooltip_text(_("Reset to default value"))
                revert.set_relief(Gtk.ReliefStyle.NONE)
                revert.set_sensitive(not self.settings.isDefault(attrname))
                revert.connect("clicked", self._resetOptionCb, attrname)
                revert.show_all()
                self.resets[attrname] = revert
                row_widgets = (label_widget, widget, revert)
                # Construct the prefs list so that it can be sorted.
                # Make sure the L{ToggleWidget}s appear at the end.
                prefs.append((label_widget is None, label, row_widgets))

            # Sort widgets: I think we only want to sort by the non-localized
            # names, so options appear in the same place across locales ...
            # but then I may be wrong
            for y, (_1, _2, row_widgets) in enumerate(sorted(prefs)):
                label, widget, revert = row_widgets
                if not label:
                    grid.attach(widget, 0, y, 2, 1)
                    grid.attach(revert, 2, y, 1, 1)
                else:
                    grid.attach(label, 0, y, 1, 1)
                    grid.attach(widget, 1, y, 1, 1)
                    grid.attach(revert, 2, y, 1, 1)
                widget.show()
                revert.show()

            self.contents.pack_start(grid, False, False, 0)

        self.treeview.get_selection().select_path((0,))
        self.factory_settings.set_sensitive(self._canReset())

    def _treeSelectionChangedCb(self, selection):
        """ Update current when selection changed"""
        model, _iter = selection.get_selected()
        section = self.sections[model[_iter][0]]
        if self._current != section:
            if self._current:
                self._current.hide()
            section.show()
            self._current = section

    def _clearHistory(self):
        # Disable missing docstring
        # pylint: disable=C0111
        self.original_values = {}
        self.revert_button.set_sensitive(False)

    def _factorySettingsButtonCb(self, unused_button):
        """
        Reset all settings to the defaults
        """
        for section in self.prefs.values():
            for attrname in section:
                self._resetOptionCb(self.resets[attrname], attrname)

    def _revertButtonCb(self, unused_button):
        """
        Resets all settings to the values from before the user opened the
        preferences dialog.
        """
        for attrname, value in self.original_values.items():
            self.widgets[attrname].setWidgetValue(value)
            setattr(self.settings, attrname, value)
        self._clearHistory()
        self.factory_settings.set_sensitive(self._canReset())

    def _resetOptionCb(self, button, attrname):
        """
        Reset a particular setting to the factory default
        """
        if not self.settings.isDefault(attrname):
            self.settings.setDefault(attrname)
        self.widgets[attrname].setWidgetValue(getattr(self.settings, attrname))
        button.set_sensitive(False)
        self.factory_settings.set_sensitive(self._canReset())

    def _acceptButtonCb(self, unused_button):
        # Disable missing docstring
        # pylint: disable=C0111
        self._clearHistory()
        self.dialog.hide()

    def _valueChangedCb(self, unused_fake_widget, real_widget, attrname):
        # Disable missing docstring
        # pylint: disable=C0111
        value = getattr(self.settings, attrname)
        if attrname not in self.original_values:
            self.original_values[attrname] = value
            if not GlobalSettings.notifiesConfigOption(attrname):
                self.restart_warning.show()
            self.revert_button.set_sensitive(True)

        # convert the value of the widget to whatever type it is currently
        if value is not None:
            value = type(value)(real_widget.getWidgetValue())
        setattr(self.settings, attrname, value)

        # adjust controls as appropriate
        self.resets[attrname].set_sensitive(
            not self.settings.isDefault(attrname))
        self.factory_settings.set_sensitive(True)

    def _configureCb(self, unused_widget, event):
        # Disable missing docstring
        # pylint: disable=C0111
        self.settings.prefsDialogWidth = event.width
        self.settings.prefsDialogHeight = event.height

    def _canReset(self):
        # Disable missing docstring
        # pylint: disable=C0111
        for section in self.prefs.values():
            for attrname in section:
                if not self.settings.isDefault(attrname):
                    return True
        return False
