# Implementation Plan: CMD Theme Pack

## Overview

This implementation plan breaks down the CMD Theme Pack feature into discrete coding tasks. The approach follows a bottom-up implementation strategy: starting with core data structures and utilities, then building the theme management system, console handlers, and finally the CLI interface. Each task builds on previous work to ensure incremental progress and early validation.

## Tasks

- [x] 1. Set up Rust project structure and dependencies
  - Initialize Cargo project with required dependencies (serde, serde_json, clap, colored, dirs, thiserror, winreg, windows)
  - Configure build profile for optimized release builds
  - Create module structure: theme.rs, theme_loader.rs, console_detector.rs, wt_handler.rs, registry_handler.rs, backup_manager.rs, previewer.rs, cli.rs
  - Set up embedded themes directory structure (src/themes/)
  - _Requirements: 9.2, 9.3_

- [x] 2. Implement core theme data structures and validation
  - [x] 2.1 Create Theme and ColorScheme data structures
    - Define Theme struct with schema_version, name, description, author, palette_type, and colors fields
    - Define ColorScheme struct with all 18 color fields (background, foreground, 16 ANSI colors)
    - Define PaletteType enum (Dark, Light)
    - Add Serialize and Deserialize derives for JSON support
    - _Requirements: 1.3, 2.1, 2.2_

  - [x] 2.2 Implement hex color validation function
    - Create validate_hex_color function that checks format #RRGGBB
    - Validate starts with '#', exactly 7 characters, valid hex digits
    - Return descriptive validation errors
    - _Requirements: 2.2, 10.4_

  - [ ]* 2.3 Write property test for hex color validation
    - **Property 1: Hex Color Format Validation**
    - **Validates: Requirements 2.2, 10.4**
    - Generate arbitrary strings and verify validation correctly identifies valid/invalid hex colors

  - [x] 2.4 Implement theme validation function
    - Create validate_theme function checking all required fields present
    - Validate schema version matches expected version
    - Validate all color fields using hex color validator
    - Validate metadata fields are non-empty
    - Return descriptive errors identifying specific missing/invalid fields
    - _Requirements: 1.4, 1.5, 2.3, 2.4, 2.5_

  - [ ]* 2.5 Write property test for theme completeness validation
    - **Property 2: Theme Completeness Validation**
    - **Validates: Requirements 1.3, 1.4, 2.3, 2.4**
    - Generate arbitrary theme objects with missing/invalid fields and verify validation catches all issues

  - [ ]* 2.6 Write property test for validation error descriptiveness
    - **Property 4: Validation Error Descriptiveness**
    - **Validates: Requirements 2.5, 10.2, 10.5**
    - Generate themes with various validation errors and verify error messages contain field names and descriptions

- [ ] 3. Implement color conversion utilities
  - [x] 3.1 Create hex to BGR DWORD conversion function
    - Implement hex_to_colorref function parsing #RRGGBB to RGB values
    - Convert RGB to BGR format: (B << 16) | (G << 8) | R
    - Handle parsing errors with descriptive messages
    - _Requirements: 5.2_

  - [x] 3.2 Create BGR DWORD to hex conversion function
    - Implement colorref_to_hex function extracting RGB from DWORD
    - Format as uppercase #RRGGBB string
    - _Requirements: 6.2, 6.3_

  - [ ]* 3.3 Write property test for color conversion round-trip
    - **Property 7: Color Conversion Round-Trip**
    - **Validates: Requirements 5.2**
    - Generate arbitrary valid hex colors and verify round-trip conversion preserves values

  - [ ]* 3.4 Write unit tests for color conversion edge cases
    - Test black (#000000), white (#FFFFFF), primary colors
    - Test conversion matches expected BGR DWORD values
    - _Requirements: 5.2_

- [x] 4. Create curated theme collection
  - [x] 4.1 Create 10 theme JSON files with proper attribution
    - Create Dracula.json, SolarizedDark.json, SolarizedLight.json
    - Create Monokai.json, Nord.json, OneDark.json, OneLight.json
    - Create GruvboxDark.json, TokyoNight.json, GithubLight.json
    - Include all metadata (name, description, author, palette_type)
    - Define all 18 colors for each theme following design specifications
    - Place in src/themes/ directory for embedding
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 4.2 Write validation tests for all theme files
    - Load each embedded theme JSON and validate structure
    - Verify all required fields present and colors valid
    - _Requirements: 1.5, 2.4_

- [x] 5. Implement theme loader
  - [x] 5.1 Create ThemeLoader struct with embedded theme loading
    - Define ThemeLoader struct with HashMap for embedded and user themes
    - Implement new() method loading embedded themes using include_str! macro
    - Parse each embedded JSON and validate themes on load
    - Store themes in embedded_themes HashMap keyed by name
    - Skip and log warning for any invalid embedded themes
    - _Requirements: 1.5, 1.6, 9.2, 9.3, 10.2_

  - [x] 5.2 Add user theme directory loading
    - Detect user themes directory: %LOCALAPPDATA%\cmd-theme-pack\themes\
    - Create directory if it doesn't exist
    - Scan for .json files and parse as themes
    - Validate user themes on load, skip invalid ones with warnings
    - Store in user_themes HashMap
    - _Requirements: 9.4, 9.5_

  - [x] 5.3 Implement theme merging and query methods
    - Implement get_theme method returning user theme if exists, else embedded theme
    - Implement list_themes method merging both sources (user themes override embedded)
    - Ensure user themes with same name override embedded themes
    - _Requirements: 9.5_

  - [ ]* 5.4 Write property test for theme merging deduplication
    - **Property 3: Theme Merging Deduplication**
    - **Validates: Requirements 9.5**
    - Generate arbitrary theme sets with overlapping names and verify user themes override built-in

  - [ ]* 5.5 Write unit tests for theme loader
    - Test embedded theme loading succeeds
    - Test user directory creation
    - Test theme deduplication with same-named themes
    - _Requirements: 9.3, 9.4, 9.5_

- [x] 6. Checkpoint - Ensure core theme system works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement console detection
  - [x] 7.1 Create ConsoleType enum and ConsoleDetector
    - Define ConsoleType enum: WindowsTerminal { settings_path }, LegacyConsole, Unknown
    - Create ConsoleDetector struct with detect() method
    - Implement Windows Terminal detection checking standard settings.json locations
    - Check %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
    - Check %LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json (unpackaged)
    - Return WindowsTerminal with path if found, else LegacyConsole
    - _Requirements: 8.2, 8.3, 8.4_

  - [ ]* 7.2 Write unit tests for console detection
    - Test Windows Terminal detection with mocked filesystem
    - Test fallback to LegacyConsole when Windows Terminal not found
    - _Requirements: 8.2, 8.4_

- [x] 8. Implement Windows Terminal handler
  - [x] 8.1 Create WindowsTerminalHandler struct
    - Define WindowsTerminalHandler with settings_path field
    - Implement new() constructor accepting path
    - Implement read_settings() method parsing settings.json
    - Preserve existing JSON structure using serde_json::Value
    - _Requirements: 8.3_

  - [x] 8.2 Implement theme application for Windows Terminal
    - Implement apply_theme() method modifying settings.json
    - Add or update color scheme in schemes array
    - Convert Theme format to Windows Terminal JSON format
    - Preserve all existing user configuration
    - Write updated settings.json with pretty printing (4-space indentation)
    - _Requirements: 5.1, 8.3_

  - [x] 8.3 Add current scheme detection
    - Implement get_current_scheme() method reading defaults.colorScheme
    - Return currently active scheme name if set
    - _Requirements: 3.3_

  - [ ]* 8.4 Write unit tests for Windows Terminal handler
    - Test parsing existing settings.json
    - Test adding new color scheme
    - Test updating existing scheme with same name
    - Test preserving user configuration
    - _Requirements: 8.3_

- [x] 9. Implement registry handler for legacy console
  - [x] 9.1 Create RegistryHandler struct
    - Define RegistryHandler with console_key_path field
    - Implement new() constructor with path HKCU\Console
    - Import winreg crate functionality for registry access
    - _Requirements: 8.4_

  - [x] 9.2 Implement color table writing for registry
    - Implement write_color_table() method writing ColorTable00-ColorTable15
    - Map theme colors to registry keys using design's mapping table
    - Convert colors using hex_to_colorref
    - Calculate ScreenColors value from background/foreground indices
    - _Requirements: 5.2, 5.3_

  - [x] 9.3 Implement theme application for registry
    - Implement apply_theme() method orchestrating color table write
    - Open HKCU\Console registry key with write permissions
    - Write all 16 ColorTable entries
    - Write ScreenColors combining background/foreground
    - Handle permission errors with descriptive messages
    - _Requirements: 5.1, 5.2, 5.5_

  - [x] 9.4 Implement current colors reading from registry
    - Implement read_current_colors() method reading all ColorTable values
    - Convert BGR DWORD values back to hex format
    - Read ScreenColors to determine current background/foreground
    - _Requirements: 6.2_

  - [ ]* 9.5 Write unit tests for registry handler
    - Test hex to DWORD conversion for ColorTable values
    - Test ScreenColors calculation
    - Test color table mapping correctness
    - _Requirements: 5.2_

- [x] 10. Implement backup manager
  - [x] 10.1 Create BackupManager struct
    - Define BackupManager with backup_dir field
    - Implement new() constructor creating backup directory if needed
    - Use %LOCALAPPDATA%\cmd-theme-pack\backups\ for backup storage
    - _Requirements: 6.2_

  - [x] 10.2 Implement backup creation
    - Implement create_backup() method accepting ConsoleType
    - For WindowsTerminal: copy settings.json to wt_backup.json
    - For LegacyConsole: export registry values to console_backup.json
    - Only create backup if backup file doesn't already exist
    - Handle file write errors with descriptive messages
    - _Requirements: 6.1, 6.2, 10.3_

  - [x] 10.3 Implement backup restoration
    - Implement restore_backup() method accepting ConsoleType
    - Check backup_exists() before attempting restore
    - For WindowsTerminal: restore settings.json from wt_backup.json
    - For LegacyConsole: restore registry values from console_backup.json
    - Display confirmation message on successful restore
    - _Requirements: 6.3, 6.4, 6.5_

  - [ ]* 10.4 Write unit tests for backup manager
    - Test backup creation with mocked filesystem
    - Test backup_exists() check
    - Test restore from backup
    - Test handling missing backup gracefully
    - _Requirements: 6.1, 6.3, 6.4_

- [x] 11. Checkpoint - Ensure console handlers and backup work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement theme previewer
  - [x] 12.1 Create ThemePreviewer struct and preview display
    - Define ThemePreviewer struct
    - Implement preview_theme() method accepting Theme reference
    - Display theme metadata (name, description, author, palette type) in formatted box
    - Use colored crate for terminal formatting
    - _Requirements: 4.1, 4.3_

  - [x] 12.2 Add color palette display
    - Implement display_color_palette() showing all 16 ANSI colors
    - Display color name, hex value, and colored block for each color
    - Show standard and bright variants side by side
    - Include background and foreground colors
    - _Requirements: 4.2, 4.3_

  - [x] 12.3 Add sample content display
    - Implement display_sample_content() showing realistic command output examples
    - Display sample directory listing with colors
    - Display sample success, warning, error messages in different colors
    - Demonstrate foreground and background color combination
    - _Requirements: 4.4_

  - [ ]* 12.4 Write property test for preview output completeness
    - **Property 5: Preview Output Completeness**
    - **Validates: Requirements 4.2, 4.3**
    - Generate arbitrary valid themes and verify preview output includes all 18 colors

  - [ ]* 12.5 Write property test for display metadata completeness
    - **Property 6: Display Metadata Completeness**
    - **Validates: Requirements 3.4**
    - Generate arbitrary themes and verify preview includes name, description, author, palette_type

  - [ ]* 12.6 Write unit tests for previewer
    - Test preview output contains theme name and metadata
    - Test all color names appear in output
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 13. Implement CLI interface
  - [x] 13.1 Define CLI structure with clap
    - Create Cli struct with Parser derive
    - Define Commands enum: List, Preview, Apply, Restore, Help
    - Add command-specific arguments (theme_name for Preview/Apply, no-backup flag for Apply)
    - Configure command descriptions and help text
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 13.2 Implement list command handler
    - Create handle_list() function loading all themes
    - Display each theme with name, description, author, and palette type
    - Format output with clear visual separation
    - Indicate currently applied theme if detectable
    - Handle no themes found scenario with helpful message
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 13.3 Implement preview command handler
    - Create handle_preview() function accepting theme name
    - Load requested theme from theme loader
    - Use ThemePreviewer to display theme
    - Handle theme not found with error listing available themes
    - Ensure Console_Settings are not modified during preview
    - _Requirements: 4.1, 4.5, 5.6_

  - [x] 13.4 Implement apply command handler
    - Create handle_apply() function accepting theme name and no-backup flag
    - Detect console type using ConsoleDetector
    - Load requested theme from theme loader
    - Create backup unless no-backup flag set or backup exists
    - Apply theme using appropriate handler (WT or Registry)
    - Display confirmation message on success
    - Handle permission errors requesting administrator privileges
    - Handle theme not found with error listing available themes
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 13.5 Implement restore command handler
    - Create handle_restore() function
    - Detect console type using ConsoleDetector
    - Check backup exists using BackupManager
    - Restore from backup using BackupManager
    - Display confirmation message on success
    - Handle no backup exists scenario with informative message
    - _Requirements: 6.3, 6.4, 6.5_

  - [x] 13.6 Implement help and error handling
    - Implement handle_help() displaying usage information
    - Add default behavior when invoked without arguments (show help)
    - Handle invalid commands with error suggesting help command
    - Ensure all error messages are clear and user-friendly
    - _Requirements: 7.1, 7.4, 7.5, 7.6_

  - [ ]* 13.7 Write integration tests for CLI commands
    - Test list command with sample themes
    - Test preview command with valid theme
    - Test apply command flow (detect, backup, apply)
    - Test restore command flow
    - Test error cases (invalid theme, no backup, etc.)
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 14. Implement main entry point and error handling
  - [x] 14.1 Create main.rs entry point
    - Parse command-line arguments using Cli::parse()
    - Route to appropriate command handler based on Commands enum
    - Implement global error handling with descriptive messages
    - Set up consistent error formatting across all commands
    - _Requirements: 7.1, 7.4, 10.1_

  - [x] 14.2 Add operating system validation
    - Detect Windows version at startup
    - Display clear error if not Windows 10 or Windows 11
    - Show minimum requirements in error message
    - _Requirements: 8.1, 8.5_

  - [x] 14.3 Implement comprehensive error reporting
    - Define error display formatting for all error types
    - For registry errors: show specific cause and suggest admin privileges if needed
    - For theme validation errors: show file name, line info, and validation issues
    - For file write errors: show location and permission requirements
    - For invalid colors: show which color field and the invalid value
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 14.4 Write integration tests for error scenarios
    - Test handling of non-existent theme
    - Test handling of restore without backup
    - Test handling of permission errors
    - Test handling of malformed theme file
    - _Requirements: 10.1, 10.2, 10.3_

- [ ] 15. Build configuration and optimization
  - [x] 15.1 Configure release build optimizations
    - Set profile.release with strip = true, lto = true, codegen-units = 1
    - Set opt-level = "z" for size optimization
    - Configure embedded themes to compile into binary
    - _Requirements: 9.1, 9.2_

  - [x] 15.2 Create README for user themes directory
    - Write README.txt explaining theme file format
    - Provide example theme JSON with comments
    - Include instructions for adding custom themes
    - Place README in themes directory template
    - _Requirements: 9.4_

  - [x] 15.3 Build and test release executable
    - Build release executable: cargo build --release
    - Verify single executable output
    - Test executable runs without dependencies
    - Verify embedded themes are accessible
    - Check executable size is reasonable (< 5 MB)
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 16. Final checkpoint - Comprehensive testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements from the requirements document for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties from the design document
- Unit and integration tests validate specific examples and error cases
- The implementation follows bottom-up order: data structures → utilities → theme management → console handlers → CLI
- All Windows-specific functionality is conditionally compiled for the Windows target
- Backup is created automatically before first theme application to ensure safety

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1"]
    },
    {
      "id": 1,
      "tasks": ["2.1", "4.1"]
    },
    {
      "id": 2,
      "tasks": ["2.2", "2.4"]
    },
    {
      "id": 3,
      "tasks": ["2.3", "2.5", "2.6", "3.1", "3.2", "4.2"]
    },
    {
      "id": 4,
      "tasks": ["3.3", "3.4", "5.1"]
    },
    {
      "id": 5,
      "tasks": ["5.2"]
    },
    {
      "id": 6,
      "tasks": ["5.3"]
    },
    {
      "id": 7,
      "tasks": ["5.4", "5.5", "7.1"]
    },
    {
      "id": 8,
      "tasks": ["7.2", "8.1", "9.1", "10.1"]
    },
    {
      "id": 9,
      "tasks": ["8.2", "9.2", "10.2"]
    },
    {
      "id": 10,
      "tasks": ["8.3", "9.3"]
    },
    {
      "id": 11,
      "tasks": ["8.4", "9.4", "9.5", "10.3"]
    },
    {
      "id": 12,
      "tasks": ["10.4", "12.1"]
    },
    {
      "id": 13,
      "tasks": ["12.2", "12.3"]
    },
    {
      "id": 14,
      "tasks": ["12.4", "12.5", "12.6", "13.1"]
    },
    {
      "id": 15,
      "tasks": ["13.2", "13.3", "13.4", "13.5", "13.6"]
    },
    {
      "id": 16,
      "tasks": ["13.7", "14.1"]
    },
    {
      "id": 17,
      "tasks": ["14.2", "14.3"]
    },
    {
      "id": 18,
      "tasks": ["14.4", "15.1", "15.2"]
    },
    {
      "id": 19,
      "tasks": ["15.3"]
    }
  ]
}
```
