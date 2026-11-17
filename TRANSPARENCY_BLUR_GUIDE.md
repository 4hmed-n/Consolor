# CMD Theme Pack - Transparency & Blur Guide

## New Features (Python Edition)

This enhanced version adds transparency and blur effects to CMD themes using **only Python standard library** (winreg, ctypes, json, argparse).

---

## 🎨 Apply Command with Effects

### Basic Syntax
```bash
python cmd_theme.py apply <theme> [--opacity N] [--blur] [--glass]
```

### Examples

**Apply theme with 75% opacity:**
```bash
python cmd_theme.py apply Nord --opacity 75
```

**Apply theme with opacity and blur:**
```bash
python cmd_theme.py apply Dracula --opacity 80 --blur
```

**Apply theme with glass preset (70% opacity + blur):**
```bash
python cmd_theme.py apply "Tokyo Night" --glass
```

**Apply theme normally (no transparency):**
```bash
python cmd_theme.py apply Monokai
```

---

## 🔧 Opacity (Transparency)

### How It Works
- **Range**: 30-100 percent
- **Registry Value**: WindowAlpha = round(N*255/100)
- **Minimum**: 77 (30%)
- **Maximum**: 255 (100%)
- **Location**: `HKCU\Console\WindowAlpha`

### Persistence
✅ **Persistent** - Opacity is saved to the registry and applies to all new CMD windows automatically.

### Legacy Console
```bash
# Set opacity to 75%
python cmd_theme.py apply Nord --opacity 75

# Check current opacity
python cmd_theme.py status
```

### Windows Terminal
```bash
# Sets "opacity": 75 in settings.json profile defaults
python cmd_theme.py apply Nord --opacity 75
```

---

## 💨 Blur (Acrylic Effect)

### How It Works
- Uses Windows API `SetWindowCompositionAttribute` via ctypes
- **ACCENT_POLICY state 4** = Acrylic blur (with fallback to state 3)
- **Flags**: 2
- **Color**: 0x99202020 (ABGR format)

### Persistence
⚠️ **Not Persistent for Legacy CMD** - Blur must be reapplied each time a window opens.

### Legacy Console

**Manual blur (current window only):**
```bash
python cmd_theme.py blur
```

**Apply theme with blur to current window:**
```bash
python cmd_theme.py apply Dracula --blur
```
Note: This applies blur immediately but prints a message that autoblur is needed for new windows.

**Enable autoblur (automatic for all new CMD windows):**
```bash
python cmd_theme.py autoblur on
```

**Disable autoblur:**
```bash
python cmd_theme.py autoblur off
```

### Windows Terminal
```bash
# Sets "useAcrylic": true in settings.json profile defaults
python cmd_theme.py apply Nord --blur
```
✅ **Persistent** - Blur is saved to settings.json

---

## 🔄 AutoRun Integration

### How Autoblur Works
When you enable autoblur, the tool modifies:
- **Registry Key**: `HKCU\Software\Microsoft\Command Processor\AutoRun`
- **Command Added**: `python "D:\path\to\cmd_theme.py" blur`

### Preserving Existing AutoRun
- If you already have an AutoRun value, the blur command is chained with `&`
- When disabling autoblur, the original AutoRun value is restored

### Example
```bash
# Before autoblur
AutoRun = "doskey ls=dir"

# After "autoblur on"
AutoRun = "doskey ls=dir & python "D:\New folder\cmd_theme.py" blur"

# After "autoblur off"
AutoRun = "doskey ls=dir"  # Restored to original
```

---

## 🎯 Glass Preset

The `--glass` flag is a convenient preset that combines:
- **Opacity**: 70%
- **Blur**: Enabled

```bash
python cmd_theme.py apply Nord --glass
```

Equivalent to:
```bash
python cmd_theme.py apply Nord --opacity 70 --blur
```

---

## 📊 Status Command

View current settings at any time:

```bash
python cmd_theme.py status
```

**Example Output:**
```
Current Console Settings:

Console Type: Legacy Console (CMD)

  Opacity: 70%
  Autoblur: Enabled

  Note: Blur for legacy console is applied per-window via 'blur' command
        or automatically with 'autoblur on'

Backup: Available (use 'restore' to revert)
```

---

## 💾 Backup & Restore

### What's Backed Up
The backup system now covers:
1. ✅ Color table (16 ColorTable entries)
2. ✅ ScreenColors value
3. ✅ WindowAlpha (opacity) - if set
4. ✅ AutoRun value - if set
5. ✅ Windows Terminal settings.json - if available

### Backup Location
`%LOCALAPPDATA%\cmd-theme-pack\backup.json`

### Automatic Backup
A backup is created automatically the first time you apply a theme.

### Manual Restore
```bash
python cmd_theme.py restore
```

This reverts **all** settings:
- Colors back to original
- Opacity removed (or restored to original value)
- AutoRun restored (autoblur removed or restored to original)
- Windows Terminal settings restored

---

## 🖥️ Console Type Detection

The tool automatically detects your console type:

### Legacy Console (CMD)
- Opacity: Registry-based (persistent)
- Blur: Windows API (requires autoblur for persistence)

### Windows Terminal
- Opacity: settings.json (persistent)
- Blur: settings.json as useAcrylic (persistent)

---

## 📝 All Commands Reference

```bash
# List themes
python cmd_theme.py list

# Preview theme
python cmd_theme.py preview <theme>

# Apply theme (various options)
python cmd_theme.py apply <theme>
python cmd_theme.py apply <theme> --opacity 75
python cmd_theme.py apply <theme> --blur
python cmd_theme.py apply <theme> --opacity 80 --blur
python cmd_theme.py apply <theme> --glass

# Blur commands (Legacy CMD only)
python cmd_theme.py blur
python cmd_theme.py autoblur on
python cmd_theme.py autoblur off

# Status and restore
python cmd_theme.py status
python cmd_theme.py restore

# Help
python cmd_theme.py --help
python cmd_theme.py apply --help
```

---

## 🎬 Complete Example Workflow

```bash
# 1. Check current status
python cmd_theme.py status

# 2. Apply theme with glass effect
python cmd_theme.py apply Dracula --glass

# 3. Enable autoblur for new windows
python cmd_theme.py autoblur on

# 4. Check status again
python cmd_theme.py status

# 5. Try a different theme with custom opacity
python cmd_theme.py apply Nord --opacity 85

# 6. Restore original settings
python cmd_theme.py restore
```

---

## ⚙️ Technical Details

### Windows API Calls (Blur)
```python
# Structures used
ACCENT_POLICY
WINDOWCOMPOSITIONATTRIBDATA

# API functions
kernel32.GetConsoleWindow()
user32.SetWindowCompositionAttribute()

# Constants
WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
```

### Registry Keys
```
Colors & Opacity:
HKCU\Console\ColorTable00-15
HKCU\Console\ScreenColors
HKCU\Console\WindowAlpha

AutoRun:
HKCU\Software\Microsoft\Command Processor\AutoRun
```

### Windows Terminal
```
File: %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json

Modified fields in profiles.defaults:
- "opacity": <number>
- "useAcrylic": <boolean>
```

---

## ✨ Tested Commands

All commands have been tested and verified:

✅ `python cmd_theme.py list` - Lists all 10 themes
✅ `python cmd_theme.py preview Dracula` - Shows theme details
✅ `python cmd_theme.py apply Nord --opacity 75` - Sets theme + opacity
✅ `python cmd_theme.py apply Dracula --opacity 80 --blur` - Full effects
✅ `python cmd_theme.py apply "Tokyo Night" --glass` - Glass preset works
✅ `python cmd_theme.py blur` - Applies blur to current window
✅ `python cmd_theme.py autoblur on` - Enables autoblur
✅ `python cmd_theme.py autoblur off` - Disables autoblur
✅ `python cmd_theme.py status` - Shows current settings
✅ `python cmd_theme.py restore` - Reverts all changes

---

## 🚀 Requirements

- **Python 3.6+**
- **Windows OS**
- **Standard library only**: winreg, ctypes, json, argparse
- **No external packages required**

---

## 🎨 Available Themes

1. Dracula
2. GitHub Light
3. Gruvbox Dark
4. Monokai
5. Nord
6. One Dark
7. One Light
8. Solarized Dark
9. Solarized Light
10. Tokyo Night
