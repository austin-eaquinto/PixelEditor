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

# Tool Imports
from tools.brush import BrushTool
from tools.eraser import EraserTool
from tools.bucket import BucketTool
from tools.line import LineTool
from tools.wand import MagicWandTool
from tools.select import SelectTool
from tools.grab import GrabTool

print("--- SYSTEM STARTING ---")

class PixelEditor:
    def __init__(self, root):
        print("Initializing Interface...")
        self.root = root
        self.root.title("Gemini Pixel Editor v39 - Responsive")
        
        # --- ISSUE 4 FIX: DYNAMIC SIZING ---
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 1. Calculate Window Size (85% of screen)
        win_width = int(screen_width * 0.85)
        win_height = int(screen_height * 0.85)
        x_pos = int((screen_width - win_width) / 2)
        y_pos = int((screen_height - win_height) / 2)
        self.root.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")
        
        # 2. Calculate Grid Size based on Window Size
        # We subtract approx 150px for toolbars/padding to ensure grid fits
        self.pixel_size = DEFAULT_PIXEL_SIZE
        available_w = win_width - 60  
        available_h = win_height - 140 
        
        self.cols = available_w // self.pixel_size
        self.rows = available_h // self.pixel_size
        
        # STATE
        self.brush_color = "#000000" 
        self.active_color = "#000000"
        self.show_grid = True
        self.settings_win = None
        self.current_project_path = None 
        self.clipboard = None 
        self.preview_window = None 

        # --- INITIALIZE TOOLS ---
        self.tool_instances = {
            "brush": BrushTool(self),
            "eraser": EraserTool(self),
            "bucket": BucketTool(self),
            "line": LineTool(self),
            "wand": MagicWandTool(self),
            "select": SelectTool(self),
            "grab": GrabTool(self)
        }
        self.active_tool = self.tool_instances["brush"]

        # --- LOAD ICONS ---
        try:
            self.img_brush = icons.create_icon("brush")
            self.img_eraser = icons.create_icon("eraser")
            self.img_bucket = icons.create_icon("bucket")
            self.img_select = icons.create_icon("select")
            self.img_line   = icons.create_icon("line")
            self.img_wand   = icons.create_icon("magic_wand")
            self.img_gemini = icons.create_icon("gemini")
            self.img_play   = icons.create_icon("play")
        except Exception as e:
            print(f"Icon Warning: {e}")
            self.img_brush = None

        # MANAGERS
        self.palette_manager = PaletteManager(self)
        self.project_manager = ProjectManager(self)

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
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-v>", self.paste_selection)
        
        for widget in [self.root, self.notebook]:
            widget.bind("<Left>", lambda e: self.nudge_selection(0, -1))
            widget.bind("<Right>", lambda e: self.nudge_selection(0, 1))
            widget.bind("<Up>", lambda e: self.nudge_selection(-1, 0))
            widget.bind("<Down>", lambda e: self.nudge_selection(1, 0))

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
        self.btn_line = tk.Button(top_frame, image=self.img_line, command=self.select_line)
        self.btn_line.pack(side=tk.LEFT, padx=1)
        self.btn_wand = tk.Button(top_frame, image=self.img_wand, command=self.select_magic_wand)
        self.btn_wand.pack(side=tk.LEFT, padx=1)

        self.btn_select = tk.Button(top_frame, image=self.img_select, command=self.select_selection_tool)
        self.btn_select.pack(side=tk.LEFT, padx=1)
        
        self.btn_grab = tk.Button(top_frame, text="✋", width=3, command=self.select_grab)
        self.btn_grab.pack(side=tk.LEFT, padx=1)

        tk.Frame(top_frame, width=10).pack(side=tk.LEFT) 
        tk.Button(top_frame, text="🎨 Palette", command=self.palette_manager.open_window, bg="#FFEB3B").pack(side=tk.LEFT, padx=2)

        tk.Button(top_frame, text=" Play", image=self.img_play, compound=tk.LEFT, 
                  command=self.open_animation_preview).pack(side=tk.LEFT, padx=10)
        
        # File Operations
        tk.Frame(top_frame, width=20).pack(side=tk.LEFT) 
        tk.Button(top_frame, text="📂 Load", bg="#2196F3", fg="white", 
                  command=self.project_manager.load_project_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="💾 Save", bg="#4CAF50", fg="white", 
                  command=self.project_manager.save_project).pack(side=tk.LEFT, padx=2)
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
                menu.add_command(label="Duplicate Frame", command=lambda: self.duplicate_tab(index))
                menu.add_command(label="Close Frame", command=lambda: self.close_tab_by_index(index))
                menu.add_separator()
                menu.add_command(label="Copy Code to Clipboard", 
                                 command=self.project_manager.export_active_tab)
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
        return new_tab

    def duplicate_tab(self, index):
        target_widget = self.root.nametowidget(self.notebook.tabs()[index])
        target_tab = getattr(target_widget, "tab_obj", None)
        if target_tab:
            new_tab = self.add_new_tab()
            new_tab.grid_data = [row[:] for row in target_tab.grid_data]
            new_tab.draw_grid_lines()
            self.show_toast(f"Duplicated {self.notebook.tab(index, 'text')}")

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
        if tab: tab.perform_undo()

    def trigger_redo(self):
        tab = self.active_tab()
        if tab: tab.perform_redo()

    # --- SELECTION & CLIPBOARD ---
    def copy_selection(self, event=None):
        tab = self.active_tab()
        if tab and tab.copy_to_clipboard():
            self.show_toast("Selection Copied!")

    def paste_selection(self, event=None):
        tab = self.active_tab()
        if tab and self.clipboard:
            self.select_selection_tool()
            tab.paste_from_clipboard(self.clipboard)
            self.show_toast("Pasted!")

    def nudge_selection(self, dr, dc):
        if self.active_tool == self.tool_instances["select"]:
            tab = self.active_tab()
            if tab:
                tab.move_selection_by_offset(dr, dc)
            return "break"

    # --- LIVE SYNC HELPER ---
    def notify_preview(self):
        if self.preview_window:
            self.preview_window.update_from_editor()

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

    def _reset_tools(self):
        self.btn_brush.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_eraser.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_bucket.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_grab.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_select.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_wand.config(relief=tk.RAISED, bg="#f0f0f0")
        self.btn_line.config(relief=tk.RAISED, bg="#f0f0f0")
        
        if self.active_tab():
            self.active_tab().commit_selection()

    def select_brush(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["brush"]
        self.active_color = self.brush_color
        self.btn_brush.config(relief=tk.SUNKEN, bg="#ddd")
        
    def select_eraser(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["eraser"]
        self.active_color = EMPTY_COLOR
        self.btn_eraser.config(relief=tk.SUNKEN, bg="#ddd")

    def select_grab(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["grab"]
        self.btn_grab.config(relief=tk.SUNKEN, bg="#ddd")
        
    def select_bucket(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["bucket"]
        self.active_color = self.brush_color
        self.btn_bucket.config(relief=tk.SUNKEN, bg="#ddd")
        
    def select_magic_wand(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["wand"]
        self.btn_wand.config(relief=tk.SUNKEN, bg="#ddd")
        
    def select_selection_tool(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["select"]
        self.btn_select.config(relief=tk.SUNKEN, bg="#ddd")
        if self.active_tab(): self.active_tab().draw_grid_lines()

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
                tab.save_state()
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
        # --- ISSUE 1 FIX: DO NOT RESET TOOL ---
        self.brush_color = c
        self.active_color = c
        # Update the button visual state only
        for idx, b in enumerate(self.palette_buttons): 
            b.config(relief=tk.SUNKEN if idx==i else tk.RAISED)

    def load_palettes_from_disk_internal(self):
        if os.path.exists(PALETTE_FILE):
            try: return json.load(open(PALETTE_FILE))
            except: return {}
        return {}
    
    def open_animation_preview(self):
        if self.preview_window and self.preview_window.win.winfo_exists():
            self.preview_window.win.lift()
            return
        self.preview_window = AnimationPreview(self)

    def select_line(self):
        self._reset_tools()
        self.active_tool = self.tool_instances["line"]
        self.active_color = self.brush_color
        self.btn_line.config(relief=tk.SUNKEN, bg="#ddd")

if __name__ == "__main__":
    print("Launching Window...")
    root = tk.Tk()
    app = PixelEditor(root)
    root.mainloop()