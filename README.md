# Gemini Pixel Editor - Project Documentation

## 1. Project Overview
**Gemini Pixel Editor** is a Python-based pixel art creation tool built with `tkinter`. It features a tabbed interface for animation frames, a custom tool system (Brush, Line, Bucket, etc.), layer-based selections (floating pixels), and an animation preview window.

The project is structured modularly:
* **`main.py`**: The entry point and UI orchestrator.
* **`editor_tab.py`**: Handles the actual drawing grid and interaction logic.
* **`tools/`**: Contains the logic for specific tools (Brush, Wand, etc.).
* **Managers**: Separate files handle Palettes, Projects (Save/Load), and History.

---

## 2. Status Tracking (User Editable)

### 🎯 Current Goals / To-Do
* [ ] Add "Onion Skinning" opacity control in settings.
* [ ] Implement a "Resize Canvas" feature (currently fixed at creation).
* [ ] Add a "Dark Mode" UI theme.

### 🐛 Known Bugs
* *No active bugs known as of v39.* (Previous issues with Tool Persistence, Selection Lag, and Grid Sizing have been fixed).

---

## 3. Codebase Reference

### Core Application

#### `main.py`
**Purpose:** Entry point. Sets up the main window, toolbar, and coordinates communication between subsystems.
* **`PixelEditor` (Class)**: The main application controller.
    * `__init__`: Calculates dynamic window size based on screen resolution and initializes all tool instances.
    * `setup_ui`: Builds the top toolbar (Buttons) and the Tab Notebook.
    * `setup_plus_tab`: Creates the dummy "+" tab for adding new frames.
    * `active_tab`: Returns the currently selected `EditorTab` object.
    * `notify_preview`: Signals the `AnimationPreview` window to update if it is open.
    * `select_[tool]`: Callback methods to switch the active tool (Brush, Eraser, etc.).
    * `set_brush_from_palette`: Updates the active color *without* resetting the active tool.

#### `editor_tab.py`
**Purpose:** Represents a single frame of animation (a tab). Handles the grid data and low-level canvas rendering.
* **`EditorTab` (Class)**:
    * `__init__`: Initializes the grid data structure (2D list) and canvas events.
    * `draw_grid_lines`: **Heavy operation.** Redraws the entire grid (static pixels + selection box).
    * `visual_move_selection`: **Optimized.** Uses `canvas.move` to instantly shift the selection without redrawing the grid.
    * `commit_selection`: Stamps the "floating" selection layer permanently onto the grid data.
    * `lift_selection_to_float`: Cuts pixels from the grid and moves them to the floating layer.
    * `save_state`: Pushes the current grid to the Undo stack.

#### `settings.py`
**Purpose:** Global constants.
* `DEFAULT_ROWS / COLS`: Fallback grid size (overridden by dynamic sizing in `main.py`).
* `EMPTY_COLOR`: Defines the background color (usually white or transparent representation).

#### `icons.py`
**Purpose:** Procedural generation of UI icons (eliminates need for external .png files).
* `create_icon(type_name)`: Returns a `tk.PhotoImage`. Contains pixel data for:
    * `brush`: Brown paintbrush icon.
    * `eraser`, `bucket`, `line`, `magic_wand`: Standard tool icons.
    * `gemini`, `play`: App-specific icons.

### Logic & Algorithms

#### `algorithms.py`
**Purpose:** Pure math functions for drawing and filling.
* `get_connected_pixels(grid, r, c)`: Performs a **Breadth-First Search (BFS)** to find all contiguous pixels of the same color (used by Bucket and Magic Wand).
* `get_line_pixels(start, end)`: Implements **Bresenham’s Line Algorithm** to calculate integer coordinates for a straight line.

#### `history.py`
**Purpose:** Manages Undo/Redo stacks.
* **`HistoryManager` (Class)**:
    * `push_state`: Saves a deep copy of the grid.
    * `undo`: Returns the previous state and moves current to "redo".
    * `redo`: Returns the next state from the "redo" stack.

#### `project_manager.py`
**Purpose:** Handles File I/O.
* **`ProjectManager` (Class)**:
    * `save_project`: Saves the project as a folder containing JSON metadata and `.txt` files for each frame.
    * `load_project_folder`: Reads the folder structure and reconstructs the tabs.
    * `export_for_gemini`: Converts the grid into a text-based ASCII/Symbol map for AI analysis.

#### `palette_manager.py`
**Purpose:** Handles the "Palette" popup window.
* **`PaletteManager` (Class)**:
    * `refresh_manager_slots`: Dynamically creates buttons for the current palette colors.
    * `resize_palette`: Adds/Removes slots from the palette list.
    * `save/load_palette_to_disk`: Persists palette presets to `my_palettes.json`.

#### `animation_preview.py`
**Purpose:** The popup window that plays the animation.
* **`AnimationPreview` (Class)**:
    * `create_grid_objects`: Creates the canvas rectangles *once* (cached) for performance.
    * `draw_scene`: Updates the colors of the cached rectangles based on the current frame data.
    * `animate`: The loop that advances the frame index and calls `draw_scene`.

### Tool System (`tools/` folder)

#### `base.py`
* **`Tool`**: Abstract parent class defining `on_click`, `on_drag`, and `on_release` interfaces.

#### `brush.py`
* **`BrushTool`**: Sets individual pixels to the active color. Saves state on click.

#### `eraser.py`
* **`EraserTool`**: Sets pixels to `EMPTY_COLOR`.

#### `line.py`
* **`LineTool`**:
    * Uses a "snapshot" system to draw a preview line while dragging.
    * Commits the final line calculation (Bresenham) on release.

#### `bucket.py`
* **`BucketTool`**: Triggers `get_connected_pixels` (BFS) and fills them with the active color.

#### `select.py`
* **`SelectTool`**:
    * **Mode "box"**: Draws a selection rectangle.
    * **Mode "move"**: Drags the floating layer using `visual_move_selection` (Optimized).

#### `wand.py`
* **`MagicWandTool`**:
    * Selects pixels by color using BFS.
    * Immediately lifts them to the floating layer.
    * Supports dragging immediately after selection.

#### `grab.py`
* **`GrabTool`**: Uses `canvas.scan_dragto` to pan the view (if zoomed/scrolled).

---

## 4. Testing
Run `python test_logic.py` to verify:
1.  Grid coordinate math.
2.  Palette resizing logic.
3.  Gemini export formatting.
4.  Selection boundary normalization.
5.  BFS and Line algorithm integrity.
6.  Undo/Redo history integrity.