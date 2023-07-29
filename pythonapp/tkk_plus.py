"""
https://stackoverflow.com/a/71380238
"""

import tkinter as tk

import numpy as np
import pandas as pd
from thefuzz import fuzz


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

class FuzzyAutoComplete(tk.Entry):
    def __init__(self, parent, values, textvariable, width):
        super().__init__(parent, textvariable=textvariable, width=width)
        self.parent = parent
        self.entry_variable = textvariable

        self.remaining_choices = values
        self.all_choices = values
        self._index = 0
        self.typed_text = ""

        self.bind("<KeyRelease>", self.autocomplete)
        self.bind("<Tab>", lambda _: self.scroll_through_choices(1))
        self.bind("<Shift-KeyPress-Tab>", lambda _: self.scroll_through_choices(-1))

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        """Index of 0 means the text entry. Index bigger than 0 corresponds to remaining_choices[index - 1]."""
        index = np.clip(index, 0, len(self.remaining_choices) + 1)
        if index == 0:
            self["state"] = "normal"
            self.entry_variable.set(self.typed_text)
            self.icursor(len(self.typed_text))
        else:
            self["state"] = "disabled"
            self.entry_variable.set(self.remaining_choices[index - 1])
        self._index = index

    def scroll_through_choices(self, step):
        self.index += step

    def autocomplete(self, event):
        """Autocomplete the Combobox."""
        if self["state"] == "disabled":
            return
        # Store in case we move in and out of list.
        self.typed_text = self.entry_variable.get()
        entry_lower = self.typed_text.lower()
        results = pd.Series([
            max(
                fuzz.partial_ratio(entry_lower, c.lower()),
                fuzz.ratio(entry_lower, c.lower()[:len(entry_lower)])
            )
            for c in self.remaining_choices
        ], index=self.remaining_choices,
        )
        self.remaining_choices = results.sort_values(ascending=False).index.tolist()

    def reset_text(self):
        self.entry_variable.set("")
        self.typed_text = ""
        self.index = 0
        self.focus_set()
