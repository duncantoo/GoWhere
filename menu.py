
import tkinter as ttk
from ttkwidgets import autocomplete

import autocomplete_box
from autocomplete_box import FuzzyAutoComplete


class Menu:
    def __init__(self, master_frame, country_names, make_guess_fn, verify_results_fn):
        self.master_frame = master_frame
        self._score = 0
        self._progress = 0
        self._all_names = country_names
        
        self._user_entry_text = ttk.StringVar()
        self._country_text = ttk.StringVar()
        self._instruction_text = ttk.StringVar()
        self._progress_text = ttk.StringVar()
        self._score_text = ttk.StringVar()

        # self._user_entry_box = autocomplete.AutocompleteCombobox(
        #     master_frame,
        #     completevalues=sorted(country_names),
        #     textvariable=self._user_entry_text,
        #     width=25,
        # )
        self._user_entry_box = FuzzyAutoComplete(
            master_frame,
            values=sorted(country_names.to_list()),
            textvariable=self._user_entry_text,
            width=25,
        )
        self._user_entry_box.focus_set()
        self._instruction_label = ttk.Label(master_frame, textvariable=self._instruction_text, width=15, fg="grey")
        self._country_label = ttk.Label(master_frame, textvariable=self._country_text, width=20, fg="grey")
        self._progress_label = ttk.Label(master_frame, textvariable=self._progress_text, width=15)
        self._verify_button = ttk.Button(master_frame, text="Verify")
        self._score_label = ttk.Label(master_frame, textvariable=self._score_text)

        self._user_entry_box.bind("<<ComboboxSelected>>", lambda e: make_guess_fn(self._user_entry_text.get()))
        self._user_entry_box.bind("<Return>", lambda e: make_guess_fn(self._user_entry_text.get()))
        self._verify_button.bind("<ButtonRelease-1>", lambda e: verify_results_fn())

        self._instruction_label.grid(row=0, column=0)
        self._user_entry_box.grid(row=0, column=1)
        self._country_label.grid(row=0, column=2)
        self._progress_label.grid(row=0, column=3)
        self._verify_button.grid(row=0, column=4)
        self._score_label.grid(row=0, column=5)

        master_frame.grid_columnconfigure(0, weight=2)
        master_frame.grid_columnconfigure(1, weight=1)
        master_frame.grid_columnconfigure(2, weight=1)
        master_frame.grid_columnconfigure(3, weight=0)
        master_frame.grid_columnconfigure(4, weight=0)
        master_frame.grid_columnconfigure(5, weight=0)

        # Initialise the text via property setters.
        self.score = 0
        self.progress = 0
        
    @property
    def score(self):
        return self._score
    
    @score.setter
    def score(self, score):
        self._score = score
        self._score_text.set(f"Score: {score}")
        
    @property
    def progress(self):
        return self._progress
    
    @progress.setter
    def progress(self, progress):
        self._progress = progress
        self._progress_text.set(f"Progress: {progress}/{len(self._all_names)}")
        
    def display_country(self, name):
        self._country_text.set(name)

    @property
    def instruction_text(self):
        return self._instruction_text.get()

    @instruction_text.setter
    def instruction_text(self, text):
        self._instruction_text.set(text)
        
    @property
    def user_entry(self):
        return self._user_entry_text.get()

    def reset_user_entry(self):
        self._user_entry_box.reset_text()
    
    def remove_country_option(self, name):
        # self._user_entry_box.set_completion_list(list(set(self._user_entry_box._completion_list) - {name}))
        self._user_entry_box.completion_list = list(set(self._user_entry_box.completion_list) - {name})

    def add_country_option(self, name):
        # self._user_entry_box.set_completion_list(list(set(self._user_entry_box._completion_list) | {name}))
        self._user_entry_box.completion_list = list(set(self._user_entry_box.completion_list) | ({name} & set(self._all_names)))
