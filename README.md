# Consolor

Apply color themes to Windows Command Prompt, PowerShell, Windows Terminal, and Git Bash with transparency and blur effects.

## Installation

**Option 1: Executable (Windows)**

Download `consolor.exe` from [Releases](https://github.com/4hmed-n/Consolor/releases).

**Option 2: Python Script**

Requires Python 3.6+. No external dependencies.

```bash
python consolor.py <command>
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
consolor gui               # Launch graphical interface
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
consolor list              # All themes
consolor list --dark       # Dark themes only
consolor list --light      # Light themes only
```

### Preview Theme

```bash
consolor preview <theme>   # Shows colors as colored blocks
```

### Apply Theme

```bash
consolor apply <theme>                         # Apply to CMD only (default for legacy console)
consolor apply <theme> --for cmd               # Apply to CMD only
consolor apply <theme> --for powershell        # Apply to PowerShell only
consolor apply <theme> --for pwsh              # Apply to PowerShell 7 only
consolor apply <theme> --for wt                # Apply to Windows Terminal
consolor apply <theme> --for gitbash           # Apply to Git Bash
consolor apply <theme> --opacity 80            # Set opacity (30-100%)
consolor apply <theme> --blur                  # Enable acrylic blur
consolor apply <theme> --tint purple           # Add custom tint color
consolor apply <theme> --glass                 # Preset: 70% opacity + blur
consolor apply <theme> --keep-effects          # Keep current opacity/blur
consolor apply random                          # Random theme selection
```

### Undo

```bash
consolor undo                                  # Revert to previous theme
consolor undo --for cmd                        # Undo CMD only
consolor undo --for powershell                 # Undo PowerShell only
```

### Restore

```bash
consolor restore                               # Restore original settings from backup
consolor restore --for cmd                     # Restore CMD only
consolor restore --for powershell              # Restore PowerShell only
consolor restore --for wt                      # Restore Windows Terminal
consolor restore --for gitbash                 # Restore Git Bash
```

### Reset

```bash
consolor reset                                 # Alias for restore
consolor reset --for powershell                # Reset PowerShell to classic blue
```

### Status

```bash
consolor status                                # Show current theme, opacity, blur state
consolor status --for cmd                      # Show CMD settings only
consolor status --for powershell               # Show PowerShell settings only
```

### Blur (Legacy CMD/PowerShell Only)

```bash
consolor blur                                  # Apply blur to current window
consolor blur --shell powershell               # Apply blur for PowerShell
consolor autoblur on                           # Enable blur for all new CMD windows
consolor autoblur off                          # Disable autoblur
```

### Tune Mode

```bash
consolor tune              # Interactive live tuning with keyboard controls
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
consolor apply Nord --for cmd --opacity 75 --blur

# Apply Dracula to PowerShell only
consolor apply Dracula --for powershell

# Apply Solarized Light to Windows Terminal
consolor apply "Solarized Light" --for wt

# Apply Tokyo Night to Git Bash
consolor apply "Tokyo Night" --for gitbash

# Add purple tint to blur effect
consolor apply Nord --tint purple --blur

# Try different themes while keeping effects
consolor apply Nord --glass
consolor apply Dracula --keep-effects
consolor apply Monokai --keep-effects

# Random theme with glass effect
consolor apply random --glass

# Undo last change for specific shell
consolor undo --for cmd

# Check current settings per shell
consolor status --for powershell

# Reset PowerShell to classic blue defaults
consolor reset --for powershell
```

## PowerShell Default Behavior

PowerShell always maintains its classic dark blue appearance unless explicitly themed with `--for powershell`. When applying a theme without `--for`, PowerShell is protected and keeps the classic blue (ScreenColors=0x56, dark blue background with yellow text).

## Security Note

The executable is unsigned and modifies the Windows registry (`HKCU\Console`). Windows SmartScreen and antivirus software may flag it. The source code is available for inspection. To build from source:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/themes;src/themes" --name consolor consolor.py
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
