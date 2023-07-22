"""
https://stackoverflow.com/a/71380238
"""
import tkinter as tk

from ttkwidgets.autocomplete import AutocompleteCombobox


class MatchOnlyAutocompleteCombobox(AutocompleteCombobox):

    def autocomplete(self, delta=0):
        """
        Autocomplete the Combobox.

        :param delta: 0, 1 or -1: how to cycle through possible hits
        :type delta: int
        """
        if delta:  # need to delete selection otherwise we would fix the current position
            self.delete(self.position, tk.END)
        else:  # set position to end so selection starts where text entry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):  # Match case insensitively
                _hits.append(element)

        if not _hits:
            # No hits with current user text input
            self.position -= 1  # delete one character
            self.delete(self.position, tk.END)
            # Display again last matched autocomplete
            self.autocomplete(delta)
            return

        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto-completion
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)
