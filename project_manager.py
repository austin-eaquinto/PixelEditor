# project_manager.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import os
import re
from settings import *

# NEW IMPORT
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class ProjectManager:
    """Handles all File I/O: Saving, Loading, Exporting, and Importing."""
    
    def __init__(self, app_ref):
        self.app = app_ref 

    # --- SAVE / LOAD (Existing Logic Preserved) ---
    def save_project(self):
        if not self.app.current_project_path: self.save_project_as()
        else: self._perform_save(self.app.current_project_path)

    def save_project_as(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Project Folder", initialfile="project_data.json",
            filetypes=[("Project Data", "project_data.json"), ("All Files", "*.*")],
            defaultextension=".json"
        )
        if not file_path: return
        folder_path = os.path.dirname(file_path) if os.path.basename(file_path) == "project_data.json" else os.path.splitext(file_path)[0]
        self.app.current_project_path = folder_path
        self._perform_save(folder_path)

    def _perform_save(self, folder_path):
        meta_data = {
            "rows": self.app.rows, "cols": self.app.cols, 
            "pixel_size": self.app.pixel_size, "palette": self.app.current_palette
        }
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(os.path.join(folder_path, "project_data.json"), "w") as f: json.dump(meta_data, f, indent=4)
            
            # Clean old frames
            if os.path.exists(folder_path):
                for f in os.listdir(folder_path):
                    if f.startswith("frame_") and f.endswith(".txt"): os.remove(os.path.join(folder_path, f))

            # Save Tabs
            tabs = self.app.notebook.tabs()
            for i in range(len(tabs) - 1): 
                tab_widget = self.app.root.nametowidget(tabs[i])
                tab = getattr(tab_widget, "tab_obj", None)
                if tab:
                    with open(os.path.join(folder_path, f"frame_{i+1}.txt"), "w") as f: 
                        f.write(self.generate_tab_content(tab))
            
            self.app.root.title(f"Gemini Pixel Editor - [{os.path.basename(folder_path)}]")
            self.app.show_toast(f"Saved to '{os.path.basename(folder_path)}'")
        except Exception as e: messagebox.showerror("Save Error", str(e))

    def load_project_folder(self):
        file_path = filedialog.askopenfilename(title="Open Project", filetypes=[("Project Files", "*.json *.txt"), ("All Files", "*.*")])
        if not file_path: return
        folder_path = os.path.dirname(file_path)
        try:
            meta_path = os.path.join(folder_path, "project_data.json")
            if not os.path.exists(meta_path): return
            with open(meta_path, "r") as f: meta = json.load(f)
            
            self.app.rows = meta.get("rows", 33)
            self.app.cols = meta.get("cols", 45)
            self.app.pixel_size = meta.get("pixel_size", 15)
            self.app.current_palette = meta.get("palette", self.app.current_palette)
            self.app.refresh_quick_palette()
            
            for tab in self.app.notebook.tabs(): self.app.notebook.forget(tab)
            
            files = [f for f in os.listdir(folder_path) if f.startswith("frame_") and f.endswith(".txt")]
            files.sort(key=lambda x: int(re.search(r'\d+', x).group()))
            
            if not files: self.app.add_new_tab("Frame 1") 
            else:
                for i, filename in enumerate(files): self.load_frame_file(os.path.join(folder_path, filename), f"Frame {i+1}")
            
            self.app.setup_plus_tab() 
            self.app.current_project_path = folder_path
            self.app.show_toast("Project Loaded!")
        except Exception as e: messagebox.showerror("Load Error", str(e))

    def load_frame_file(self, filepath, title):
        new_tab = self.app.add_new_tab(title)
        with open(filepath, "r") as f: content = f.read()
        grid_match = re.search(r'my_pixel_art\s*=\s*"""(.*?)"""', content, re.DOTALL)
        if not grid_match: return 
        
        pal_match = re.search(r"palette\s*=\s*\{(.*?)\}", content, re.DOTALL)
        file_map = {}
        if pal_match:
            for sym, hex_val in re.findall(r"'(\S)':\s*'([^']*)'", pal_match.group(1)):
                if hex_val == 'Transparent': hex_val = EMPTY_COLOR
                file_map[sym] = hex_val
                
        raw_grid = grid_match.group(1).strip().split('\n')
        for r, line in enumerate(raw_grid):
            if r < self.app.rows:
                for c, char in enumerate(line):
                    if c < self.app.cols and char in file_map: new_tab.grid_data[r][c] = file_map[char]
        new_tab.draw_grid_lines()

    # --- TEXT EXPORT (Gemini) ---
    def generate_tab_content(self, tab):
        unique_colors = set(cell for row in tab.grid_data for cell in row if cell != EMPTY_COLOR)
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%&*"
        color_map = {EMPTY_COLOR: '.'}
        legend_str = "palette = {\n    '.': 'Transparent',\n"
        for i, color in enumerate(sorted(unique_colors)):
            sym = symbols[i] if i < len(symbols) else "?"
            color_map[color] = sym
            legend_str += f"    '{sym}': '{color}',\n"
        legend_str += "}"
        
        ascii_art = 'my_pixel_art = """\n' + "\n".join("".join(color_map[cell] for cell in row) for row in tab.grid_data) + '\n"""'
        return f"{legend_str}\n\n{ascii_art}"

    def export_active_tab(self):
        tab = self.app.active_tab()
        if tab:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(self.generate_tab_content(tab))
            self.app.show_toast("Code Copied!")

    def export_for_gemini(self):
        path = filedialog.asksaveasfilename(title="Export Text", initialfile="gemini_context.txt", filetypes=[("Text File", "*.txt")])
        if not path: return
        
        # Simple symbol map for all frames
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@%&*"
        symbol_map = {c: symbols[i] for i, c in enumerate(self.app.current_palette) if i < len(symbols)}
        legend = ["### PALETTE ###", ".: Transparent"] + [f"{v}: {k}" for k,v in symbol_map.items()]
        
        content = ["\n".join(legend), "="*20]
        tabs = self.app.notebook.tabs()
        for i in range(len(tabs) - 1):
            tab = getattr(self.app.root.nametowidget(tabs[i]), "tab_obj", None)
            if tab:
                content.append(f"FRAME {i+1}")
                content.append("\n".join("".join("." if c == EMPTY_COLOR else symbol_map.get(c, "?") for c in row) for row in tab.grid_data))
                content.append("-" * 20)
        
        with open(path, "w") as f: f.write("\n".join(content))
        self.app.show_toast("Exported Text!")

    # --- NEW: IMAGE IO (Pillow) ---
    
    def export_as_png(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow library not installed.\nRun: pip install Pillow")
            return
        
        tab = self.app.active_tab()
        if not tab: return

        path = filedialog.asksaveasfilename(title="Export PNG", defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not path: return
        
        # Use simple integer scaling
        scale = simpledialog.askinteger("Export", "Scale (e.g. 1, 4, 10):", initialvalue=10, minvalue=1, maxvalue=50)
        if not scale: return

        try:
            img = self._grid_to_image(tab.get_flattened_data(), scale)
            img.save(path)
            self.app.show_toast(f"Saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_sprite_sheet(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow library not installed.\nRun: pip install Pillow")
            return

        path = filedialog.asksaveasfilename(title="Export Sprite Sheet", defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not path: return

        scale = simpledialog.askinteger("Export", "Scale (e.g. 1, 4, 10):", initialvalue=1, minvalue=1, maxvalue=50)
        if not scale: return

        try:
            # 1. Collect all frames
            frames = []
            tabs = self.app.notebook.tabs()
            for i in range(len(tabs) - 1):
                tab_widget = self.app.root.nametowidget(tabs[i])
                tab = getattr(tab_widget, "tab_obj", None)
                if tab:
                    frames.append(self._grid_to_image(tab.get_flattened_data(), scale))
            
            if not frames: return

            # 2. Stitch them horizontally
            w, h = frames[0].size
            sheet = Image.new("RGBA", (w * len(frames), h))
            
            for i, frame in enumerate(frames):
                sheet.paste(frame, (i * w, 0))

            sheet.save(path)
            self.app.show_toast(f"Saved Sheet: {len(frames)} frames")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_image_to_selection(self):
        """Loads an image and converts it into a floating selection."""
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow library not installed.\nRun: pip install Pillow")
            return
            
        tab = self.app.active_tab()
        if not tab: return

        path = filedialog.askopenfilename(title="Import Image", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if not path: return

        try:
            # 1. Load and Resize
            original = Image.open(path).convert("RGBA")
            
            # Simple prompt: Fit to Width?
            resize_mode = messagebox.askyesno("Resize", "Resize image to fit canvas width?")
            
            target_w, target_h = original.size
            if resize_mode:
                ratio = original.height / original.width
                target_w = self.app.cols
                target_h = int(target_w * ratio)
                original = original.resize((target_w, target_h), Image.NEAREST)

            # 2. Convert to Grid Data (Dictionary format for selection)
            pixels = original.load()
            new_floating = {}
            
            # Clamp to reasonable size to prevent massive lags
            scan_w = min(target_w, self.app.cols)
            scan_h = min(target_h, self.app.rows)

            for r in range(scan_h):
                for c in range(scan_w):
                    r_g_b_a = pixels[c, r]
                    if r_g_b_a[3] > 0: # If not transparent
                        # Convert (255, 0, 0) to "#FF0000"
                        hex_color = '#{:02x}{:02x}{:02x}'.format(*r_g_b_a[:3]).upper()
                        new_floating[(r, c)] = hex_color

            if not new_floating:
                messagebox.showinfo("Info", "Image was empty or fully transparent.")
                return

            # 3. Apply to Tab as Floating Selection
            tab.commit_selection() # Commit anything existing
            tab.save_state()
            
            tab.floating_pixels = new_floating
            tab.floating_offset = (0, 0) # Place at top-left
            
            # Update Selection Bounds
            max_r = max(k[0] for k in new_floating.keys())
            max_c = max(k[1] for k in new_floating.keys())
            tab.sel_start = (0, 0)
            tab.sel_end = (max_r, max_c)
            
            tab.draw_grid_lines()
            self.app.show_toast("Image Imported!")
            
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _grid_to_image(self, grid_data, scale):
        """Helper to convert grid matrix to PIL Image."""
        cols = len(grid_data[0])
        rows = len(grid_data)
        img = Image.new("RGBA", (cols, rows), (0, 0, 0, 0))
        pixels = img.load()
        
        for r in range(rows):
            for c in range(cols):
                color = grid_data[r][c]
                if color != EMPTY_COLOR:
                    # Convert Hex to RGB
                    color = color.lstrip('#')
                    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                    pixels[c, r] = rgb + (255,) # Add Alpha 255
                    
        if scale > 1:
            return img.resize((cols * scale, rows * scale), Image.NEAREST)
        return img