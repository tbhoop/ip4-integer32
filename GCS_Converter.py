# Tyler's Semi-Ultimate Unit Converter with Nord Color Palette

# ------------------------------------------
# Script: GCS_Converter.py
# Author: Tbhooper
# Date: 2025-06-28
# Version: 1.0
# Description: The Semi-Ultimate Unit Converter
#              Converts between IPv4 addresses and 32-bit integers. Tailored for GCS use.
# ------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import tempfile
import shutil

# Nord color palette
BG_COLOR = "#2E3440"
FG_COLOR = "#ECEFF4"
ACCENT1 = "#88C0D0"
ACCENT2 = "#A3BE8C"
ENTRY_BG = "#3B4252"
ENTRY_FG = "#ECEFF4"
RESULT_FG = "#EBCB8B"
ERROR_FG = "#BF616A"

def ip_to_int(ip_address: str) -> int:
    parts = ip_address.strip().split('.')
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        raise ValueError("Invalid IPv4 address format")
    return sum(int(part) << (8 * (3 - i)) for i, part in enumerate(parts))

def int_to_ip(int_value: int) -> str:
    if not (0 <= int_value <= 0xFFFFFFFF):
        raise ValueError("Integer out of IPv4 range")
    return ".".join(str((int_value >> (8 * i)) & 0xFF) for i in reversed(range(4)))

class ModernUnitConverterApp(tk.Tk):
    HISTORY_FILE = "conversion_history.txt"

    def __init__(self):
        super().__init__()
        # --- ICON WORKAROUND FOR PYINSTALLER ---
        icon_path = resource_path("thumbnail.ico")
        if hasattr(sys, "_MEIPASS"):
            # Running as PyInstaller EXE: copy to a real temp file
            temp_icon = os.path.join(tempfile.gettempdir(), "thumbnail.ico")
            shutil.copyfile(icon_path, temp_icon)
            self.iconbitmap(temp_icon)
        else:
            # Running as script
            self.iconbitmap(icon_path)
        # --- END ICON WORKAROUND ---
        self.withdraw()
        self.title("GCS Unit Converter")
        self.configure(bg=BG_COLOR)
        self.history = []
        self.conv_input_history = []
        self.conv_input_index = None
        self.search_input_history = []
        self.search_input_index = None
        self._setup_styles()
        self._create_widgets()
        self._load_history_from_file()
        self.update_idletasks()
        self.minsize(400, 350)
        self.resizable(False, False)
        self.deiconify()  # Show window

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=BG_COLOR, foreground=ACCENT1)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), background=ACCENT1, foreground=BG_COLOR, padding=6, relief="flat")
        style.map("TButton",
            background=[("active", ACCENT2), ("disabled", "#636e72")],
            foreground=[("active", BG_COLOR)]
        )
        style.configure("Result.TLabel", font=("Segoe UI", 14, "bold"), background=BG_COLOR, foreground=RESULT_FG)
        style.configure("NoHover.TCheckbutton", background=BG_COLOR, foreground=ACCENT1, font=("Segoe UI", 10, "bold"))
        style.map("NoHover.TCheckbutton",
                  background=[("selected", BG_COLOR), ("active", BG_COLOR)],
                  foreground=[("selected", ACCENT1), ("active", ACCENT1)])
        style.configure("LightPlain.TCombobox",
                        fieldbackground=ENTRY_BG,
                        background=ENTRY_BG,
                        foreground=ENTRY_FG,
                        selectbackground=ENTRY_BG,
                        selectforeground=ENTRY_FG,
                        font=("Segoe UI", 10))
        style.map("LightPlain.TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  background=[("readonly", ENTRY_BG)],
                  foreground=[("readonly", ENTRY_FG)])

    def _create_widgets(self):
        ttk.Label(self, text="IP/Integer Converter", style="Header.TLabel").pack(pady=(12, 4))
        converter_frame = ttk.Frame(self, style="TFrame")
        converter_frame.pack(pady=(0, 8), padx=20, fill="x")
        converter_frame.grid_columnconfigure(1, weight=1)

        self.reverse_var = tk.BooleanVar()
        self.reverse_check = ttk.Checkbutton(
            converter_frame,
            text="Reverse (Integer → IP)",
            variable=self.reverse_var,
            style="NoHover.TCheckbutton",
            command=self._update_conversion_labels,
            takefocus=True
        )
        self.reverse_check.grid(row=0, column=0, columnspan=2, padx=(0, 0), pady=6, sticky="w")

        self.input_label = ttk.Label(converter_frame, text="", style="TLabel")
        self.input_label.grid(row=1, column=0, sticky="e", pady=6, padx=(0, 10))
        self.value_entry = tk.Entry(
            converter_frame, width=20, font=("Segoe UI", 11),
            bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ACCENT1,
            relief="flat", highlightthickness=2, highlightbackground=ACCENT1, highlightcolor=ACCENT2
        )
        self.value_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.value_entry.bind("<Return>", lambda e: self._convert_units())
        self.value_entry.bind("<Enter>", lambda e: self.value_entry.focus_set())
        self.value_entry.bind("<Up>", self._conv_input_up)
        self.value_entry.bind("<Down>", self._conv_input_down)
        self.value_entry.bind("<KeyRelease>", self._conv_input_store)
        self.value_entry.focus_set()

        self.convert_btn = ttk.Button(converter_frame, text="Convert", command=self._convert_units)
        self.convert_btn.grid(row=1, column=2, padx=(10, 0), pady=6)

        self.output_label = ttk.Label(converter_frame, text="", style="TLabel")
        self.output_label.grid(row=2, column=0, sticky="e", pady=6, padx=(0, 10))
        self.conv_result_label = ttk.Label(
            converter_frame,
            text="",
            style="Result.TLabel",
            font=("Segoe UI", 14, "bold"),
            background=BG_COLOR,
            foreground=RESULT_FG,
            anchor="w",
            justify="left"
        )
        self.conv_result_label.grid(
            row=2, column=1, columnspan=2,
            pady=(4, 0), sticky="ew", ipadx=4, ipady=4
        )
        self._update_conversion_labels()

        # --- Search History Section ---
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=8, padx=20)
        ttk.Label(self, text="Conversion History", style="Header.TLabel").pack(pady=(0, 6))

        # Search bar, matching conversion input box size
        search_frame = tk.Frame(self, bg=BG_COLOR)
        search_frame.pack(pady=(0, 0), padx=20, fill="x")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=20,
            bg=ENTRY_BG,
            fg="#aaa",
            insertbackground=ACCENT1,
            relief="flat",
            highlightthickness=2,
            highlightbackground=ACCENT1,
            highlightcolor=ACCENT2,
            font=("Segoe UI", 11)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=0, pady=6)
        self.search_entry.insert(0, "Type to search...")

        def on_focus_in(event):
            if self.search_entry.get() == "Type to search...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(fg=ENTRY_FG, font=("Segoe UI", 11, "normal"))
            self.search_entry.config(bg="#434C5E", highlightbackground=ACCENT2)

        def on_focus_out(event):
            if not self.search_entry.get():
                self.search_entry.insert(0, "Type to search...")
                self.search_entry.config(fg="#aaa", font=("Segoe UI", 11, "italic"))
            self.search_entry.config(bg=ENTRY_BG, highlightbackground=ACCENT1)

        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)
        self.search_entry.bind("<KeyRelease>", self._search_history)
        self.search_entry.bind("<Enter>", lambda e: self.search_entry.focus_set())
        self.search_entry.bind("<Up>", self._search_input_up)
        self.search_entry.bind("<Down>", self._search_input_down)
        self.search_entry.bind("<Return>", self._search_input_store)

        self.history_listbox = tk.Listbox(
            self,
            height=5,
            font=("Segoe UI", 9),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            highlightbackground=ACCENT1,
            selectbackground=ACCENT2,
            relief="flat",
            borderwidth=0
        )
        self.history_listbox.pack(padx=20, fill="x", pady=(0, 10))

    # --- Conversion logic and history ---
    def _search_history(self, event=None):
        query = self.search_var.get().lower()
        if query:
            # Search the file for all history
            if os.path.exists(self.HISTORY_FILE):
                try:
                    with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                        all_lines = [line.strip() for line in f.readlines()]
                except Exception:
                    all_lines = []
            else:
                all_lines = []
            filtered = [line for line in all_lines if query in line.lower()]
        else:
            # Show only current session history (last 10)
            filtered = self.history[-10:]

        self.history_listbox.delete(0, tk.END)
        for item in reversed(filtered):
            self.history_listbox.insert(tk.END, item)

    def _add_history(self, entry):
        self.history.append(entry)
        if len(self.history) > 10:
            self.history.pop(0)
        self._append_history_to_file(entry)
        self.search_var.set("")  # Clear search box after each calculation
        self._search_history()

    def _append_history_to_file(self, entry):
        try:
            with open(self.HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass

    def _load_history_from_file(self):
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                self.history = [line.strip() for line in lines[-10:]]
                self._search_history()
            except Exception:
                pass

    def _update_conversion_labels(self, event=None):
        reverse = self.reverse_var.get()
        if reverse:
            self.input_label.config(text="32-bit Integer:")
            self.output_label.config(text="IP Address:")
        else:
            self.input_label.config(text="IP Address:")
            self.output_label.config(text="32-bit Integer:")
        self.value_entry.delete(0, tk.END)
        self.conv_result_label.config(text="")

    def _convert_units(self):
        reverse = self.reverse_var.get()
        value_str = self.value_entry.get().strip()
        try:
            if reverse:
                value = int(value_str)
                result = int_to_ip(value)
                display = str(result)
                input_label = "32-bit Integer"
                output_label = "IP Address"
                # Extract third octet from result IP
                third_octet = result.split(".")[2] if len(result.split(".")) == 4 else "??"
            else:
                value = value_str
                result = ip_to_int(value)
                display = str(result)
                input_label = "IP Address"
                output_label = "32-bit Integer"
                # Extract third octet from input IP
                third_octet = value.split(".")[2] if len(value.split(".")) == 4 else "??"
            vb_code = f"🚀 VB-2000{third_octet}"
            history_entry = f"{input_label}: {value_str} → {output_label}: {display}    {vb_code}"
            self.conv_result_label.config(text=display, foreground=RESULT_FG)
            self._add_history(history_entry)
        except Exception:
            if reverse:
                msg = "Enter a valid 32-bit integer (0-4294967295)."
            else:
                msg = "Enter a valid IPv4 address."
            self.conv_result_label.config(
                text=msg,
                foreground=ERROR_FG
            )
            # Still try to extract third octet for error entry
            try:
                if reverse:
                    result_ip = int_to_ip(int(value_str))
                    third_octet = result_ip.split(".")[2] if len(result_ip.split(".")) == 4 else "??"
                else:
                    third_octet = value_str.split(".")[2] if len(value_str.split(".")) == 4 else "??"
            except Exception:
                third_octet = "??"
            vb_code = f"🚀 VB-2000{third_octet}"
            error_entry = f"{input_label}: {value_str} → Error    {vb_code}"
            self._add_history(error_entry)
        self.value_entry.focus_set()

    # --- Conversion input history handlers ---
    def _conv_input_store(self, event):
        if event.keysym == "Return":
            value = self.value_entry.get().strip()
            if value and (not self.conv_input_history or value != self.conv_input_history[-1]):
                self.conv_input_history.append(value)
            self.conv_input_index = None  # Reset index after entry

    def _conv_input_up(self, event):
        if not self.conv_input_history:
            return "break"
        if self.conv_input_index is None:
            self.conv_input_index = len(self.conv_input_history) - 1
        elif self.conv_input_index > 0:
            self.conv_input_index -= 1
        self.value_entry.delete(0, tk.END)
        self.value_entry.insert(0, self.conv_input_history[self.conv_input_index])
        self.value_entry.icursor(tk.END)
        return "break"

    def _conv_input_down(self, event):
        if self.conv_input_index is None:
            return "break"
        if self.conv_input_index < len(self.conv_input_history) - 1:
            self.conv_input_index += 1
            self.value_entry.delete(0, tk.END)
            self.value_entry.insert(0, self.conv_input_history[self.conv_input_index])
            self.value_entry.icursor(tk.END)
        else:
            self.value_entry.delete(0, tk.END)
            self.conv_input_index = None
        return "break"

    # --- Search input history handlers ---
    def _search_input_store(self, event):
        value = self.search_entry.get().strip()
        if value and (not self.search_input_history or value != self.search_input_history[-1]):
            self.search_input_history.append(value)
        self.search_input_index = None

    def _search_input_up(self, event):
        if not self.search_input_history:
            return "break"
        if self.search_input_index is None:
            self.search_input_index = len(self.search_input_history) - 1
        elif self.search_input_index > 0:
            self.search_input_index -= 1
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, self.search_input_history[self.search_input_index])
        self.search_entry.icursor(tk.END)
        return "break"

    def _search_input_down(self, event):
        if self.search_input_index is None:
            return "break"
        if self.search_input_index < len(self.search_input_history) - 1:
            self.search_input_index += 1
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, self.search_input_history[self.search_input_index])
            self.search_entry.icursor(tk.END)
        else:
            self.search_entry.delete(0, tk.END)
            self.search_input_index = None
        return "break"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    ModernUnitConverterApp().mainloop()