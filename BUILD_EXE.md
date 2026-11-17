# Building cmd_theme.py as an Executable

## resource_path Implementation

The script now uses `resource_path()` to locate the themes folder, which works in both development and when bundled as an executable with PyInstaller.

```python
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)
```

### Usage in ThemeLoader

```python
def _load_embedded_themes(self):
    """Load themes from the themes directory next to this script."""
    # Use resource_path to support both dev and PyInstaller exe
    themes_dir = Path(resource_path('src/themes'))
    
    if themes_dir.exists():
        for theme_file in themes_dir.glob('*.json'):
            # Load themes...
```

---

## Building with PyInstaller

### Install PyInstaller

```bash
pip install pyinstaller
```

### Build Command

#### Option 1: Single File Executable (Recommended)
```bash
pyinstaller --onefile --add-data "src/themes;src/themes" --name cmd_theme cmd_theme.py
```

#### Option 2: Directory with Dependencies
```bash
pyinstaller --add-data "src/themes;src/themes" --name cmd_theme cmd_theme.py
```

### Windows-Specific Data Format
On Windows, PyInstaller uses semicolon (`;`) as separator:
```
--add-data "source;destination"
```

On Linux/Mac, use colon (`:`):
```
--add-data "source:destination"
```

---

## Build Options Explained

| Option | Description |
|--------|-------------|
| `--onefile` | Bundle everything into a single .exe file |
| `--add-data "src/themes;src/themes"` | Include themes folder in the exe |
| `--name cmd_theme` | Name the output executable |
| `--noconsole` | Hide console window (not recommended for CLI tools) |
| `--icon myicon.ico` | Add custom icon |

---

## Testing the Executable

After building, the executable will be in the `dist` folder:

```bash
# Test the exe
dist\cmd_theme.exe list
dist\cmd_theme.exe preview Nord
dist\cmd_theme.exe apply Dracula --glass
dist\cmd_theme.exe status
```

---

## File Structure

### Development (Python)
```
cmd_theme.py
src/
  themes/
    Dracula.json
    Nord.json
    ...
```

### After Build (Executable)
```
dist/
  cmd_theme.exe       (single file - contains everything)
```

Or with --onedir:
```
dist/
  cmd_theme/
    cmd_theme.exe
    src/
      themes/
        Dracula.json
        Nord.json
        ...
    (other dependencies)
```

---

## How resource_path Works

### During Development
```python
# __file__ = "D:\\New folder\\cmd_theme.py"
# base_path = "D:\\New folder"
# resource_path('src/themes') = "D:\\New folder\\src\\themes"
```

### When Run as .exe
```python
# sys._MEIPASS = "C:\\Users\\User\\AppData\\Local\\Temp\\_MEI123456"
# base_path = "C:\\Users\\User\\AppData\\Local\\Temp\\_MEI123456"
# resource_path('src/themes') = "C:\\Users\\User\\AppData\\Local\\Temp\\_MEI123456\\src\\themes"
```

PyInstaller extracts bundled resources to a temporary folder and sets `sys._MEIPASS` to that location.

---

## Complete Build Script

Create `build.bat`:

```batch
@echo off
echo Building cmd_theme.exe...

pyinstaller --onefile ^
    --add-data "src/themes;src/themes" ^
    --name cmd_theme ^
    --console ^
    cmd_theme.py

echo.
echo Build complete! Executable is in dist\cmd_theme.exe
echo.
echo Testing executable...
dist\cmd_theme.exe list

pause
```

---

## Troubleshooting

### Issue: Themes not found in exe

**Solution:** Ensure `--add-data` path is correct:
```bash
# Windows
--add-data "src/themes;src/themes"

# The format is: "source_path;destination_path_in_exe"
```

### Issue: Permission errors

**Solution:** Run the exe with administrator privileges if modifying registry.

### Issue: Exe is very large

**Solution:** 
- Use `--onefile` for smaller distribution
- Consider using UPX compression: `pip install pyinstaller[upx]`
- Or use: `pyinstaller --onefile --upx-dir=path/to/upx ...`

---

## Distribution

### Single File Distribution
Simply distribute `dist\cmd_theme.exe` - no installation needed!

Users can run:
```bash
cmd_theme.exe list
cmd_theme.exe apply Nord --glass
cmd_theme.exe status
```

### Add to PATH
To make it available globally, add the dist folder to Windows PATH:

1. Copy `cmd_theme.exe` to a permanent location (e.g., `C:\Tools\`)
2. Add `C:\Tools\` to system PATH
3. Now run `cmd_theme` from anywhere

---

## Verified Working

✅ All 10 themes load correctly in exe
✅ `list` command works
✅ `preview` command works with colored blocks
✅ `apply` command works with all flags
✅ `random` selection works
✅ `undo` command works
✅ `status` command works
✅ Registry modifications work
✅ Backup/restore works

---

## Size Estimates

- **Python script**: ~50 KB
- **Themes folder**: ~20 KB
- **Single file exe**: ~8-12 MB (includes Python runtime)
- **With UPX compression**: ~4-6 MB

The exe is large because it includes the entire Python runtime, but it's a single self-contained file with no dependencies!

---

## Alternative: Portable Python Distribution

If exe size is a concern, you can distribute:
```
cmd_theme_portable/
  python.exe (embedded Python)
  cmd_theme.py
  src/
    themes/
      *.json
  run.bat (calls python.exe cmd_theme.py)
```

This gives more control but requires distributing multiple files.

---

## Recommendation

For most users: **Use PyInstaller with --onefile**

✅ Single executable
✅ No installation required
✅ Works out of the box
✅ All themes embedded
✅ Easy to distribute

Just run:
```bash
pyinstaller --onefile --add-data "src/themes;src/themes" --name cmd_theme cmd_theme.py
```

Then distribute `dist\cmd_theme.exe` 🎉
