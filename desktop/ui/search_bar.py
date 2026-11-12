"""
SkyCast Desktop UI — Search Bar & Autocomplete Component
-------------------------------------------------------
Provides:
- Tkinter Entry field with 300ms debounced query triggering
- Autocomplete dropdown listbox
- Keyboard shortcuts: Enter to submit, Escape to clear/dismiss
- Favorite toggle button (⭐)
"""

import tkinter as tk
from typing import Callable, List, Dict, Any, Optional

class SearchBar:
    def __init__(self, parent_canvas: tk.Canvas,
                 on_search_submit: Callable[[str], None],
                 on_select_city: Callable[[Dict[str, Any]], None],
                 on_query_autocomplete: Callable[[str], None]):
        self.canvas = parent_canvas
        self.on_search_submit = on_search_submit
        self.on_select_city = on_select_city
        self.on_query_autocomplete = on_query_autocomplete

        self.debounce_timer = None
        self.autocomplete_data: List[Dict[str, Any]] = []

        # String variable for search query
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_text_changed)

        # Native Entry styled cleanly
        self.entry = tk.Entry(
            self.canvas,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg="#0F172A",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightcolor="#38BDF8",
            highlightbackground="#475569"
        )

        # Autocomplete Listbox
        self.listbox = tk.Listbox(
            self.canvas,
            font=("Segoe UI", 10),
            bg="#0F172A",
            fg="#F8FAFC",
            selectbackground="#2563EB",
            selectforeground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#38BDF8",
            activestyle="none"
        )
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self.listbox.bind("<Return>", self._on_listbox_select)

        # Key bindings
        self.entry.bind("<Return>", lambda e: self.submit())
        self.entry.bind("<Escape>", lambda e: self.clear())
        self.entry.bind("<Down>", self._focus_listbox)

    def _on_text_changed(self, *args):
        if self.debounce_timer:
            self.canvas.after_cancel(self.debounce_timer)
        self.debounce_timer = self.canvas.after(300, self._trigger_autocomplete)

    def _trigger_autocomplete(self):
        text = self.search_var.get().strip()
        if len(text) >= 2:
            self.on_query_autocomplete(text)
        else:
            self.hide_autocomplete()

    def update_suggestions(self, results: List[Dict[str, Any]], x: int, y: int, width: int):
        """Populate the suggestions listbox with returned geocoding results."""
        self.autocomplete_data = results
        self.listbox.delete(0, tk.END)

        if not results:
            self.hide_autocomplete()
            return

        for r in results:
            self.listbox.insert(tk.END, f"  📍 {r['display_name']}")

        h = min(len(results) * 26 + 10, 150)
        self.listbox.place(x=x, y=y, width=width, height=h)
        self.listbox.lift()

    def hide_autocomplete(self):
        self.listbox.place_forget()

    def _focus_listbox(self, event):
        if self.listbox.winfo_ismapped() and self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_set(0)

    def _on_listbox_select(self, event):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.autocomplete_data):
            item = self.autocomplete_data[sel[0]]
            self.search_var.set(item["name"])
            self.hide_autocomplete()
            self.on_select_city(item)

    def submit(self):
        self.hide_autocomplete()
        text = self.search_var.get().strip()
        if text:
            self.on_search_submit(text)

    def clear(self):
        self.search_var.set("")
        self.hide_autocomplete()

    def set_text(self, text: str):
        self.search_var.set(text)
        self.hide_autocomplete()
