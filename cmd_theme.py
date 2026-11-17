#!/usr/bin/env python3
"""CMD Theme Pack - Manage and apply CMD color themes (Python Edition)

A command-line utility for managing and applying color schemes to Windows Command Prompt.
Uses only Python standard library (winreg, json, argparse, ctypes).
"""

import winreg
import json
import argparse
import os
import sys
import ctypes
import random
import time
from pathlib import Path
from ctypes import wintypes


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


class BlurHandler:
    """Handles console window blur effects using Windows API."""
    
    # Windows API constants
    WCA_ACCENT_POLICY = 19
    ACCENT_ENABLE_GRADIENT = 1
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    
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
        
        self.ACCENT_POLICY = ACCENT_POLICY
        self.WINDOWCOMPOSITIONATTRIBDATA = WINDOWCOMPOSITIONATTRIBDATA
        
        # Load required DLLs
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
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
    
    def apply_acrylic_blur(self, tint_color_hex, tint_opacity_percent):
        """
        Apply Fluent acrylic blur with theme-based tint color.
        
        Args:
            tint_color_hex: Theme background color in #RRGGBB format
            tint_opacity_percent: Tint opacity 30-100% (lower = more transparent/blurry)
        """
        if not self.SetWindowCompositionAttribute:
            raise Exception("SetWindowCompositionAttribute not available on this system")
        
        # Get console window handle
        hwnd = self.kernel32.GetConsoleWindow()
        if not hwnd:
            raise Exception("Could not get console window handle")
        
        # Convert hex color to BGR format and add tint opacity
        # Format: 0xAABBGGRR (A=alpha/tint opacity, BGR=color)
        gradient_color = self._hex_to_gradient_color(tint_color_hex, tint_opacity_percent)
        
        # Try acrylic blur first (state 4)
        accent = self.ACCENT_POLICY()
        accent.AccentState = self.ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.AccentFlags = 2
        accent.GradientColor = gradient_color
        accent.AnimationId = 0
        
        data = self.WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = self.WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)
        
        result = self.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
        
        # If acrylic fails, fall back to regular blur (state 3)
        if not result:
            accent.AccentState = self.ACCENT_ENABLE_BLURBEHIND
            result = self.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
        
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
    
    def apply_blur(self):
        """Legacy method for backward compatibility - uses hardcoded dark tint."""
        # Use a default dark grey tint for legacy blur command
        return self.apply_acrylic_blur("#202020", 60)


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
    
    def save_blur_settings(self, tint=None, opacity=None, theme_background=None):
        """Save blur settings for autoblur to use."""
        try:
            settings = {
                'tint': tint,
                'opacity': opacity,
                'theme_background': theme_background
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
    # 1. User specified --opacity, --blur, --glass, or --tint
    # 2. User specified --keep-effects
    user_specified_effects = args.opacity is not None or args.blur or args.glass or args.tint
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
                        theme_background=theme.colors['background']
                    )
                    
                    # Set minimum opacity of 60% in WindowAlpha for glass to show through
                    if opacity and opacity < 60:
                        handler.set_opacity(60)
                        print(f"  Window opacity set to 60% (minimum for glass effect)")
                    
                    blur_handler.apply_acrylic_blur(blur_tint, blur_opacity)
                    
                    tint_desc = f"custom tint {tint_color}" if tint_color else "theme tint"
                    print(f"  Blur: Applied to current window (Fluent acrylic with {tint_desc}, {blur_opacity}% strength)")
                    print()
                    print("Note: Blur is not persistent for legacy console.")
                    print("Use 'python cmd_theme.py autoblur on' to enable blur for all new CMD windows.")
                except Exception as e:
                    print(f"  Blur: Failed to apply - {e}", file=sys.stderr)
            else:
                # No blur requested - clear saved blur settings if not keeping effects
                if not keep_effects:
                    backup_manager.clear_blur_settings()
            
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
        # Check if we're being called from autoblur (silent mode)
        # AutoRun typically passes command line directly, so check if stdout is a TTY
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
            
            blur_tint = tint if tint else (theme_background if theme_background else '#202020')
            blur_opacity = opacity if opacity else 70
            
            blur_handler.apply_acrylic_blur(blur_tint, blur_opacity)
            
            if is_interactive:
                tint_desc = f"custom tint {tint}" if tint else "theme tint"
                print(f"✓ Blur effect applied (Fluent acrylic with {tint_desc}, {blur_opacity}% strength)")
        else:
            # No saved settings, use default
            blur_handler.apply_blur()
            if is_interactive:
                print("✓ Blur effect applied to current console window")
    except Exception as e:
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
    parser = argparse.ArgumentParser(
        prog='cmd_theme.py',
        description='CMD Theme Pack - Manage and apply CMD color themes'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
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
    parser_apply.add_argument('--blur', action='store_true', help='Enable acrylic blur effect')
    parser_apply.add_argument('--glass', action='store_true', help='Preset: --opacity 70 --blur')
    parser_apply.add_argument('--tint', metavar='COLOR', help='Custom tint color (hex #RRGGBB or name: red, blue, green, purple, pink, orange, cyan, yellow, teal, white, black). Implies --blur.')
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
