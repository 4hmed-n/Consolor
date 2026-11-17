# Consolor

Apply color themes to Windows Command Prompt and terminal with transparency and blur effects.

## Installation

**Option 1: Executable (Windows)**

Download `cmd_theme.exe` from [Releases](https://github.com/yourusername/consolor/releases).

**Option 2: Python Script**

Requires Python 3.6+. No external dependencies.

```bash
python cmd_theme.py <command>
```

## Commands

### List Themes

```bash
cmd_theme list              # All themes
cmd_theme list --dark       # Dark themes only
cmd_theme list --light      # Light themes only
```

### Preview Theme

```bash
cmd_theme preview <theme>   # Shows colors as colored blocks
```

### Apply Theme

```bash
cmd_theme apply <theme>                    # Apply theme (resets to solid)
cmd_theme apply <theme> --opacity 80       # Set opacity (30-100%)
cmd_theme apply <theme> --blur             # Enable acrylic blur
cmd_theme apply <theme> --glass            # Preset: 70% opacity + blur
cmd_theme apply <theme> --keep-effects     # Keep current opacity/blur
cmd_theme apply random                     # Random theme selection
```

### Undo

```bash
cmd_theme undo              # Revert to previous theme
```

### Restore

```bash
cmd_theme restore           # Restore original settings from backup
```

### Status

```bash
cmd_theme status            # Show current theme, opacity, blur state
```

### Blur (Legacy CMD Only)

```bash
cmd_theme blur              # Apply blur to current window
cmd_theme autoblur on       # Enable blur for all new CMD windows
cmd_theme autoblur off      # Disable autoblur
```

## Available Themes

- Dracula
- GitHub Light
- Gruvbox Dark
- Monokai
- Nord
- One Dark
- One Light
- Solarized Dark
- Solarized Light
- Tokyo Night

## Examples

```bash
# Apply Nord with 75% opacity and blur
cmd_theme apply Nord --opacity 75 --blur

# Try different themes while keeping effects
cmd_theme apply Nord --glass
cmd_theme apply Dracula --keep-effects
cmd_theme apply Monokai --keep-effects

# Random theme with glass effect
cmd_theme apply random --glass

# Undo last change
cmd_theme undo

# Check current settings
cmd_theme status
```

## Security Note

The executable is unsigned and modifies the Windows registry (`HKCU\Console`). Windows SmartScreen and antivirus software may flag it. The source code is available for inspection. To build from source:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/themes;src/themes" --name cmd_theme cmd_theme.py
```

## Technical Details

- Modifies `HKEY_CURRENT_USER\Console` for color settings
- Uses `WindowAlpha` registry value for opacity (77-255)
- Blur uses Windows API `SetWindowCompositionAttribute` (non-persistent for CMD)
- Backup stored in `%LOCALAPPDATA%\cmd-theme-pack\backup.json`
- History stored in `%LOCALAPPDATA%\cmd-theme-pack\history.json`

## License

MIT License
