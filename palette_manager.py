# palette_manager.py
import tkinter as tk
from tkinter import colorchooser, messagebox, simpledialog, ttk
import json
import re
from settings import *

class PaletteManager:
    """Handles loading, saving, and editing palettes."""
    def __init__(self, app_ref):
        self.app = app_ref 
        self.pal_win = None
    
    def open_window(self):
        # 1. IF WINDOW EXISTS: Just show it and update colors. 
        if self.pal_win and tk.Toplevel.winfo_exists(self.pal_win): 
            self.refresh_manager_slots() 
            self.pal_win.deiconify()     
            return

        # 2. IF NEW: Create the window
        self.pal_win = tk.Toplevel(self.app.root)
        self.pal_win.withdraw() 
        
        # HIDE instead of destroy on close
        self.pal_win.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.pal_win.transient(self.app.root) 
        
        self.pal_win.title("Palette Manager")
        self.pal_win.geometry("600x450+150+150")
        self.pal_win.resizable(False, False)
        
        # Load/Save Frame
        frame_load = tk.LabelFrame(self.pal_win, text="Manage Saved Palettes", padx=10, pady=10)
        frame_load.pack(fill=tk.X, padx=10, pady=5)
        
        self.p_combo = ttk.Combobox(frame_load, values=list(self.app.saved_palettes.keys()), state="readonly")
        self.p_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.p_combo.bind("<<ComboboxSelected>>", self.load_palette_to_app)

        tk.Button(frame_load, text="Load", command=lambda: self.load_palette_to_app(None)).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_load, text="Delete", fg="red", command=self.delete_palette).pack(side=tk.LEFT, padx=2)

        # Edit Frame
        frame_edit = tk.LabelFrame(self.pal_win, text="Edit Palette Colors", padx=10, pady=10)
        frame_edit.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ctrl_frame = tk.Frame(frame_edit)
        ctrl_frame.pack(fill=tk.X, pady=5)
        tk.Label(ctrl_frame, text="Color Count:").pack(side=tk.LEFT)
        self.pal_size_entry = tk.Entry(ctrl_frame, width=5)
        self.pal_size_entry.insert(0, str(len(self.app.current_palette)))
        self.pal_size_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl_frame, text="Resize Palette", command=self.resize_palette).pack(side=tk.LEFT)

        tk.Label(ctrl_frame, text="(L-Click: Wheel | R-Click: Hex)", fg="gray").pack(side=tk.RIGHT)

        self.manager_slots_frame = tk.Frame(frame_edit)
        self.manager_slots_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.refresh_manager_slots()
        
        self.pal_win.update_idletasks()
        self.pal_win.deiconify()

    def hide_window(self):
        self.pal_win.withdraw()

    def resize_palette(self):
        try: 
            new_size = int(self.pal_size_entry.get())
            if new_size < 1: raise ValueError
        except: 
            messagebox.showerror("Error", "Invalid number.", parent=self.pal_win)
            return
            
        current = len(self.app.current_palette)
        if new_size > current: 
            self.app.current_palette += ["#FFFFFF"] * (new_size - current)
        elif new_size < current: 
            self.app.current_palette = self.app.current_palette[:new_size]
            
        self.refresh_manager_slots()
        self.app.refresh_quick_palette()

    def refresh_manager_slots(self):
        """
        Updates button colors and fixes the 'disappearing hover' bug
        by setting activebackground same as bg.
        """
        existing_buttons = self.manager_slots_frame.winfo_children()
        total_needed = len(self.app.current_palette)
        
        MAX_COLS = 10

        # 1. Update EXISTING buttons
        for i in range(min(len(existing_buttons), total_needed)):
            color = self.app.current_palette[i]
            # FIX: activebackground must match bg to prevent white flash on hover
            existing_buttons[i].config(bg=color, activebackground=color)

        # 2. Create NEW buttons if needed
        if total_needed > len(existing_buttons):
            for idx in range(len(existing_buttons), total_needed):
                color = self.app.current_palette[idx]
                row = idx // MAX_COLS
                col = idx % MAX_COLS
                
                # FIX: Set activebackground initially too
                btn = tk.Button(self.manager_slots_frame, bg=color, activebackground=color, 
                                width=4, height=2, relief=tk.RAISED)
                btn.bind("<Button-1>", lambda e, i=idx: self.edit_color_visual(i))
                btn.bind("<Button-3>", lambda e, i=idx: self.edit_color_hex(i))
                btn.grid(row=row, column=col, padx=2, pady=2)

        # 3. Destroy EXTRA buttons
        if total_needed < len(existing_buttons):
            for i in range(total_needed, len(existing_buttons)):
                existing_buttons[i].destroy()

    def edit_color_visual(self, index):
        current_color = self.app.current_palette[index]
        # Code pauses here while picker is open
        color_code = colorchooser.askcolor(title=f"Pick Color for Slot {index+1}", color=current_color)[1]
        
        if color_code:
            self.app.current_palette[index] = color_code
            self.refresh_manager_slots() 
            self.app.refresh_quick_palette()
            # FIX: Force immediate repaint so user sees change instantly
            self.pal_win.update()

    def edit_color_hex(self, index):
        current_color = self.app.current_palette[index]
        hex_input = simpledialog.askstring("Edit Color", f"Edit Slot {index+1}\nEnter Hex (e.g. #FF0000):", initialvalue=current_color, parent=self.pal_win)
        
        if hex_input:
            hex_input = hex_input.strip()
            if not hex_input.startswith("#"): hex_input = "#" + hex_input
            
            if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_input): 
                self.app.current_palette[index] = hex_input
                self.refresh_manager_slots() 
                self.app.refresh_quick_palette()
                # FIX: Force immediate repaint
                self.pal_win.update()
            else:
                messagebox.showerror("Invalid Hex", "Invalid hex code.", parent=self.pal_win)

    def save_palette_to_disk(self):
        name = simpledialog.askstring("Save Palette", "Name:", parent=self.pal_win)
        
        if name:
            self.app.saved_palettes[name] = list(self.app.current_palette)
            
            with open(PALETTE_FILE, "w") as f:
                json.dump(self.app.saved_palettes, f)
            
            self.p_combo['values'] = list(self.app.saved_palettes.keys())
            self.p_combo.set(name)
            self.app.show_toast(f"Palette '{name}' saved!", parent=self.pal_win)

    def load_palette_to_app(self, event):
        name = self.p_combo.get()
        if name in self.app.saved_palettes:
            self.app.current_palette = list(self.app.saved_palettes[name])
            self.pal_size_entry.delete(0, tk.END)
            self.pal_size_entry.insert(0, str(len(self.app.current_palette)))
            self.refresh_manager_slots()
            self.app.refresh_quick_palette()
            self.pal_win.update() # Force repaint

    def delete_palette(self):
        name = self.p_combo.get()
        if name in self.app.saved_palettes:
            if messagebox.askyesno("Confirm", f"Delete '{name}'?", parent=self.pal_win):
                del self.app.saved_palettes[name]
                
                with open(PALETTE_FILE, "w") as f:
                    json.dump(self.app.saved_palettes, f)
                
                self.p_combo['values'] = list(self.app.saved_palettes.keys())
                self.p_combo.set('')
                
                self.app.current_palette = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF", "#808080", "#C0C0C0"]
                self.pal_size_entry.delete(0, tk.END); self.pal_size_entry.insert(0, "10")
                self.refresh_manager_slots()
                self.app.refresh_quick_palette()
                self.pal_win.update()