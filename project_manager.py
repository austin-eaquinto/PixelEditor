# project_manager.py
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import re
from settings import *
from editor_tab import EditorTab

class ProjectManager:
    """Handles all File I/O: Saving, Loading, and Exporting."""
    
    def __init__(self, app_ref):
        self.app = app_ref 

    # --- SAVE SYSTEM ---
    def save_project(self):
        if not self.app.current_project_path:
            self.save_project_as()
        else:
            self._perform_save(self.app.current_project_path)

    def save_project_as(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Project (Type a Name for the Folder)",
            initialfile="project_data.json",
            filetypes=[("Project Data", "project_data.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        if not file_path: return
        
        filename = os.path.basename(file_path)
        
        if filename == "project_data.json":
            # Scenario A: User navigated INTO a folder and clicked 'Save'
            folder_path = os.path.dirname(file_path)
        else:
            # Scenario B: User typed a name like "MyGame"
            # We treat "MyGame" as the folder name
            folder_path = os.path.splitext(file_path)[0] 
        
        self.app.current_project_path = folder_path
        self._perform_save(folder_path)

    def _perform_save(self, folder_path):
        meta_data = {
            "rows": self.app.rows, 
            "cols": self.app.cols, 
            "pixel_size": self.app.pixel_size,
            "palette": self.app.current_palette
        }
        try:
            os.makedirs(folder_path, exist_ok=True)

            json_path = os.path.join(folder_path, "project_data.json")
            with open(json_path, "w") as f:
                json.dump(meta_data, f, indent=4)
            
            if os.path.exists(folder_path):
                for f in os.listdir(folder_path):
                    if f.startswith("frame_") and f.endswith(".txt"): 
                        os.remove(os.path.join(folder_path, f))

            tabs = self.app.notebook.tabs()
            for i in range(len(tabs) - 1): 
                tab_widget = self.app.root.nametowidget(tabs[i])
                tab = getattr(tab_widget, "tab_obj", None)
                if tab:
                    content = self.generate_tab_content(tab)
                    filename = f"frame_{i+1}.txt"
                    with open(os.path.join(folder_path, filename), "w") as f: 
                        f.write(content)
            
            project_name = os.path.basename(folder_path)
            self.app.root.title(f"Gemini Pixel Editor - [{project_name}]")
            self.app.show_toast(f"Saved to '{project_name}'")
            
        except Exception as e: 
            messagebox.showerror("Save Error", f"Could not save project:\n{str(e)}")

    # --- LOAD SYSTEM ---
    # --- LOAD SYSTEM ---
    def load_project_folder(self):
        # CHANGED: The first entry is the DEFAULT.
        # We list "*.json *.txt" together so both appear immediately.
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[
                ("Project Files", "*.json *.txt"), 
                ("All Files", "*.*")
            ]
        )
        
        if not file_path: return
        
        # Robustness: We find the folder regardless of which file they clicked.
        folder_path = os.path.dirname(file_path)
        
        try:
            meta_path = os.path.join(folder_path, "project_data.json")
            
            if not os.path.exists(meta_path):
                messagebox.showerror("Error", "Could not find 'project_data.json' in this folder.\nPlease select the main project file.")
                return
            
            with open(meta_path, "r") as f: meta = json.load(f)
            
            # Apply Settings
            self.app.rows = meta.get("rows", 33)
            self.app.cols = meta.get("cols", 45)
            self.app.pixel_size = meta.get("pixel_size", 15)
            self.app.current_palette = meta.get("palette", self.app.current_palette)
            self.app.refresh_quick_palette()
            
            # Clear existing tabs
            for tab in self.app.notebook.tabs(): 
                self.app.notebook.forget(tab)
            
            # Load Files
            files = []
            for f in os.listdir(folder_path):
                if f.startswith("frame_") and f.endswith(".txt"):
                    if re.search(r'\d+', f):
                        files.append(f)
            
            files.sort(key=lambda x: int(re.search(r'\d+', x).group()))

            if not files:
                self.app.add_new_tab("Frame 1") 
            else:
                for i, filename in enumerate(files):
                    self.load_frame_file(os.path.join(folder_path, filename), f"Frame {i+1}")
            
            self.app.setup_plus_tab() 
            self.app.current_project_path = folder_path
            self.app.root.title(f"Gemini Pixel Editor - [{os.path.basename(folder_path)}]")
            self.app.show_toast("Project Loaded!")
        except Exception as e: 
            messagebox.showerror("Load Error", f"Error loading project:\n{str(e)}")

    def load_frame_file(self, filepath, title):
        new_tab = EditorTab(self.app.notebook, self.app, self.app.rows, self.app.cols, self.app.pixel_size, title)
        new_tab.frame.tab_obj = new_tab 
        self.app.notebook.add(new_tab.frame, text=title) 
        
        with open(filepath, "r") as f: content = f.read()
        grid_match = re.search(r'my_pixel_art\s*=\s*"""(.*?)"""', content, re.DOTALL)
        if not grid_match: return 
        
        pal_match = re.search(r"palette\s*=\s*\{(.*?)\}", content, re.DOTALL)
        file_map = {}
        if pal_match:
            raw_pal_str = pal_match.group(1)
            for sym, hex_val in re.findall(r"'(\S)':\s*'([^']*)'", raw_pal_str):
                if hex_val == 'Transparent': hex_val = EMPTY_COLOR
                file_map[sym] = hex_val
                
        raw_grid = grid_match.group(1).strip().split('\n')
        for r, line in enumerate(raw_grid):
            if r < self.app.rows:
                for c, char in enumerate(line):
                    if c < self.app.cols and char in file_map: 
                        new_tab.grid_data[r][c] = file_map[char]
        new_tab.draw_grid_lines()

    # --- EXPORT SYSTEM ---
    def generate_tab_content(self, tab):
        unique_colors = set()
        for row in tab.grid_data:
            for cell in row:
                if cell != EMPTY_COLOR: unique_colors.add(cell)
        
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%&*"
        color_map = {}
        legend_str = "palette = {\n    '.': 'Transparent',\n"
        for i, color in enumerate(sorted(unique_colors)):
            sym = symbols[i] if i < len(symbols) else "?"
            color_map[color] = sym
            legend_str += f"    '{sym}': '{color}',\n"
        legend_str += "}"
        
        ascii_art = 'my_pixel_art = """\n'
        for row in tab.grid_data:
            line = ""
            for cell in row:
                line += "." if cell == EMPTY_COLOR else color_map[cell]
            ascii_art += line + "\n"
        ascii_art += '"""'
        return f"{legend_str}\n\n{ascii_art}"

    def export_active_tab(self):
        tab = self.app.active_tab()
        if tab:
            content = self.generate_tab_content(tab)
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(content)
            self.app.show_toast("Code Copied!")

    def export_for_gemini(self):
        path = filedialog.asksaveasfilename(
            title="Export for Gemini", 
            initialfile="gemini_context.txt", 
            filetypes=[("Text File", "*.txt")]
        )
        if not path: return
        
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%&*"
        symbol_map = {}
        legend = ["### GLOBAL PALETTE LEGEND ###", ".: Transparent"]
        
        for i, color in enumerate(self.app.current_palette):
            if i < len(symbols):
                symbol_map[color] = symbols[i]
                legend.append(f"{symbols[i]}: {color}")
                
        content = ["\n".join(legend), "\n" + "="*30 + "\n"]
        
        tabs = self.app.notebook.tabs()
        for i in range(len(tabs) - 1):
            tab = getattr(self.app.root.nametowidget(tabs[i]), "tab_obj", None)
            if tab:
                content.append(f"### FRAME {i+1} ###")
                for row in tab.grid_data:
                    content.append("".join("." if c == EMPTY_COLOR else symbol_map.get(c, "?") for c in row))
                content.append("-" * 20 + "\n")
                
        with open(path, "w") as f: f.write("\n".join(content))
        self.app.show_toast("Exported for Gemini!")