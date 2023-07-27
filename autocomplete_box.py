"""
https://stackoverflow.com/a/71380238
"""
import tkinter as tk
from tkinter import ttk


import pandas as pd
from thefuzz import fuzz
from ttkwidgets.autocomplete import AutocompleteCombobox

class ResizingCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        # self.scale("all", 0, 0, wscale, hscale)




class AutoScrollbar(tk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class ZoomFrame(tk.Frame):
    ''' Simple zoom with mouse wheel '''
    def __init__(self, mainframe, *args, **kwargs):
        ''' Initialize the main Frame '''
        super().__init__(mainframe, *args, **kwargs)
        # self.master.title('Simple zoom with mouse wheel')
        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self, orient='vertical')
        hbar = AutoScrollbar(self, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        vbar.configure(command=self.canvas.yview)  # bind scrollbars to the canvas
        hbar.configure(command=self.canvas.xview)
        # # Make the canvas expandable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>', self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>', self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>', self.wheel)  # only with Linux, wheel scroll up

        self.imscale = 1.0
        self.imageid = None
        self.delta = 0.75

        # # Text is used to set proper coordinates to the image. You can make it invisible.
        # self.text = self.canvas.create_text(0, 0, anchor='nw', text='Scroll to zoom')
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:
            scale        *= self.delta
            self.imscale *= self.delta
        if event.num == 4 or event.delta == 120:
            scale        /= self.delta
            self.imscale /= self.delta
        # Rescale all canvas objects
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale('all', x, y, scale, scale)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))


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



class FuzzyAutoComplete(tk.Frame):
    def __init__(self, parent, values, textvariable, width):
        super().__init__(parent, width=width)
        self.entry = tk.Entry(self, textvariable=textvariable, width=width)
        self.parent = parent
        self.entry_variable = textvariable

        self.lbframe = tk.Frame(self)
        self.choicesvar = tk.StringVar(value=values)
        self.list = tk.Listbox(self.lbframe, listvariable=self.choicesvar, width=width)
        self.list.pack()
        self.typed_text = ""

        self.entry.grid(row=0, column=0)

        self.rowconfigure(0, weight=1)


        self.entry.bind("<KeyRelease>", self.autocomplete)
        self.entry.bind("<Down>", self.down_to_list)
        self.entry.bind("<FocusIn>", self.up_to_entry)
        self.list.bind("<Up>", self.up_to_entry)
        self.list.bind("<<ListboxSelect>>", self.select_choice)
        self.list.bind("<FocusOut>", lambda _: self.enable_text())
        self._all_values = values

    def bind(self, key, function):
        super().bind(key, function)
        if key == "<Return>":
            self.entry.bind(key, function)
            self.list.bind(key, function)

    def down_to_list(self, event):
        self.entry["state"] = "disabled"
        self.list.select_set(0)
        self.list.focus_set()
        self.list.event_generate("<<ListboxSelect>>")
        self.show_list()

    def up_to_entry(self, event):
        selection = self.list.curselection()
        if selection and (selection[0] == 0):
            self.enable_text()
            self.entry.focus_set()
            self.entry_variable.set(self.typed_text)
            self.entry.icursor(len(self.typed_text))
            self.hide_list()

    def enable_text(self):
        self.entry["state"] = "normal"

    def autocomplete(self, event):
        """Autocomplete the Combobox."""
        # Store in case we move in and out of list.
        self.typed_text = self.entry.get()
        entry_lower = self.entry.get().lower()
        results = pd.Series([
            max(
                fuzz.partial_ratio(entry_lower, c.lower()),
                fuzz.ratio(entry_lower, c.lower()[:len(entry_lower)])
            )
            for c in self._all_values
        ], index=self._all_values,
        )
        self.choicesvar.set(results.sort_values(ascending=False).index[:5].tolist())

        self.show_list()

    def focus_set(self):
        super().focus_set()
        self.entry.focus_set()
    def show_list(self):
        self.lbframe.place(in_=self.entry, x=0, rely=1, relwidth=1.0, anchor="nw")
        self.lbframe.lift()

    def hide_list(self):
        self.lbframe.place_forget()

    def select_choice(self, event):
        if self.list.focus_get() is self.list:
            selection = self.list.curselection()
            index = selection[0]
            data = event.widget.get(index)
            self.entry_variable.set(data)

    def reset_text(self):
        self.entry_variable.set("")
        self.enable_text()
        self.typed_text = ""
        self.focus_set()

    @property
    def completion_list(self):
        return self._all_values

    @completion_list.setter
    def completion_list(self, values):
        self._all_values = values
