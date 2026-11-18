#!/usr/bin/env python3
"""CMD Theme Pack - Manage and apply CMD color themes (Python Edition)

A command-line utility for managing and applying color schemes to Windows Command Prompt.
Uses only Python standard library (winreg, json, argparse, ctypes).
"""

__version__ = "0.2.0"

import winreg
import json
import argparse
import os
import sys
import ctypes
import random
import time
import colorsys
from pathlib import Path
from ctypes import wintypes

# Check if GUI modules are available
try:
    import tkinter as tk
    from tkinter import ttk, colorchooser
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Check if msvcrt is available (Windows only)
try:
    import msvcrt
    MSVCRT_AVAILABLE = True
except ImportError:
    MSVCRT_AVAILABLE = False


def hide_console_window():
    """Hide the console window (for GUI mode)."""
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except:
        pass


class ThemeGUI:
    """GUI for theme management."""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            print("ERROR: GUI not available (tkinter not found)", file=sys.stderr)
            sys.exit(1)
        
        self.root = tk.Tk()
        self.root.title(f"CMD Theme Pack - v{__version__}")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Dark theme colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.widget_bg = "#2d2d2d"
        self.button_bg = "#3e3e3e"
        
        self.root.configure(bg=self.bg_color)
        
        # Load theme data
        self.loader = ThemeLoader()
        self.themes = sorted(self.loader.list_themes(), key=lambda t: t.name)
        
        # State variables
        self.selected_theme = tk.StringVar(value=self.themes[0].name if self.themes else "")
        self.opacity_var = tk.IntVar(value=70)
        self.tint_color = None  # None = no tint
        self.tint_strength_var = tk.IntVar(value=60)
        self.use_acrylic_var = tk.BooleanVar(value=False)
        self.window_alpha_var = tk.IntVar(value=100)
        self.autoblur_var = tk.BooleanVar(value=False)
        self.clip_edges_var = tk.BooleanVar(value=False)
        
        self.blur_handler = BlurHandler()
        
        # Create UI
        self.create_widgets()
        
        # Apply initial preview
        self.root.after(100, self.update_preview)
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Theme selection
        theme_label = tk.Label(main_frame, text="Theme:", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 10, "bold"))
        theme_label.pack(anchor="w", pady=(0, 5))
        
        theme_frame = tk.Frame(main_frame, bg=self.bg_color)
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.theme_combo = ttk.Combobox(theme_frame, textvariable=self.selected_theme, 
                                        values=[t.name for t in self.themes], state="readonly", width=40)
        self.theme_combo.pack(side=tk.LEFT)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.on_theme_changed())
        
        # Color swatch
        self.swatch_canvas = tk.Canvas(main_frame, height=30, bg=self.widget_bg, highlightthickness=0)
        self.swatch_canvas.pack(fill=tk.X, pady=(0, 15))
        
        # Opacity slider
        self.create_slider(main_frame, "Opacity:", self.opacity_var, 30, 100, self.on_setting_changed)
        
        # Tint section
        tint_label = tk.Label(main_frame, text="Tint Color:", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 10, "bold"))
        tint_label.pack(anchor="w", pady=(10, 5))
        
        tint_buttons_frame = tk.Frame(main_frame, bg=self.bg_color)
        tint_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(tint_buttons_frame, text="Pick Color", command=self.pick_tint_color, 
                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT, padx=10, pady=5).pack(side=tk.LEFT, padx=(0, 5))
        
        for color_name, color_hex in [("Red", "#FF0000"), ("Blue", "#0000FF"), ("Green", "#00FF00"), 
                                       ("Purple", "#800080"), ("Pink", "#FFC0CB"), ("None", None)]:
            btn = tk.Button(tint_buttons_frame, text=color_name, 
                           command=lambda c=color_hex: self.set_tint_color(c),
                           bg=color_hex if color_hex else self.button_bg, 
                           fg="white" if color_hex else self.fg_color,
                           relief=tk.FLAT, padx=10, pady=5)
            btn.pack(side=tk.LEFT, padx=2)
        
        # Tint strength slider
        self.create_slider(main_frame, "Tint Strength:", self.tint_strength_var, 0, 100, self.on_setting_changed)
        
        # Mode toggle
        mode_frame = tk.Frame(main_frame, bg=self.bg_color)
        mode_frame.pack(fill=tk.X, pady=(10, 10))
        
        tk.Label(mode_frame, text="Mode:", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        tk.Radiobutton(mode_frame, text="Blur (no drag lag)", variable=self.use_acrylic_var, value=False,
                      command=self.on_setting_changed, bg=self.bg_color, fg=self.fg_color, 
                      selectcolor=self.widget_bg).pack(side=tk.LEFT, padx=(10, 5))
        
        tk.Radiobutton(mode_frame, text="Acrylic (lags on drag)", variable=self.use_acrylic_var, value=True,
                      command=self.on_setting_changed, bg=self.bg_color, fg=self.fg_color,
                      selectcolor=self.widget_bg).pack(side=tk.LEFT)
        
        # Window alpha slider
        self.create_slider(main_frame, "Window Alpha (CMD opacity):", self.window_alpha_var, 60, 100, self.on_setting_changed)
        
        # Autoblur checkbox
        tk.Checkbutton(main_frame, text="Apply to every new CMD window (autoblur)", 
                      variable=self.autoblur_var, bg=self.bg_color, fg=self.fg_color,
                      selectcolor=self.widget_bg).pack(anchor="w", pady=(10, 5))
        
        # Clip edges checkbox
        tk.Checkbutton(main_frame, text="Clip edges (prevent tint bleed)", 
                      variable=self.clip_edges_var, command=self.on_clip_edges_changed,
                      bg=self.bg_color, fg=self.fg_color,
                      selectcolor=self.widget_bg).pack(anchor="w", pady=(0, 15))
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(button_frame, text="Apply", command=self.apply_theme, 
                 bg="#007acc", fg="white", relief=tk.FLAT, padx=20, pady=8, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Restore", command=self.restore_backup,
                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Undo", command=self.undo_theme,
                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Random", command=self.random_theme,
                 bg=self.button_bg, fg=self.fg_color, relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", pady=(10, 0))
    
    def create_slider(self, parent, label_text, variable, from_, to, command):
        """Helper to create labeled slider."""
        frame = tk.Frame(parent, bg=self.bg_color)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        label = tk.Label(frame, text=label_text, bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 10, "bold"))
        label.pack(side=tk.LEFT)
        
        value_label = tk.Label(frame, textvariable=variable, bg=self.bg_color, fg=self.fg_color, width=4)
        value_label.pack(side=tk.RIGHT)
        
        slider = tk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL, variable=variable,
                         command=lambda v: command(), bg=self.widget_bg, fg=self.fg_color,
                         highlightthickness=0, troughcolor=self.button_bg, showvalue=False)
        slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 10))
    
    def on_theme_changed(self):
        """Handle theme selection change."""
        self.draw_color_swatch()
        self.update_preview()
    
    def on_setting_changed(self):
        """Handle any setting change."""
        self.update_preview()
    
    def on_clip_edges_changed(self):
        """Handle edge clipping toggle."""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if self.clip_edges_var.get():
            self.blur_handler.clip_window_edges(hwnd)
        else:
            self.blur_handler.remove_window_clip(hwnd)
    
    def draw_color_swatch(self):
        """Draw color swatch for selected theme."""
        theme = self.loader.get_theme(self.selected_theme.get())
        if not theme:
            return
        
        self.swatch_canvas.delete("all")
        
        colors = [
            theme.colors['background'], theme.colors['foreground'],
            theme.colors['black'], theme.colors['red'], theme.colors['green'], theme.colors['yellow'],
            theme.colors['blue'], theme.colors['magenta'], theme.colors['cyan'], theme.colors['white'],
            theme.colors['bright_black'], theme.colors['bright_red'], theme.colors['bright_green'], theme.colors['bright_yellow'],
            theme.colors['bright_blue'], theme.colors['bright_magenta'], theme.colors['bright_cyan'], theme.colors['bright_white']
        ]
        
        canvas_width = self.swatch_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 560  # Default width
        
        box_width = canvas_width / len(colors)
        
        for i, color in enumerate(colors):
            x0 = i * box_width
            x1 = (i + 1) * box_width
            self.swatch_canvas.create_rectangle(x0, 0, x1, 30, fill=color, outline="")
    
    def update_preview(self):
        """Update live glass preview on GUI window."""
        try:
            theme = self.loader.get_theme(self.selected_theme.get())
            if not theme:
                return
            
            # Determine tint color
            if self.tint_color:
                tint = self.tint_color
            else:
                tint = theme.colors['background']
            
            opacity = self.tint_strength_var.get()
            use_acrylic = self.use_acrylic_var.get()
            
            # Get GUI window handle
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            # Apply blur to GUI window
            self.blur_handler.apply_blur_to_window(hwnd, tint, opacity, use_acrylic)
            
        except Exception as e:
            pass  # Silently fail preview
    
    def pick_tint_color(self):
        """Open color picker for tint."""
        color = colorchooser.askcolor(title="Pick Tint Color")
        if color and color[1]:
            self.set_tint_color(color[1])
    
    def set_tint_color(self, color_hex):
        """Set tint color."""
        self.tint_color = color_hex
        self.update_preview()
    
    def apply_theme(self):
        """Apply the selected theme with current settings."""
        try:
            theme = self.loader.get_theme(self.selected_theme.get())
            if not theme:
                self.status_label.config(text="ERROR: Theme not found", fg="#ff0000")
                return
            
            opacity = self.opacity_var.get()
            use_acrylic = self.use_acrylic_var.get()
            window_alpha_percent = self.window_alpha_var.get()
            autoblur = self.autoblur_var.get()
            
            # Create backup
            backup_manager = BackupManager()
            if not backup_manager.backup_exists():
                backup_manager.create_backup()
            
            # Apply theme to registry
            handler = RegistryHandler()
            
            # Convert window alpha percentage to registry value
            window_alpha_registry = max(60, opacity) if self.tint_color else window_alpha_percent
            handler.apply_theme(theme, opacity=window_alpha_registry)
            
            # Apply blur if tint is set
            blur_applied = False
            if self.tint_color or opacity < 100:
                try:
                    blur_tint = self.tint_color if self.tint_color else theme.colors['background']
                    blur_opacity = self.tint_strength_var.get()
                    
                    # Save settings for autoblur
                    backup_manager.save_blur_settings(
                        tint=self.tint_color,
                        opacity=blur_opacity,
                        theme_background=theme.colors['background'],
                        use_acrylic=use_acrylic
                    )
                    
                    # Apply to current console window
                    kernel32 = ctypes.windll.kernel32
                    console_hwnd = kernel32.GetConsoleWindow()
                    if console_hwnd:
                        self.blur_handler.apply_blur_to_window(console_hwnd, blur_tint, blur_opacity, use_acrylic)
                    
                    blur_applied = True
                except Exception as e:
                    self.status_label.config(text=f"Blur failed: {e}", fg="#ffaa00")
            
            # Handle autoblur
            if autoblur and (self.tint_color or blur_applied):
                handler.enable_autoblur()
            elif not autoblur:
                handler.disable_autoblur()
                backup_manager.clear_blur_settings()
            
            # Save to history
            backup_manager.save_state_before_apply(theme.name, opacity, blur_applied, self.tint_color)
            
            self.status_label.config(text=f"✓ Applied: {theme.name}", fg="#00ff00")
            
        except Exception as e:
            self.status_label.config(text=f"ERROR: {e}", fg="#ff0000")
    
    def restore_backup(self):
        """Restore from backup."""
        try:
            backup_manager = BackupManager()
            if not backup_manager.backup_exists():
                self.status_label.config(text="No backup found", fg="#ffaa00")
                return
            
            backup_manager.restore_backup()
            backup_manager.clear_blur_settings()
            
            handler = RegistryHandler()
            handler.disable_autoblur()
            
            self.status_label.config(text="✓ Restored from backup", fg="#00ff00")
        except Exception as e:
            self.status_label.config(text=f"ERROR: {e}", fg="#ff0000")
    
    def undo_theme(self):
        """Undo to previous theme."""
        try:
            backup_manager = BackupManager()
            state = backup_manager.get_state_to_restore()
            
            if not state:
                self.status_label.config(text="Nothing to undo", fg="#ffaa00")
                return
            
            theme_name = state.get('theme')
            if theme_name:
                # Update GUI to show the theme
                self.selected_theme.set(theme_name)
                self.on_theme_changed()
                
                # Apply it
                self.apply_theme()
                
                self.status_label.config(text=f"✓ Undone to: {theme_name}", fg="#00ff00")
            
        except Exception as e:
            self.status_label.config(text=f"ERROR: {e}", fg="#ff0000")
    
    def random_theme(self):
        """Select a random theme."""
        if self.themes:
            theme = random.choice(self.themes)
            self.selected_theme.set(theme.name)
            self.on_theme_changed()
    
    def run(self):
        """Run the GUI main loop."""
        self.root.mainloop()


def cmd_gui(args):
    """Handle gui command."""
    hide_console_window()
    gui = ThemeGUI()
    gui.run()


def cmd_tune(args):
    """Handle tune command - interactive live tuning."""
    if not MSVCRT_AVAILABLE:
        print("ERROR: tune command not available (msvcrt not found)", file=sys.stderr)
        sys.exit(1)
    
    print("CMD Theme Pack - Live Tune Mode")
    print("=" * 50)
    print()
    print("Controls:")
    print("  Left/Right : Opacity -/+5")
    print("  Up/Down    : Rotate tint hue")
    print("  W          : White tint")
    print("  B          : Black tint")
    print("  [/]        : Tint strength -/+5")
    print("  M          : Toggle blur/acrylic")
    print("  A/D        : Window alpha -/+5 (min 60)")
    print("  E          : Toggle edge clipping")
    print("  S          : Save (enable autoblur)")
    print("  R          : Reset to solid")
    print("  Q          : Quit and restore")
    print()
    print("Press any key to start...")
    msvcrt.getch()
    
    # Store original state
    handler = RegistryHandler()
    original_opacity = handler.get_opacity() or 100
    
    # Initialize state
    loader = ThemeLoader()
    themes = loader.list_themes()
    if not themes:
        print("ERROR: No themes available", file=sys.stderr)
        sys.exit(1)
    
    current_theme = themes[0]
    opacity = 70
    tint_hue = 0.0  # 0.0 to 1.0
    tint_saturation = 1.0
    tint_value = 1.0
    tint_strength = 60
    use_acrylic = False
    window_alpha = 100
    clip_edges = False
    
    # Get console window handle
    kernel32 = ctypes.windll.kernel32
    console_hwnd = kernel32.GetConsoleWindow()
    
    if not console_hwnd:
        print("ERROR: Could not get console window handle", file=sys.stderr)
        sys.exit(1)
    
    blur_handler = BlurHandler()
    
    def get_tint_hex():
        """Convert HSV to hex color."""
        r, g, b = colorsys.hsv_to_rgb(tint_hue, tint_saturation, tint_value)
        return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
    
    def apply_current_settings():
        """Apply current settings to console."""
        try:
            tint_hex = get_tint_hex()
            blur_handler.apply_blur_to_window(console_hwnd, tint_hex, tint_strength, use_acrylic)
            
            # Also set window alpha
            handler.set_opacity(window_alpha)
        except Exception as e:
            pass  # Silently fail during tuning
    
    def display_state():
        """Display current state."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("CMD Theme Pack - Live Tune Mode")
        print("=" * 50)
        print()
        print(f"Theme: {current_theme.name}")
        print(f"Tint: {get_tint_hex()}")
        print(f"Tint Strength: {tint_strength}%")
        print(f"Opacity: {opacity}%")
        print(f"Window Alpha: {window_alpha}%")
        print(f"Mode: {'Acrylic' if use_acrylic else 'Blur'}")
        print(f"Edge Clipping: {'ON' if clip_edges else 'OFF'}")
        print()
        print("Controls: Left/Right=opacity, Up/Down=hue, [/]=strength")
        print("          W=white, B=black, M=mode, A/D=alpha, E=clip, S=save, R=reset, Q=quit")
    
    # Initial display and apply
    display_state()
    apply_current_settings()
    
    # Main loop
    running = True
    while running:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            # Handle arrow keys and special keys
            if key == b'\xe0' or key == b'\x00':  # Arrow key prefix
                key = msvcrt.getch()
                if key == b'K':  # Left arrow
                    opacity = max(30, opacity - 5)
                elif key == b'M':  # Right arrow
                    opacity = min(100, opacity + 5)
                elif key == b'H':  # Up arrow
                    tint_hue = (tint_hue + 0.05) % 1.0
                elif key == b'P':  # Down arrow
                    tint_hue = (tint_hue - 0.05) % 1.0
            elif key == b'[':
                tint_strength = max(0, tint_strength - 5)
            elif key == b']':
                tint_strength = min(100, tint_strength + 5)
            elif key.lower() == b'w':
                tint_hue, tint_saturation, tint_value = 0.0, 0.0, 1.0
            elif key.lower() == b'b':
                tint_hue, tint_saturation, tint_value = 0.0, 0.0, 0.0
            elif key.lower() == b'm':
                use_acrylic = not use_acrylic
            elif key.lower() == b'a':
                window_alpha = max(60, window_alpha - 5)
            elif key.lower() == b'd':
                window_alpha = min(100, window_alpha + 5)
            elif key.lower() == b'e':
                clip_edges = not clip_edges
                if clip_edges:
                    blur_handler.clip_window_edges(console_hwnd)
                else:
                    blur_handler.remove_window_clip(console_hwnd)
            elif key.lower() == b's':
                # Save settings
                backup_manager = BackupManager()
                tint_hex = get_tint_hex()
                backup_manager.save_blur_settings(
                    tint=tint_hex,
                    opacity=tint_strength,
                    theme_background=current_theme.colors['background'],
                    use_acrylic=use_acrylic
                )
                handler.enable_autoblur()
                handler.set_opacity(window_alpha)
                display_state()
                print("\n✓ Settings saved! Autoblur enabled.")
                time.sleep(1)
            elif key.lower() == b'r':
                # Reset to solid
                opacity = 100
                tint_strength = 0
                window_alpha = 100
                handler.set_opacity(100)
                # Don't apply blur when reset
                display_state()
                print("\n✓ Reset to solid")
                time.sleep(1)
            elif key.lower() == b'q':
                # Quit and restore
                handler.set_opacity(original_opacity)
                running = False
                print("\n✓ Restored original settings")
                break
            else:
                continue
            
            display_state()
            apply_current_settings()
    
    print("\nExited tune mode.")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class Theme:
    """Represents a theme with metadata and color scheme."""
    
    def __init__(self, data):
        self.schema_version = data.get('schema_version', '1.0')
        self.name = data['name']
        self.description = data['description']
        self.author = data['author']
        self.palette_type = data['palette_type']
        self.colors = data['colors']
    
    def validate(self):
        """Validate theme has all required fields and valid colors."""
        if self.schema_version != '1.0':
            raise ValueError(f"Invalid schema version: {self.schema_version}")
        
        if not self.name.strip():
            raise ValueError("Theme name cannot be empty")
        
        if not self.description.strip():
            raise ValueError("Theme description cannot be empty")
        
        if not self.author.strip():
            raise ValueError("Theme author cannot be empty")
        
        # Validate all color fields
        color_fields = [
            'background', 'foreground',
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
        ]
        
        for field in color_fields:
            if field not in self.colors:
                raise ValueError(f"Missing color field: {field}")
            self._validate_hex_color(self.colors[field], field)
    
    def _validate_hex_color(self, color, field_name):
        """Validate that a string is a valid hex color (#RRGGBB)."""
        if not color.startswith('#'):
            raise ValueError(f"{field_name}: Color must start with '#', got: {color}")
        
        if len(color) != 7:
            raise ValueError(f"{field_name}: Color must be 7 characters (#RRGGBB), got: {color}")
        
        try:
            int(color[1:], 16)
        except ValueError:
            raise ValueError(f"{field_name}: Invalid hex characters in: {color}")


class ThemeLoader:
    """Loads themes from embedded JSON and external directories."""
    
    def __init__(self):
        self.themes = {}
        self._load_embedded_themes()
    
    def _load_embedded_themes(self):
        """Load themes from the themes directory next to this script."""
        # Use resource_path to support both dev and PyInstaller exe
        themes_dir = Path(resource_path('src/themes'))
        
        if themes_dir.exists():
            for theme_file in themes_dir.glob('*.json'):
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        theme = Theme(data)
                        theme.validate()
                        self.themes[theme.name] = theme
                except Exception as e:
                    print(f"Warning: Failed to load {theme_file.name}: {e}", file=sys.stderr)
    
    def get_theme(self, name):
        """Get a theme by name."""
        return self.themes.get(name)
    
    def list_themes(self):
        """List all available themes."""
        return list(self.themes.values())


class WindowsTerminalHandler:
    """Handles Windows Terminal settings.json modifications."""
    
    def __init__(self):
        self.settings_path = self._find_settings_path()
    
    def _find_settings_path(self):
        """Find Windows Terminal settings.json path."""
        local_appdata = Path(os.environ.get('LOCALAPPDATA', ''))
        wt_path = local_appdata / 'Packages' / 'Microsoft.WindowsTerminal_8wekyb3d8bbwe' / 'LocalState' / 'settings.json'
        
        if wt_path.exists():
            return wt_path
        return None
    
    def is_available(self):
        """Check if Windows Terminal is available."""
        return self.settings_path is not None
    
    def apply_opacity_blur(self, opacity=None, blur=False):
        """Apply opacity and blur to Windows Terminal."""
        if not self.is_available():
            return False
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Ensure profiles.defaults exists
            if 'profiles' not in settings:
                settings['profiles'] = {}
            if 'defaults' not in settings['profiles']:
                settings['profiles']['defaults'] = {}
            
            # Apply opacity
            if opacity is not None:
                settings['profiles']['defaults']['opacity'] = opacity
            
            # Apply blur
            if blur:
                settings['profiles']['defaults']['useAcrylic'] = True
            
            # Write back
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to modify Windows Terminal settings: {e}")
    
    def get_current_settings(self):
        """Get current opacity and blur settings."""
        if not self.is_available():
            return None
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            defaults = settings.get('profiles', {}).get('defaults', {})
            return {
                'opacity': defaults.get('opacity'),
                'useAcrylic': defaults.get('useAcrylic', False)
            }
        except:
            return None


class RegistryHandler:
    """Handles reading and modifying Windows Console registry settings."""
    
    CONSOLE_KEY_PATH = r"Console"
    AUTORUN_KEY_PATH = r"Software\Microsoft\Command Processor"
    
    def __init__(self):
        pass
    
    def apply_theme(self, theme, opacity=None):
        """Apply a theme to the legacy console by modifying registry."""
        try:
            # Open HKEY_CURRENT_USER\Console with write permissions
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.CONSOLE_KEY_PATH,
                0,
                winreg.KEY_WRITE
            )
            
            try:
                # Write all 16 ColorTable entries
                self._write_color_table(key, theme.colors)
                
                # Write ScreenColors value (background in high nibble, foreground in low nibble)
                # Use black background (index 0) and white foreground (index 7)
                screen_colors = (0 << 4) | 7  # 0x07
                winreg.SetValueEx(key, "ScreenColors", 0, winreg.REG_DWORD, screen_colors)
                
                # Apply opacity if specified
                if opacity is not None:
                    window_alpha = self._opacity_to_window_alpha(opacity)
                    winreg.SetValueEx(key, "WindowAlpha", 0, winreg.REG_DWORD, window_alpha)
                
            finally:
                winreg.CloseKey(key)
            
        except PermissionError:
            raise PermissionError("Insufficient permissions. Try running as administrator.")
        except Exception as e:
            raise Exception(f"Failed to write registry: {e}")
    
    def _write_color_table(self, key, colors):
        """Write color table to registry."""
        color_mapping = [
            ("ColorTable00", colors['black']),
            ("ColorTable01", colors['blue']),
            ("ColorTable02", colors['green']),
            ("ColorTable03", colors['cyan']),
            ("ColorTable04", colors['red']),
            ("ColorTable05", colors['magenta']),
            ("ColorTable06", colors['yellow']),
            ("ColorTable07", colors['white']),
            ("ColorTable08", colors['bright_black']),
            ("ColorTable09", colors['bright_blue']),
            ("ColorTable10", colors['bright_green']),
            ("ColorTable11", colors['bright_cyan']),
            ("ColorTable12", colors['bright_red']),
            ("ColorTable13", colors['bright_magenta']),
            ("ColorTable14", colors['bright_yellow']),
            ("ColorTable15", colors['bright_white']),
        ]
        
        for key_name, hex_color in color_mapping:
            colorref = self._hex_to_colorref(hex_color)
            winreg.SetValueEx(key, key_name, 0, winreg.REG_DWORD, colorref)
    
    def _hex_to_colorref(self, hex_color):
        """Convert hex color (#RRGGBB) to Windows COLORREF format (0x00BBGGRR)."""
        if not hex_color.startswith('#') or len(hex_color) != 7:
            raise ValueError(f"Invalid color format: {hex_color}")
        
        # Parse RGB components
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Convert to BGR DWORD format for Windows registry
        return (b << 16) | (g << 8) | r
    
    def read_current_colors(self):
        """Read current console colors from registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.CONSOLE_KEY_PATH,
                0,
                winreg.KEY_READ
            )
            
            try:
                color_table = []
                for i in range(16):
                    key_name = f"ColorTable{i:02d}"
                    try:
                        value, _ = winreg.QueryValueEx(key, key_name)
                        color_table.append(value)
                    except FileNotFoundError:
                        color_table.append(0)
                
                try:
                    screen_colors, _ = winreg.QueryValueEx(key, "ScreenColors")
                except FileNotFoundError:
                    screen_colors = 0x07
                
                return {
                    'color_table': color_table,
                    'screen_colors': screen_colors
                }
            finally:
                winreg.CloseKey(key)
                
        except Exception as e:
            raise Exception(f"Failed to read registry: {e}")
    
    def _colorref_to_hex(self, colorref):
        """Convert Windows COLORREF format (0x00BBGGRR) to hex color (#RRGGBB)."""
        r = colorref & 0xFF
        g = (colorref >> 8) & 0xFF
        b = (colorref >> 16) & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _opacity_to_window_alpha(self, opacity):
        """Convert opacity percentage (30-100) to WindowAlpha value (77-255)."""
        # Clamp opacity to valid range
        opacity = max(30, min(100, opacity))
        # Convert to WindowAlpha (0-255 scale, minimum 77)
        alpha = round(opacity * 255 / 100)
        return max(77, min(255, alpha))
    
    def set_opacity(self, opacity):
        """Set console opacity via WindowAlpha registry value."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.CONSOLE_KEY_PATH,
                0,
                winreg.KEY_WRITE
            )
            try:
                window_alpha = self._opacity_to_window_alpha(opacity)
                winreg.SetValueEx(key, "WindowAlpha", 0, winreg.REG_DWORD, window_alpha)
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Failed to set opacity: {e}")
    
    def get_opacity(self):
        """Get current console opacity from WindowAlpha registry value."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.CONSOLE_KEY_PATH,
                0,
                winreg.KEY_READ
            )
            try:
                window_alpha, _ = winreg.QueryValueEx(key, "WindowAlpha")
                # Convert WindowAlpha to opacity percentage
                opacity = round(window_alpha * 100 / 255)
                return opacity
            except FileNotFoundError:
                return None
            finally:
                winreg.CloseKey(key)
        except:
            return None
    
    def get_autorun(self):
        """Get current AutoRun value from registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.AUTORUN_KEY_PATH,
                0,
                winreg.KEY_READ
            )
            try:
                autorun, _ = winreg.QueryValueEx(key, "AutoRun")
                return autorun
            except FileNotFoundError:
                return None
            finally:
                winreg.CloseKey(key)
        except:
            return None
    
    def set_autorun(self, value):
        """Set AutoRun value in registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.AUTORUN_KEY_PATH,
                0,
                winreg.KEY_WRITE
            )
            try:
                if value:
                    winreg.SetValueEx(key, "AutoRun", 0, winreg.REG_SZ, value)
                else:
                    # Delete the value
                    try:
                        winreg.DeleteValue(key, "AutoRun")
                    except FileNotFoundError:
                        pass
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Failed to set AutoRun: {e}")
    
    def is_autoblur_enabled(self):
        """Check if autoblur is enabled in AutoRun."""
        autorun = self.get_autorun()
        if not autorun:
            return False
        # Check for the blur command in various forms
        script_path = os.path.abspath(__file__)
        return (f'"{script_path}" blur' in autorun or 
                'cmd_theme.py blur' in autorun or 
                'cmd_theme blur' in autorun)
    
    def enable_autoblur(self):
        """Enable autoblur - returns True if successful, False if already enabled."""
        current_autorun = self.get_autorun()
        
        # Get the path to this script
        script_path = os.path.abspath(__file__)
        blur_command = f'python "{script_path}" blur'
        
        # Check if already enabled
        if current_autorun and blur_command in current_autorun:
            return False  # Already enabled
        
        # Chain with existing AutoRun if present
        if current_autorun:
            new_autorun = f"{current_autorun} & {blur_command}"
        else:
            new_autorun = blur_command
        
        self.set_autorun(new_autorun)
        return True
    
    def disable_autoblur(self):
        """Disable autoblur - returns True if successful, False if not enabled."""
        current_autorun = self.get_autorun()
        
        if not current_autorun:
            return False  # Not enabled
        
        # Get the path to this script
        script_path = os.path.abspath(__file__)
        blur_command = f'python "{script_path}" blur'
        
        # Remove blur command from AutoRun
        if blur_command not in current_autorun:
            return False  # Not enabled
        
        # Remove the blur command
        new_autorun = current_autorun.replace(blur_command, '').strip()
        # Clean up any leftover & separators
        new_autorun = new_autorun.replace('& &', '&').strip('& ').strip()
        
        if new_autorun:
            self.set_autorun(new_autorun)
        else:
            self.set_autorun(None)
        
        return True


class BlurHandler:
    """Handles console window blur effects using Windows API."""
    
    # Windows API constants
    WCA_ACCENT_POLICY = 19
    ACCENT_ENABLE_GRADIENT = 1
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    
    def __init__(self):
        # Define structures
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", wintypes.DWORD),
                ("AccentFlags", wintypes.DWORD),
                ("GradientColor", wintypes.DWORD),
                ("AnimationId", wintypes.DWORD),
            ]
        
        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", wintypes.DWORD),
                ("Data", ctypes.POINTER(ACCENT_POLICY)),
                ("SizeOfData", ctypes.c_size_t),
            ]
        
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]
        
        self.ACCENT_POLICY = ACCENT_POLICY
        self.WINDOWCOMPOSITIONATTRIBDATA = WINDOWCOMPOSITIONATTRIBDATA
        self.RECT = RECT
        
        # Load required DLLs
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.dwmapi = ctypes.windll.dwmapi
        
        # Try to load SetWindowCompositionAttribute
        try:
            self.SetWindowCompositionAttribute = self.user32.SetWindowCompositionAttribute
            self.SetWindowCompositionAttribute.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)
            ]
            self.SetWindowCompositionAttribute.restype = wintypes.BOOL
        except AttributeError:
            self.SetWindowCompositionAttribute = None
        
        # Load DWM functions
        try:
            self.DwmGetWindowAttribute = self.dwmapi.DwmGetWindowAttribute
            self.DwmGetWindowAttribute.argtypes = [
                wintypes.HWND,
                wintypes.DWORD,
                ctypes.POINTER(RECT),
                wintypes.DWORD
            ]
            self.DwmGetWindowAttribute.restype = ctypes.c_long
        except AttributeError:
            self.DwmGetWindowAttribute = None
        
        # SetWindowRgn
        self.SetWindowRgn = self.user32.SetWindowRgn
        self.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
        self.SetWindowRgn.restype = ctypes.c_int
        
        # CreateRectRgn
        self.CreateRectRgn = self.user32.CreateRectRgn
        self.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.CreateRectRgn.restype = wintypes.HRGN
    
    def parse_tint_color(self, color_input):
        """Parse tint color from hex or color name."""
        # Color name mapping
        color_names = {
            'red': '#FF0000',
            'blue': '#0000FF',
            'green': '#00FF00',
            'purple': '#800080',
            'pink': '#FFC0CB',
            'orange': '#FFA500',
            'cyan': '#00FFFF',
            'yellow': '#FFFF00',
            'teal': '#008080',
            'white': '#FFFFFF',
            'black': '#000000'
        }
        
        # Check if it's a color name
        if color_input.lower() in color_names:
            return color_names[color_input.lower()]
        
        # Otherwise treat as hex
        if not color_input.startswith('#'):
            color_input = '#' + color_input
        
        # Validate hex format
        if len(color_input) != 7:
            raise ValueError(f"Invalid color format: {color_input}")
        
        try:
            int(color_input[1:], 16)
        except ValueError:
            raise ValueError(f"Invalid hex color: {color_input}")
        
        return color_input
    
    def apply_acrylic_blur(self, tint_color_hex, tint_opacity_percent, use_acrylic=False):
        """
        Apply blur with theme-based tint color.
        
        Args:
            tint_color_hex: Theme background color in #RRGGBB format
            tint_opacity_percent: Tint opacity 30-100% (lower = more transparent/blurry)
            use_acrylic: If True, use state 4 (acrylic, laggy on drag). If False, use state 3 (regular blur)
        """
        if not self.SetWindowCompositionAttribute:
            raise Exception("SetWindowCompositionAttribute not available on this system")
        
        # Get console window handle
        hwnd = self.kernel32.GetConsoleWindow()
        if not hwnd:
            raise Exception("Could not get console window handle")
        
        return self.apply_blur_to_window(hwnd, tint_color_hex, tint_opacity_percent, use_acrylic)
    
    def apply_blur_to_window(self, hwnd, tint_color_hex, tint_opacity_percent, use_acrylic=False):
        """
        Apply blur to a specific window.
        
        Args:
            hwnd: Window handle
            tint_color_hex: Theme background color in #RRGGBB format
            tint_opacity_percent: Tint opacity 30-100% (lower = more transparent/blurry)
            use_acrylic: If True, use state 4 (acrylic, laggy on drag). If False, use state 3 (regular blur)
        """
        if not self.SetWindowCompositionAttribute:
            raise Exception("SetWindowCompositionAttribute not available on this system")
        
        if not hwnd:
            raise Exception("Invalid window handle")
        
        # Convert hex color to BGR format and add tint opacity
        # Format: 0xAABBGGRR (A=alpha/tint opacity, BGR=color)
        gradient_color = self._hex_to_gradient_color(tint_color_hex, tint_opacity_percent)
        
        # Use state 3 (BLURBEHIND) by default for better performance
        # State 4 (ACRYLICBLURBEHIND) causes drag lag on Windows 10
        accent_state = self.ACCENT_ENABLE_ACRYLICBLURBEHIND if use_acrylic else self.ACCENT_ENABLE_BLURBEHIND
        
        # Try different AccentFlags to prevent edge bleed
        # Flags tested: 0, 2, 0x20|0x40|0x80|0x100 (border flags)
        accent_flags_to_try = [2, 0, 0x20 | 0x40 | 0x80 | 0x100]
        
        result = False
        for accent_flags in accent_flags_to_try:
            accent = self.ACCENT_POLICY()
            accent.AccentState = accent_state
            accent.AccentFlags = accent_flags
            accent.GradientColor = gradient_color
            accent.AnimationId = 0
            
            data = self.WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = self.WCA_ACCENT_POLICY
            data.Data = ctypes.pointer(accent)
            data.SizeOfData = ctypes.sizeof(accent)
            
            result = self.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
            
            if result:
                # Success with this flag combination
                break
        
        if not result:
            raise Exception("Failed to apply blur effect")
        
        return True
    
    def _hex_to_gradient_color(self, hex_color, opacity_percent):
        """
        Convert theme hex color and opacity to GradientColor DWORD.
        Format: 0xAABBGGRR where AA=tint opacity, BBGGRR=BGR color
        
        Args:
            hex_color: #RRGGBB format
            opacity_percent: 30-100 (tint opacity, lower = more see-through)
        
        Returns:
            DWORD in 0xAABBGGRR format
        """
        # Parse RGB from hex
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Convert opacity percent to alpha byte (0-255)
        # Clamp to 30-100 range for readability
        opacity_percent = max(30, min(100, opacity_percent))
        alpha = round(opacity_percent * 255 / 100)
        
        # Format: 0xAABBGGRR (alpha, blue, green, red)
        gradient_color = (alpha << 24) | (b << 16) | (g << 8) | r
        
        return gradient_color
    
    def apply_blur(self, use_acrylic=False):
        """Legacy method for backward compatibility - uses hardcoded dark tint."""
        # Use a default dark grey tint for legacy blur command
        return self.apply_acrylic_blur("#202020", 60, use_acrylic=use_acrylic)
    
    def clip_window_edges(self, hwnd):
        """Clip window to visible frame bounds to prevent edge bleed."""
        if not self.DwmGetWindowAttribute:
            return False
        
        try:
            # Get extended frame bounds (actual visible window rect)
            rect = self.RECT()
            result = self.DwmGetWindowAttribute(
                hwnd,
                self.DWMWA_EXTENDED_FRAME_BOUNDS,
                ctypes.byref(rect),
                ctypes.sizeof(rect)
            )
            
            if result != 0:  # S_OK = 0
                return False
            
            # Get window rect to calculate offset
            window_rect = self.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(window_rect))
            
            # Calculate region in window coordinates
            left = rect.left - window_rect.left
            top = rect.top - window_rect.top
            right = rect.right - window_rect.left
            bottom = rect.bottom - window_rect.top
            
            # Create rectangular region
            hrgn = self.CreateRectRgn(left, top, right, bottom)
            
            if not hrgn:
                return False
            
            # Apply region
            self.SetWindowRgn(hwnd, hrgn, True)
            
            return True
            
        except Exception as e:
            return False
    
    def remove_window_clip(self, hwnd):
        """Remove window clipping."""
        try:
            self.SetWindowRgn(hwnd, 0, True)  # NULL region = no clipping
            return True
        except:
            return False


class BackupManager:
    """Manages backup and restore of console settings."""
    
    def __init__(self):
        self.backup_dir = Path.home() / 'AppData' / 'Local' / 'cmd-theme-pack'
        self.backup_file = self.backup_dir / 'backup.json'
        self.history_file = self.backup_dir / 'history.json'
        self.settings_file = self.backup_dir / 'settings.json'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_exists(self):
        """Check if a backup exists."""
        return self.backup_file.exists()
    
    def save_blur_settings(self, tint=None, opacity=None, theme_background=None, use_acrylic=False):
        """Save blur settings for autoblur to use."""
        try:
            settings = {
                'tint': tint,
                'opacity': opacity,
                'theme_background': theme_background,
                'use_acrylic': use_acrylic
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            # Don't fail if settings can't be saved
            pass
    
    def load_blur_settings(self):
        """Load saved blur settings."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def clear_blur_settings(self):
        """Clear saved blur settings."""
        try:
            if self.settings_file.exists():
                self.settings_file.unlink()
        except:
            pass
    
    def save_state_before_apply(self, theme_name, opacity=None, blur=False, tint=None):
        """Save the state we're ABOUT TO APPLY (so undo can revert to it)."""
        try:
            # Load existing history
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Add new entry - this is what we're applying NOW
            # When we undo, we want to revert to what was BEFORE this
            entry = {
                'theme': theme_name,
                'opacity': opacity,
                'blur': blur,
                'tint': tint,
                'timestamp': time.time()
            }
            history.append(entry)
            
            # Keep only last 50 entries
            history = history[-50:]
            
            # Save history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            # Don't fail if history can't be saved
            pass
    
    def get_state_to_restore(self):
        """Get the state to restore (second-to-last entry) and remove current."""
        try:
            if not self.history_file.exists():
                return None
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if len(history) < 2:
                # Not enough history
                return None
            
            # Get second-to-last entry (the state before current)
            state_to_restore = history[-2]
            
            # Remove the last entry (current state)
            history = history[:-1]
            
            # Save updated history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
            
            return state_to_restore
        except:
            return None
    
    def create_backup(self):
        """Create a backup of current console settings."""
        handler = RegistryHandler()
        backup_data = {}
        
        try:
            # Backup color settings
            colors = handler.read_current_colors()
            backup_data['colors'] = colors
            
            # Backup opacity
            opacity = handler.get_opacity()
            if opacity is not None:
                backup_data['opacity'] = opacity
            
            # Backup AutoRun
            autorun = handler.get_autorun()
            if autorun is not None:
                backup_data['autorun'] = autorun
            
            # Backup Windows Terminal settings if available
            wt_handler = WindowsTerminalHandler()
            if wt_handler.is_available():
                wt_settings = wt_handler.get_current_settings()
                if wt_settings:
                    backup_data['windows_terminal'] = wt_settings
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def restore_backup(self):
        """Restore console settings from backup."""
        if not self.backup_exists():
            raise Exception("No backup found")
        
        try:
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            
            handler = RegistryHandler()
            
            # Restore colors if present
            if 'colors' in backup:
                colors = backup['colors']
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    RegistryHandler.CONSOLE_KEY_PATH,
                    0,
                    winreg.KEY_WRITE
                )
                
                try:
                    # Restore color table
                    for i, color in enumerate(colors['color_table']):
                        key_name = f"ColorTable{i:02d}"
                        winreg.SetValueEx(key, key_name, 0, winreg.REG_DWORD, color)
                    
                    # Restore screen colors
                    winreg.SetValueEx(key, "ScreenColors", 0, winreg.REG_DWORD, colors['screen_colors'])
                finally:
                    winreg.CloseKey(key)
            
            # Restore opacity if present
            if 'opacity' in backup:
                handler.set_opacity(backup['opacity'])
            else:
                # Remove WindowAlpha if it wasn't in backup
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        RegistryHandler.CONSOLE_KEY_PATH,
                        0,
                        winreg.KEY_WRITE
                    )
                    try:
                        winreg.DeleteValue(key, "WindowAlpha")
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(key)
                except:
                    pass
            
            # Restore AutoRun if present
            if 'autorun' in backup:
                handler.set_autorun(backup['autorun'])
            else:
                handler.set_autorun(None)
            
            # Restore Windows Terminal settings if present
            if 'windows_terminal' in backup:
                wt_handler = WindowsTerminalHandler()
                if wt_handler.is_available():
                    wt_settings = backup['windows_terminal']
                    wt_handler.apply_opacity_blur(
                        opacity=wt_settings.get('opacity'),
                        blur=wt_settings.get('useAcrylic', False)
                    )
            
            print("✓ Settings restored successfully!")
            print()
            print("Open a new Command Prompt window to see the original settings.")
            
        except Exception as e:
            raise Exception(f"Failed to restore backup: {e}")


class ThemePreviewer:
    """Displays visual preview of themes."""
    
    @staticmethod
    def enable_vt_mode():
        """Enable VT100 mode on Windows for ANSI color support."""
        try:
            kernel32 = ctypes.windll.kernel32
            # Get stdout handle
            stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            
            # Get current console mode
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode))
            
            # Enable VT processing (0x0004)
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
            
            # Set new console mode
            kernel32.SetConsoleMode(stdout_handle, mode)
            return True
        except:
            return False
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def color_block(hex_color, text="  "):
        """Return a colored block using truecolor ANSI escape."""
        r, g, b = ThemePreviewer.hex_to_rgb(hex_color)
        # Use background color for blocks
        return f"\x1b[48;2;{r};{g};{b}m{text}\x1b[0m"
    
    @staticmethod
    def preview_theme(theme):
        """Display a visual preview of the theme with colored blocks."""
        # Enable VT mode for colors
        ThemePreviewer.enable_vt_mode()
        
        print(f"\n{theme.name}")
        print("=" * len(theme.name))
        print(f"{theme.description}")
        print(f"Author: {theme.author} | Type: {theme.palette_type}")
        print()
        
        print("Colors:")
        print(f"  Background:   {ThemePreviewer.color_block(theme.colors['background'])} {theme.colors['background']}")
        print(f"  Foreground:   {ThemePreviewer.color_block(theme.colors['foreground'])} {theme.colors['foreground']}")
        print()
        
        print("ANSI Colors:")
        ansi_colors = [
            ('Black', 'black'),
            ('Red', 'red'),
            ('Green', 'green'),
            ('Yellow', 'yellow'),
            ('Blue', 'blue'),
            ('Magenta', 'magenta'),
            ('Cyan', 'cyan'),
            ('White', 'white'),
        ]
        
        for name, key in ansi_colors:
            normal = theme.colors[key]
            bright = theme.colors[f'bright_{key}']
            normal_block = ThemePreviewer.color_block(normal, "    ")
            bright_block = ThemePreviewer.color_block(bright, "    ")
            print(f"  {name:12} {normal_block} {normal:8}  Bright {name:12} {bright_block} {bright:8}")
        print()


def cmd_list(args):
    """Handle list command."""
    loader = ThemeLoader()
    themes = loader.list_themes()
    
    if not themes:
        print("No themes available.")
        return
    
    # Apply filter if specified
    if args.filter_type:
        if args.filter_type == 'dark':
            themes = [t for t in themes if t.palette_type == 'Dark']
        elif args.filter_type == 'light':
            themes = [t for t in themes if t.palette_type == 'Light']
    
    if not themes:
        print(f"No {args.filter_type} themes available.")
        return
    
    # Show filter in header
    header = "Available Themes"
    if args.filter_type:
        header += f" ({args.filter_type.title()})"
    
    print(f"{header}:")
    print()
    
    for theme in sorted(themes, key=lambda t: t.name):
        print(f"  {theme.name}")
        print(f"      {theme.description}")
        print(f"      Type: by {theme.author} • {theme.palette_type}")
        print()
    
    print(f"Total: {len(themes)} theme{'s' if len(themes) != 1 else ''}")


def cmd_preview(args):
    """Handle preview command."""
    loader = ThemeLoader()
    theme = loader.get_theme(args.theme_name)
    
    if not theme:
        print(f"ERROR: Theme '{args.theme_name}' not found", file=sys.stderr)
        print(file=sys.stderr)
        print("Available themes:", file=sys.stderr)
        for t in sorted(loader.list_themes(), key=lambda x: x.name):
            print(f"  - {t.name}", file=sys.stderr)
        sys.exit(1)
    
    ThemePreviewer.preview_theme(theme)


def cmd_apply(args):
    """Handle apply command."""
    loader = ThemeLoader()
    
    # Handle random theme selection
    if args.theme_name == 'random':
        themes = loader.list_themes()
        if not themes:
            print("ERROR: No themes available", file=sys.stderr)
            sys.exit(1)
        theme = random.choice(themes)
        print(f"Randomly selected: {theme.name}")
    else:
        theme = loader.get_theme(args.theme_name)
        
        if not theme:
            print(f"ERROR: Theme '{args.theme_name}' not found", file=sys.stderr)
            print(file=sys.stderr)
            print("Available themes:", file=sys.stderr)
            for t in sorted(loader.list_themes(), key=lambda x: x.name):
                print(f"  - {t.name}", file=sys.stderr)
            sys.exit(1)
    
    # Parse tint color if specified
    tint_color = None
    if args.tint:
        try:
            blur_handler = BlurHandler()
            tint_color = blur_handler.parse_tint_color(args.tint)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Handle --glass preset
    opacity = args.opacity
    blur = args.blur
    use_acrylic = args.acrylic if hasattr(args, 'acrylic') else False
    
    if args.glass:
        # Glass preset: enable blur and set opacity to 70 if not explicitly specified
        blur = True
        if opacity is None:
            opacity = 70
    
    # --tint implies --blur
    if tint_color:
        blur = True
    
    # Create backup manager early (needed for clearing settings)
    backup_manager = BackupManager()
    
    # Determine if we should reset effects or keep them
    # Reset to solid (100%, no blur, no tint) unless:
    # 1. User specified --opacity, --blur, --glass, --tint, or --acrylic
    # 2. User specified --keep-effects
    user_specified_effects = args.opacity is not None or args.blur or args.glass or args.tint or use_acrylic
    keep_effects = args.keep_effects
    
    if not user_specified_effects and not keep_effects:
        # Reset to solid (100% opacity, no blur, no tint)
        opacity = 100
        blur = False
        tint_color = None
        # Clear saved blur settings
        backup_manager.clear_blur_settings()
    
    # Create backup if it doesn't exist
    if not backup_manager.backup_exists():
        try:
            backup_manager.create_backup()
            print("✓ Backup created successfully")
        except Exception as e:
            print(f"ERROR: Failed to create backup: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Detect console type
    wt_handler = WindowsTerminalHandler()
    handler = RegistryHandler()
    is_windows_terminal = wt_handler.is_available()
    
    if is_windows_terminal:
        # Windows Terminal mode
        try:
            # Apply opacity and blur to Windows Terminal
            if opacity is not None or blur:
                wt_handler.apply_opacity_blur(opacity=opacity, blur=blur)
            
            print(f"✓ Theme '{theme.name}' configured for Windows Terminal!")
            if opacity:
                print(f"  Opacity: {opacity}%")
            if blur:
                print(f"  Blur: Enabled (acrylic)")
            if tint_color:
                print(f"  Note: Custom tint ({tint_color}) only applies to legacy CMD blur")
            print()
            print("Restart Windows Terminal or open a new tab to see the changes.")
            
            # Save to history AFTER successful apply
            backup_manager.save_state_before_apply(theme.name, opacity, blur, tint_color)
        except Exception as e:
            print(f"ERROR: Failed to configure Windows Terminal: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Legacy Console mode
        try:
            handler.apply_theme(theme, opacity=opacity)
            print(f"✓ Theme '{theme.name}' applied successfully to Legacy Console!")
            
            if opacity:
                print(f"  Opacity: {opacity}% (persistent)")
            
            # Apply blur to current window if requested
            if blur:
                try:
                    blur_handler = BlurHandler()
                    # Use custom tint if specified, otherwise use theme's background color
                    blur_tint = tint_color if tint_color else theme.colors['background']
                    blur_opacity = opacity if opacity else 70  # Default to 70% for blur
                    
                    # Save blur settings for autoblur to use
                    backup_manager.save_blur_settings(
                        tint=tint_color,
                        opacity=opacity,
                        theme_background=theme.colors['background'],
                        use_acrylic=use_acrylic
                    )
                    
                    # Set minimum opacity of 60% in WindowAlpha for glass to show through
                    if opacity and opacity < 60:
                        handler.set_opacity(60)
                        print(f"  Window opacity set to 60% (minimum for glass effect)")
                    
                    blur_handler.apply_acrylic_blur(blur_tint, blur_opacity, use_acrylic=use_acrylic)
                    
                    tint_desc = f"custom tint {tint_color}" if tint_color else "theme tint"
                    blur_type = "acrylic" if use_acrylic else "blur"
                    print(f"  Blur: Applied to current window ({blur_type} with {tint_desc}, {blur_opacity}% strength)")
                    
                    # Automatically enable autoblur when using glass effects
                    autoblur_enabled = handler.enable_autoblur()
                    if autoblur_enabled:
                        print(f"  Autoblur: Enabled for new CMD windows")
                    else:
                        print(f"  Autoblur: Already enabled")
                except Exception as e:
                    print(f"  Blur: Failed to apply - {e}", file=sys.stderr)
            else:
                # No blur requested - clear saved blur settings and disable autoblur if not keeping effects
                if not keep_effects:
                    backup_manager.clear_blur_settings()
                    autoblur_disabled = handler.disable_autoblur()
                    if autoblur_disabled:
                        print(f"  Autoblur: Disabled")
            
            print()
            print("Open a new Command Prompt window to see the changes.")
            
            # Save to history AFTER successful apply
            backup_manager.save_state_before_apply(theme.name, opacity, blur, tint_color)
        except PermissionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            print(file=sys.stderr)
            print("Try running from an elevated command prompt (Run as Administrator).", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to apply theme: {e}", file=sys.stderr)
            sys.exit(1)


def cmd_restore(args):
    """Handle restore command."""
    backup_manager = BackupManager()
    
    if not backup_manager.backup_exists():
        print("ERROR: No backup found", file=sys.stderr)
        print(file=sys.stderr)
        print("A backup is created automatically when you first apply a theme.", file=sys.stderr)
        print("Use 'python cmd_theme.py apply <theme>' to apply a theme.", file=sys.stderr)
        sys.exit(1)
    
    try:
        backup_manager.restore_backup()
        # Clear saved blur settings on restore
        backup_manager.clear_blur_settings()
    except Exception as e:
        print(f"ERROR: Failed to restore from backup: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_blur(args):
    """Handle blur command - apply blur to current console window."""
    try:
        # Autoblur should be silent - don't print messages
        is_interactive = sys.stdout.isatty()
        
        backup_manager = BackupManager()
        blur_handler = BlurHandler()
        
        # Load saved blur settings
        settings = backup_manager.load_blur_settings()
        
        if settings:
            # Use saved tint if available, otherwise use saved theme background
            tint = settings.get('tint')
            opacity = settings.get('opacity')
            theme_background = settings.get('theme_background')
            use_acrylic = settings.get('use_acrylic', False)
            
            blur_tint = tint if tint else (theme_background if theme_background else '#202020')
            blur_opacity = opacity if opacity else 70
            
            blur_handler.apply_acrylic_blur(blur_tint, blur_opacity, use_acrylic=use_acrylic)
            
            # Only print in interactive mode (not when called by autoblur)
            if is_interactive:
                tint_desc = f"custom tint {tint}" if tint else "theme tint"
                blur_type = "acrylic" if use_acrylic else "blur"
                print(f"✓ Blur effect applied ({blur_type} with {tint_desc}, {blur_opacity}% strength)")
        else:
            # No saved settings, use default
            blur_handler.apply_blur()
            if is_interactive:
                print("✓ Blur effect applied to current console window")
    except Exception as e:
        # Only print errors in interactive mode
        if sys.stdout.isatty():
            print(f"ERROR: Failed to apply blur: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_autoblur(args):
    """Handle autoblur command - enable/disable automatic blur on CMD start."""
    handler = RegistryHandler()
    
    if args.action == 'on':
        # Get current AutoRun value
        current_autorun = handler.get_autorun()
        
        # Get the path to this script
        script_path = os.path.abspath(__file__)
        blur_command = f'python "{script_path}" blur'
        
        # Check if already enabled
        if current_autorun and blur_command in current_autorun:
            print("Autoblur is already enabled")
            return
        
        # Chain with existing AutoRun if present
        if current_autorun:
            new_autorun = f"{current_autorun} & {blur_command}"
        else:
            new_autorun = blur_command
        
        try:
            handler.set_autorun(new_autorun)
            print("✓ Autoblur enabled")
            print(f"  Command: {blur_command}")
            print()
            print("Blur will be applied automatically when you start a new CMD window.")
        except Exception as e:
            print(f"ERROR: Failed to enable autoblur: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == 'off':
        # Get current AutoRun value
        current_autorun = handler.get_autorun()
        
        if not current_autorun:
            print("Autoblur is not enabled")
            return
        
        # Get the path to this script
        script_path = os.path.abspath(__file__)
        blur_command = f'python "{script_path}" blur'
        
        # Remove blur command from AutoRun
        if blur_command not in current_autorun:
            print("Autoblur is not enabled")
            return
        
        # Remove the blur command
        new_autorun = current_autorun.replace(blur_command, '').strip()
        # Clean up any leftover & separators
        new_autorun = new_autorun.replace('& &', '&').strip('& ').strip()
        
        try:
            if new_autorun:
                handler.set_autorun(new_autorun)
            else:
                handler.set_autorun(None)
            
            print("✓ Autoblur disabled")
        except Exception as e:
            print(f"ERROR: Failed to disable autoblur: {e}", file=sys.stderr)
            sys.exit(1)


def cmd_status(args):
    """Handle status command - show current theme, opacity, blur, tint, and autoblur state."""
    handler = RegistryHandler()
    wt_handler = WindowsTerminalHandler()
    backup_manager = BackupManager()
    
    print("Current Console Settings:")
    print()
    
    # Try to get last applied settings from history
    last_state = None
    try:
        if backup_manager.history_file.exists():
            with open(backup_manager.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                if history:
                    last_state = history[-1]
    except:
        pass
    
    # Check console type
    if wt_handler.is_available():
        print("Console Type: Windows Terminal")
        print()
        
        # Get Windows Terminal settings
        wt_settings = wt_handler.get_current_settings()
        if wt_settings:
            opacity = wt_settings.get('opacity')
            use_acrylic = wt_settings.get('useAcrylic', False)
            
            if opacity:
                print(f"  Opacity: {opacity}%")
            else:
                print(f"  Opacity: 100% (default)")
            
            if use_acrylic:
                print(f"  Blur: Enabled (acrylic)")
            else:
                print(f"  Blur: Disabled")
            
            if last_state and last_state.get('tint'):
                print(f"  Tint: {last_state['tint']} (applies to legacy CMD only)")
        else:
            print("  Could not read Windows Terminal settings")
    else:
        print("Console Type: Legacy Console (CMD)")
        print()
        
        # Get opacity
        opacity = handler.get_opacity()
        if opacity:
            print(f"  Opacity: {opacity}%")
        else:
            print(f"  Opacity: 100% (default)")
        
        # Show tint from last state
        if last_state and last_state.get('tint'):
            print(f"  Tint: {last_state['tint']}")
        
        # Check autoblur
        is_autoblur = handler.is_autoblur_enabled()
        if is_autoblur:
            print(f"  Autoblur: Enabled")
        else:
            print(f"  Autoblur: Disabled")
        
        print()
        print("  Note: Blur for legacy console is applied per-window via 'blur' command")
        print("        or automatically with 'autoblur on'")
    
    print()
    
    # Show last applied theme
    if last_state:
        print(f"Last Applied Theme: {last_state['theme']}")
        print()
    
    # Check for backup
    if backup_manager.backup_exists():
        print("Backup: Available (use 'restore' to revert)")
    else:
        print("Backup: None (will be created on first 'apply')")


def cmd_undo(args):
    """Handle undo command - revert to previous theme."""
    backup_manager = BackupManager()
    loader = ThemeLoader()
    
    # Get the state to restore (second-to-last, before current)
    state_to_restore = backup_manager.get_state_to_restore()
    
    if not state_to_restore:
        print("Nothing to undo.")
        print()
        print("Would you like to restore from backup instead?")
        print("Use 'python cmd_theme.py restore' to revert to original settings.")
        return
    
    # Get the theme from history
    theme_name = state_to_restore.get('theme')
    opacity = state_to_restore.get('opacity')
    blur = state_to_restore.get('blur', False)
    tint = state_to_restore.get('tint')
    
    if not theme_name:
        # No theme name stored, just restore opacity/blur settings
        print("Undoing settings...")
    else:
        # Load the theme
        theme = loader.get_theme(theme_name)
        if not theme:
            print(f"ERROR: Theme '{theme_name}' not found", file=sys.stderr)
            sys.exit(1)
        
        print(f"Undoing to: {theme.name}")
    
    # Detect console type
    wt_handler = WindowsTerminalHandler()
    handler = RegistryHandler()
    is_windows_terminal = wt_handler.is_available()
    
    if is_windows_terminal:
        # Windows Terminal mode
        try:
            if opacity is not None or blur:
                wt_handler.apply_opacity_blur(opacity=opacity, blur=blur)
            
            print(f"✓ Reverted to previous state")
            if opacity:
                print(f"  Opacity: {opacity}%")
            if blur:
                print(f"  Blur: Enabled")
            if tint:
                print(f"  Note: Custom tint ({tint}) only applies to legacy CMD")
            print()
            print("Restart Windows Terminal or open a new tab to see the changes.")
        except Exception as e:
            print(f"ERROR: Failed to revert: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Legacy Console mode
        try:
            if theme_name:
                theme = loader.get_theme(theme_name)
                if theme:
                    handler.apply_theme(theme, opacity=opacity)
                    print(f"✓ Reverted to theme '{theme.name}'")
                else:
                    # Theme not found, just restore opacity
                    if opacity is not None:
                        handler.set_opacity(opacity)
                        print(f"✓ Reverted opacity to {opacity}%")
            else:
                # No theme, just opacity
                if opacity is not None:
                    handler.set_opacity(opacity)
                    print(f"✓ Reverted opacity to {opacity}%")
            
            if opacity and theme_name:
                print(f"  Opacity: {opacity}% (persistent)")
            
            # Apply blur if it was enabled
            if blur:
                try:
                    blur_handler = BlurHandler()
                    if theme_name and theme:
                        # Use custom tint if stored, otherwise use theme's background color
                        blur_tint = tint if tint else theme.colors['background']
                        blur_opacity = opacity if opacity else 70
                        
                        # Set minimum opacity of 60% in WindowAlpha for glass to show through
                        if opacity and opacity < 60:
                            handler.set_opacity(60)
                        
                        blur_handler.apply_acrylic_blur(blur_tint, blur_opacity)
                        
                        tint_desc = f"custom tint {tint}" if tint else "theme tint"
                        print(f"  Blur: Applied to current window ({tint_desc})")
                    else:
                        blur_handler.apply_blur()
                        print(f"  Blur: Applied to current window")
                except Exception as e:
                    print(f"  Blur: Failed to apply - {e}", file=sys.stderr)
            
            print()
            print("Open a new Command Prompt window to see the changes.")
        except Exception as e:
            print(f"ERROR: Failed to revert: {e}", file=sys.stderr)
            sys.exit(1)



def main():
    """Main CLI entry point."""
    # If no arguments provided, launch GUI
    if len(sys.argv) == 1:
        if GUI_AVAILABLE:
            hide_console_window()
            gui = ThemeGUI()
            gui.run()
            return
        else:
            print("ERROR: GUI not available (tkinter not found)", file=sys.stderr)
            print("Use command-line arguments instead.", file=sys.stderr)
            sys.exit(1)
    
    parser = argparse.ArgumentParser(
        prog='cmd_theme.py',
        description='CMD Theme Pack - Manage and apply CMD color themes'
    )
    
    # Add version flag
    parser.add_argument('--version', action='version', version=f'CMD Theme Pack v{__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # GUI command
    parser_gui = subparsers.add_parser('gui', help='Open graphical user interface')
    parser_gui.set_defaults(func=cmd_gui)
    
    # Tune command
    parser_tune = subparsers.add_parser('tune', help='Interactive live tuning mode')
    parser_tune.set_defaults(func=cmd_tune)
    
    # List command
    parser_list = subparsers.add_parser('list', help='List all available themes')
    parser_list.add_argument('--dark', dest='filter_type', action='store_const', const='dark', help='Show only dark themes')
    parser_list.add_argument('--light', dest='filter_type', action='store_const', const='light', help='Show only light themes')
    parser_list.set_defaults(func=cmd_list, filter_type=None)
    
    # Preview command
    parser_preview = subparsers.add_parser('preview', help='Preview a theme without applying it')
    parser_preview.add_argument('theme_name', help='Theme name to preview')
    parser_preview.set_defaults(func=cmd_preview)
    
    # Apply command
    parser_apply = subparsers.add_parser('apply', help='Apply a theme to the console')
    parser_apply.add_argument('theme_name', help='Theme name to apply (or "random" for random selection)')
    parser_apply.add_argument('--opacity', type=int, metavar='N', help='Set opacity (30-100 percent)')
    parser_apply.add_argument('--blur', action='store_true', help='Enable blur effect (state 3, no drag lag)')
    parser_apply.add_argument('--glass', action='store_true', help='Preset: --opacity 70 --blur')
    parser_apply.add_argument('--tint', metavar='COLOR', help='Custom tint color (hex #RRGGBB or name: red, blue, green, purple, pink, orange, cyan, yellow, teal, white, black). Implies --blur.')
    parser_apply.add_argument('--acrylic', action='store_true', help='Use acrylic blur (state 4) instead of regular blur. WARNING: Causes drag lag on Windows 10.')
    parser_apply.add_argument('--keep-effects', action='store_true', help='Keep current opacity and blur settings')
    parser_apply.set_defaults(func=cmd_apply)
    
    # Restore command
    parser_restore = subparsers.add_parser('restore', help='Restore console settings from backup')
    parser_restore.set_defaults(func=cmd_restore)
    
    # Blur command
    parser_blur = subparsers.add_parser('blur', help='Apply blur to current console window (legacy CMD only)')
    parser_blur.set_defaults(func=cmd_blur)
    
    # Autoblur command
    parser_autoblur = subparsers.add_parser('autoblur', help='Enable/disable automatic blur on CMD start')
    parser_autoblur.add_argument('action', choices=['on', 'off'], help='Enable or disable autoblur')
    parser_autoblur.set_defaults(func=cmd_autoblur)
    
    # Status command
    parser_status = subparsers.add_parser('status', help='Show current theme, opacity, blur and autoblur state')
    parser_status.set_defaults(func=cmd_status)
    
    # Undo command
    parser_undo = subparsers.add_parser('undo', help='Revert to previously applied theme')
    parser_undo.set_defaults(func=cmd_undo)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()
