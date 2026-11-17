# CMD Theme Pack

A command-line utility for managing and applying color schemes to Windows Command Prompt environments.

## Features

- 🎨 Curated collection of beautiful CMD themes
- 🔄 Easy theme switching with backup/restore functionality
- 👁️ Preview themes before applying
- 🪟 Supports both Windows Terminal and legacy console
- 📦 Single executable with embedded themes

## Project Structure

```
cmd-theme/
├── src/
│   ├── main.rs              # Application entry point
│   ├── cli.rs               # Command-line interface
│   ├── theme.rs             # Theme data structures
│   ├── theme_loader.rs      # Theme loading and validation
│   ├── console_detector.rs  # Console type detection
│   ├── wt_handler.rs        # Windows Terminal handler
│   ├── registry_handler.rs  # Legacy console registry handler
│   ├── backup_manager.rs    # Backup/restore functionality
│   ├── previewer.rs         # Theme preview display
│   └── themes/              # Embedded theme files
├── Cargo.toml               # Project dependencies
└── README.md                # This file
```

## Building

Requires Rust toolchain (1.70+):

```bash
cargo build --release
```

The compiled executable will be in `target/release/cmd-theme.exe`.

## Usage

```bash
# List all available themes
cmd-theme list

# Preview a theme
cmd-theme preview dracula

# Apply a theme
cmd-theme apply dracula

# Restore from backup
cmd-theme restore
```

## Requirements

- Windows 10 or Windows 11
- Administrator privileges may be required for legacy console registry modifications

## License

See LICENSE file for details.
