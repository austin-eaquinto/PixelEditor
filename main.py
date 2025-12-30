# main.py
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import os

# Import modules
from settings import *
from editor_tab import EditorTab
from palette_manager import PaletteManager
from project_manager import ProjectManager
from animation_preview import AnimationPreview
import icons 

print("--- SYSTEM STARTING ---")

class PixelEditor:
    def __init__(self, root):
        print("Initializing Interface...")
        self.root = root
        self.root.title("Gemini Pixel Editor v30 - Fixed")
        self.root.geometry("800x650+100+100")
        
        # GLOBAL SETTINGS
        self.rows = DEFAULT_ROWS
        self.cols = DEFAULT_COLS
        self.pixel_size = DEFAULT_PIXEL_SIZE
        
        # STATE
        self.brush_color = "#000000" 
        self.active_color = "#000000"
        self.active_tool = "brush" 
        self.show_grid = True
        self.settings_win = None
        self.current_project_path = None 

        # --- LOAD ICONS (PROGRAMMATICALLY) ---
        # This uses the new safe method from icons.py
        try:
            self.img_brush = icons.create_icon("brush")
            self.img_eraser = icons.create_icon("eraser")
            self.img_bucket = icons.create_icon("bucket")
            self.img_gemini = icons.create_icon("gemini")
            self.img_play   = icons.create_icon("play")
        except Exception as e:
            print(f"Icon Warning: {e}")
            # Fallback to prevent crash if something goes wrong
            self.img_brush = None
            self.img_eraser = None
            self.img_gemini = None

        # MANAGERS
        self.palette_manager = PaletteManager(self)
        self.project_manager = ProjectManager(self) # <--- Initialize Project Manager

        # Load Palette Config
        self.saved_palettes = self.project_manager.app.load_palettes_from_disk() if hasattr(self, 'load_palettes_from_disk') else self.load_palettes_from_disk_internal()
        self.current_palette = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", 
                                "#FFFF00", "#00FFFF", "#FF00FF", "#808080", "#C0C0C0"]
        self.palette_buttons = [] 

        self.setup_ui()
        
        self.add_new_tab("Frame 1")
        self.setup_plus_tab()

        # Bindings
        self.root.bind("<Control-z>", lambda e: self.trigger_undo())
        self.root.bind("<Control-y>", lambda e: self.trigger_redo())
        self.root.bind("<Control-s>", lambda e: self.project_manager.save_project())

        print("Interface Ready.")

    def setup_ui(self):
        top_frame = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(top_frame, text="⚙️ Grid", command=self.open_grid_settings).pack(side=tk.LEFT, padx=2)
        self.btn_grid = tk.Button(top_frame, text="Grid: ON", width=8, relief=tk.RAISED, command=self.toggle_grid)
        self.btn_grid.pack(side=tk.LEFT, padx=2)
        
        tk.Frame(top_frame, width=10).pack(side=tk.LEFT)
        tk.Button(top_frame, text="↩", width=3, command=self.trigger_undo).pack(side=tk.LEFT, padx=1)
        tk.Button(top_frame, text="↪", width=3, command=self.trigger_redo).pack(side=tk.LEFT, padx=1)

        tk.Frame(top_frame, width=10).pack(side=tk.LEFT) 
        
        # Tools
        self.btn_brush = tk.Button(top_frame, image=self.img_brush, relief=tk.SUNKEN, command=self.select_brush)
        self.btn_brush.pack(side=tk.LEFT, padx=1)
        self.btn_eraser = tk.Button(top_frame, image=self.img_eraser, command=self.select_eraser)
        self.btn_eraser.pack(side=tk.LEFT, padx=1)
        self.btn_bucket = tk.Button(top_frame, image=self.img_bucket, command=self.select_bucket)
        self.btn_bucket.pack(side=tk.LEFT, padx=1)
        self.btn_grab = tk.Button(top_frame, text="✋", width=3, command=self.select_grab)
        self.btn_grab.pack(side=tk.LEFT, padx=1)

        tk.Frame(top_frame, width=10).pack(side=tk.LEFT) 
        tk.Button(top_frame, text="🎨 Palette", command=self.palette_manager.open_window, bg="#FFEB3B").pack(side=tk.LEFT, padx=2)

        tk.Button(top_frame, text=" Play", image=self.img_play, compound=tk.LEFT, 
                  command=self.open_animation_preview).pack(side=tk.LEFT, padx=10)
        
        # File Operations (Delegated to ProjectManager)
        tk.Frame(top_frame, width=20).pack(side=tk.LEFT) 
        tk.Button(top_frame, text="📂 Load", bg="#2196F3", fg="white", 
                  command=self.project_manager.load_project_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="💾 Save", bg="#4CAF50", fg="white", 
                  command=self.project_manager.save_project).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="💾 Save As", bg="#388E3C", fg="white", 
                  command=self.project_manager.save_project_as).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text=" Export", image=self.img_gemini, compound=tk.LEFT, bg="#9C27B0", fg="white", 
                  command=self.project_manager.export_for_gemini).pack(side=tk.LEFT, padx=2)

        # Quick Palette
        self.quick_palette_frame = tk.Frame(self.root, bd=1, relief=tk.GROOVE, bg="#f0f0f0")
        self.quick_palette_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        tk.Label(self.quick_palette_frame, text="Active Palette:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.slots_frame = tk.Frame(self.quick_palette_frame, bg="#f0f0f0")
        self.slots_frame.pack(side=tk.LEFT, padx=5)
        self.refresh_quick_palette() 

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind("<Button-1>", self.on_tab_left_click)
        self.notebook.bind("<Button-3>", self.on_tab_right_click)
        self.notebook.bind("<Button-2>", self.on_tab_middle_click)

    # --- TAB SYSTEM ---
    def setup_plus_tab(self):
        tabs = self.notebook.tabs()
        if tabs and self.notebook.tab(tabs[-1], "text") == " + ": return 
        plus_frame = tk.Frame(self.notebook, bg="#dddddd")
        self.notebook.add(plus_frame, text=" + ")

    def on_tab_left_click(self, event):
        try:
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")
            if clicked_tab_index == len(self.notebook.tabs()) - 1:
                if self.notebook.tab(clicked_tab_index, "text") == " + ":
                    self.add_new_tab()
                    return "break" 
        except: pass

    def on_tab_middle_click(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            if self.notebook.tab(index, "text") != " + ": self.close_tab_by_index(index)
        except: pass

    def on_tab_right_click(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            if self.notebook.tab(index, "text") != " + ":
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Close Frame", command=lambda: self.close_tab_by_index(index))
                menu.add_command(label="Copy Code to Clipboard", 
                                 command=self.project_manager.export_active_tab) # Delegated
                menu.post(event.x_root, event.y_root)
        except: pass

    def active_tab(self):
        select_id = self.notebook.select()
        if not select_id: return None
        if self.notebook.tab(select_id, "text") == " + ": return None
        return getattr(self.root.nametowidget(select_id), "tab_obj", None)

    def add_new_tab(self, name=None):
        if name is None:
            existing = [self.notebook.tab(i, "text") for i in range(len(self.notebook.tabs()))]
            count = 1
            while f"Frame {count}" in existing: count += 1
            name = f"Frame {count}"
        new_tab = EditorTab(self.notebook, self, self.rows, self.cols, self.pixel_size, name)
        new_tab.frame.tab_obj = new_tab 
        total = len(self.notebook.tabs())
        if total > 0 and self.notebook.tab(total-1, "text") == " + ":
            self.notebook.insert(total-1, new_tab.frame, text=name)
        else:
            self.notebook.add(new_tab.frame, text=name)
            self.setup_plus_tab() 
        self.notebook.select(new_tab.frame) 

    def close_tab_by_index(self, index):
        if len(self.notebook.tabs()) <= 2: 
            self.show_toast("Cannot close the last frame.")
            return
        if messagebox.askyesno("Close Frame", "Close this frame?"):
            self.notebook.forget(index)
            self.reindex_tabs()

    def reindex_tabs(self):
        tabs = self.notebook.tabs()
        for i in range(len(tabs) - 1): 
            self.notebook.tab(tabs[i], text=f"Frame {i+1}")

    # --- UNDO / REDO ---
    def trigger_undo(self):
        tab = self.active_tab()
        if tab and tab.history:
            tab.redo_stack.append([row[:] for row in tab.grid_data])
            tab.grid_data = tab.history.pop()
            tab.draw_grid_lines()

    def trigger_redo(self):
        tab = self.active_tab()
        if tab and tab.redo_stack:
            tab.history.append([row[:] for row in tab.grid_data])
            tab.grid_data = tab.redo_stack.pop()
            tab.draw_grid_lines()

    # --- UI HELPERS ---
    def show_toast(self, message, parent=None, color="#333333"):
        target = parent if parent else self.root
        toast = tk.Label(target, text=message, bg=color, fg="white", padx=20, pady=10, font=("Arial", 10, "bold"), relief=tk.FLAT)
        toast.place(relx=0.5, rely=0.9, anchor="center")
        target.after(2000, toast.destroy)

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.btn_grid.config(text="Grid: ON" if self.show_grid else "Grid: OFF", relief=tk.RAISED if self.show_grid else tk.SUNKEN)
        if self.active_tab(): self.active_tab().draw_grid_lines()

    def select_brush(self):
        self.active_tool = "brush"; self.active_color = self.brush_color; self.update_tool_visuals()
    def select_eraser(self):
        self.active_tool = "eraser"; self.active_color = EMPTY_COLOR; self.update_tool_visuals()
    def select_grab(self):
        self.active_tool = "grab"; self.update_tool_visuals()
    def select_bucket(self):
        self.active_tool = "bucket"
        self.active_color = self.brush_color
        self.update_tool_visuals()

    def update_tool_visuals(self):
        self.btn_brush.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_eraser.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_bucket.config(relief=tk.RAISED, bg="#f0f0f0") # <--- RESET BUCKET
        self.btn_grab.config(relief=tk.RAISED, bg="#f0f0f0")
        
        if self.active_tool == "brush": self.btn_brush.config(relief=tk.SUNKEN, bg="#ddd")
        elif self.active_tool == "eraser": self.btn_eraser.config(relief=tk.SUNKEN, bg="#ddd")
        elif self.active_tool == "bucket": self.btn_bucket.config(relief=tk.SUNKEN, bg="#ddd") # <--- SET BUCKET
        elif self.active_tool == "grab": self.btn_grab.config(relief=tk.SUNKEN, bg="#ddd")

    def open_grid_settings(self):
        if self.settings_win and tk.Toplevel.winfo_exists(self.settings_win): self.settings_win.lift(); return
        self.settings_win = tk.Toplevel(self.root); self.settings_win.title("Grid Settings"); self.settings_win.geometry("300x350+150+150")
        frame = tk.Frame(self.settings_win, padx=20, pady=20); frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Cols:").pack(); self.set_cols = tk.Entry(frame); self.set_cols.insert(0, str(self.cols)); self.set_cols.pack()
        tk.Label(frame, text="Rows:").pack(); self.set_rows = tk.Entry(frame); self.set_rows.insert(0, str(self.rows)); self.set_rows.pack()
        tk.Label(frame, text="Px:").pack(); self.set_px = tk.Entry(frame); self.set_px.insert(0, str(self.pixel_size)); self.set_px.pack()
        tk.Button(frame, text="Apply", command=self.apply_grid_settings).pack(pady=10)

    def apply_grid_settings(self):
        try: new_c = int(self.set_cols.get()); new_r = int(self.set_rows.get()); new_px = int(self.set_px.get())
        except: return
        self.cols = new_c; self.rows = new_r; self.pixel_size = new_px
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == " + ": continue
            tab = getattr(self.root.nametowidget(tab_id), "tab_obj", None)
            if tab:
                tab.cols = new_c; tab.rows = new_r; tab.pixel_size = new_px
                new_grid = [[EMPTY_COLOR for _ in range(new_c)] for _ in range(new_r)]
                for r in range(min(len(tab.grid_data), new_r)):
                    for c in range(min(len(tab.grid_data[0]), new_c)): new_grid[r][c] = tab.grid_data[r][c]
                tab.grid_data = new_grid; tab.draw_grid_lines()
        self.settings_win.destroy()

    def refresh_quick_palette(self):
        for w in self.slots_frame.winfo_children(): w.destroy()
        self.palette_buttons = []
        for idx, c in enumerate(self.current_palette):
            b = tk.Button(self.slots_frame, bg=c, width=2, command=lambda c=c, i=idx: self.set_brush_from_palette(c, i))
            b.grid(row=idx//20, column=idx%20, padx=1); self.palette_buttons.append(b)

    def set_brush_from_palette(self, c, i):
        self.brush_color = c; self.select_brush()
        for idx, b in enumerate(self.palette_buttons): b.config(relief=tk.SUNKEN if idx==i else tk.RAISED)

    def load_palettes_from_disk_internal(self):
        if os.path.exists(PALETTE_FILE):
            try: return json.load(open(PALETTE_FILE))
            except: return {}
        return {}
    
    def open_animation_preview(self):
        # We just launch the class, it handles its own window
        AnimationPreview(self)

if __name__ == "__main__":
    print("Launching Window...")
    root = tk.Tk()
    app = PixelEditor(root)
    root.mainloop()