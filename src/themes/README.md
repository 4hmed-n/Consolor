# Embedded Themes Directory

This directory contains the curated theme collection that will be embedded into the compiled binary.

## Theme File Format

Each theme file should be a JSON file following this structure:

```json
{
  "schema_version": "1.0",
  "name": "Theme Name",
  "description": "Theme description",
  "author": "Author Name",
  "palette_type": "Dark",
  "colors": {
    "background": "#000000",
    "foreground": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#00FF00",
    "yellow": "#FFFF00",
    "blue": "#0000FF",
    "magenta": "#FF00FF",
    "cyan": "#00FFFF",
    "white": "#FFFFFF",
    "bright_black": "#808080",
    "bright_red": "#FF8080",
    "bright_green": "#80FF80",
    "bright_yellow": "#FFFF80",
    "bright_blue": "#8080FF",
    "bright_magenta": "#FF80FF",
    "bright_cyan": "#80FFFF",
    "bright_white": "#FFFFFF"
  }
}
```

## Planned Themes

1. Dracula (Dark)
2. Solarized Dark
3. Solarized Light
4. Monokai (Dark)
5. Nord (Dark)
6. One Dark
7. One Light
8. Gruvbox Dark
9. Tokyo Night (Dark)
10. GitHub Light

Theme files will be added in subsequent tasks.
