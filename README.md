# Consolor

Apply color themes to Windows Command Prompt, PowerShell, Windows Terminal, and Git Bash with transparency and blur effects.

## Installation

**Option 1: Executable (Windows)**

Download `cmd_theme.exe` from [Releases](https://github.com/yourusername/consolor/releases).

**Option 2: Python Script**

Requires Python 3.6+. No external dependencies.

```bash
python cmd_theme.py <command>
```

## Supported Terminals

- Command Prompt (CMD)
- PowerShell 5.1
- PowerShell 7 (pwsh)
- Windows Terminal
- Git Bash (mintty)

Each terminal can have its own theme independently.

## Commands

### GUI Mode

```bash
cmd_theme gui               # Launch graphical interface
```

The GUI provides:
- Visual theme preview with color palette display
- Live preview option to see blur effects on the GUI window
- Per-terminal selection (CMD, PowerShell, Windows Terminal, Git Bash, PowerShell 7)
- Tint color overlay with adjustable strength
- Opacity and blur controls
- Per-shell autoblur settings

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
cmd_theme apply <theme>                         # Apply to both CMD and PowerShell
cmd_theme apply <theme> --for cmd               # Apply to CMD only
cmd_theme apply <theme> --for powershell        # Apply to PowerShell only
cmd_theme apply <theme> --for pwsh              # Apply to PowerShell 7 only
cmd_theme apply <theme> --for wt                # Apply to Windows Terminal
cmd_theme apply <theme> --for gitbash           # Apply to Git Bash
cmd_theme apply <theme> --opacity 80            # Set opacity (30-100%)
cmd_theme apply <theme> --blur                  # Enable acrylic blur
cmd_theme apply <theme> --tint purple           # Add custom tint color
cmd_theme apply <theme> --glass                 # Preset: 70% opacity + blur
cmd_theme apply <theme> --keep-effects          # Keep current opacity/blur
cmd_theme apply random                          # Random theme selection
```

### Undo

```bash
cmd_theme undo                                  # Revert to previous theme
cmd_theme undo --for cmd                        # Undo CMD only
cmd_theme undo --for powershell                 # Undo PowerShell only
```

### Restore

```bash
cmd_theme restore                               # Restore original settings from backup
cmd_theme restore --for cmd                     # Restore CMD only
cmd_theme restore --for powershell              # Restore PowerShell only
cmd_theme restore --for wt                      # Restore Windows Terminal
cmd_theme restore --for gitbash                 # Restore Git Bash
```

### Reset

```bash
cmd_theme reset                                 # Alias for restore
cmd_theme reset --for powershell                # Reset PowerShell to classic blue
```

### Status

```bash
cmd_theme status                                # Show current theme, opacity, blur state
cmd_theme status --for cmd                      # Show CMD settings only
cmd_theme status --for powershell               # Show PowerShell settings only
```

### Blur (Legacy CMD/PowerShell Only)

```bash
cmd_theme blur                                  # Apply blur to current window
cmd_theme blur --shell powershell               # Apply blur for PowerShell
cmd_theme autoblur on                           # Enable blur for all new CMD windows
cmd_theme autoblur off                          # Disable autoblur
```

### Tune Mode

```bash
cmd_theme tune              # Interactive live tuning with keyboard controls
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
# Apply Nord to CMD with 75% opacity and blur
cmd_theme apply Nord --for cmd --opacity 75 --blur

# Apply Dracula to PowerShell only
cmd_theme apply Dracula --for powershell

# Apply Solarized Light to Windows Terminal
cmd_theme apply "Solarized Light" --for wt

# Apply Tokyo Night to Git Bash
cmd_theme apply "Tokyo Night" --for gitbash

# Add purple tint to blur effect
cmd_theme apply Nord --tint purple --blur

# Try different themes while keeping effects
cmd_theme apply Nord --glass
cmd_theme apply Dracula --keep-effects
cmd_theme apply Monokai --keep-effects

# Random theme with glass effect
cmd_theme apply random --glass

# Undo last change for specific shell
cmd_theme undo --for cmd

# Check current settings per shell
cmd_theme status --for powershell

# Reset PowerShell to classic blue defaults
cmd_theme reset --for powershell
```

## PowerShell Default Behavior

PowerShell always maintains its classic dark blue appearance unless explicitly themed with `--for powershell`. When applying a theme without `--for`, PowerShell is protected and keeps the classic blue (ScreenColors=0x56, dark blue background with yellow text).

## Security Note

The executable is unsigned and modifies the Windows registry (`HKCU\Console`). Windows SmartScreen and antivirus software may flag it. The source code is available for inspection. To build from source:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/themes;src/themes" --name cmd_theme cmd_theme.py
```

## Technical Details

- Modifies `HKEY_CURRENT_USER\Console` and per-shell registry keys for color settings
- Per-shell keys: `Console\%SystemRoot%_system32_cmd.exe`, `Console\%SystemRoot%_System32_WindowsPowerShell_v1.0_powershell.exe`
- Uses `WindowAlpha` registry value for opacity (77-255)
- Blur uses Windows API `SetWindowCompositionAttribute` with automatic edge clipping
- Automatic edge clipping prevents tint bleed using `DwmGetWindowAttribute`
- Windows Terminal: Modifies `settings.json` with color scheme and opacity
- Git Bash: Modifies `~/.minttyrc` with color settings
- PowerShell 7: Auto-detects registry key location
- Backup stored in `%LOCALAPPDATA%\consolor\backup.json`
- History stored in `%LOCALAPPDATA%\consolor\history.json`
- Per-shell blur settings in `%LOCALAPPDATA%\consolor\settings.json`

## License

MIT License
