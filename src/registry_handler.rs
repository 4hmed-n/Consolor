// Windows Registry handler for legacy console settings

use crate::theme::{ColorScheme, Theme};
use thiserror::Error;

#[cfg(windows)]
use winreg::enums::*;
#[cfg(windows)]
use winreg::RegKey;

/// Handles reading and modifying Windows Console registry settings
pub struct RegistryHandler {
    console_key_path: String,
}

impl RegistryHandler {
    /// Creates a new registry handler
    pub fn new() -> Self {
        Self {
            console_key_path: r"Console".to_string(),
        }
    }

    /// Applies a theme to the legacy console by modifying registry
    pub fn apply_theme(&self, theme: &Theme) -> Result<(), ApplyError> {
        #[cfg(not(windows))]
        {
            return Err(ApplyError::RegistryWrite(
                "Registry operations are only supported on Windows".to_string()
            ));
        }

        #[cfg(windows)]
        {
            // Open HKEY_CURRENT_USER\Console with write permissions
            let hkcu = RegKey::predef(HKEY_CURRENT_USER);
            let console_key = hkcu.open_subkey_with_flags(&self.console_key_path, KEY_WRITE)
                .map_err(|e| {
                    if e.kind() == std::io::ErrorKind::PermissionDenied {
                        ApplyError::PermissionDenied
                    } else {
                        ApplyError::RegistryWrite(format!("Failed to open Console registry key: {}", e))
                    }
                })?;

            // Write all 16 ColorTable entries
            self.write_color_table(&console_key, &theme.colors)?;

            // Calculate and write ScreenColors value
            // For now, use black background (index 0) and white foreground (index 7)
            // Background is in high nibble, foreground in low nibble: 0x00BF
            let background_index: u32 = 0;  // black
            let foreground_index: u32 = 7;  // white
            let screen_colors = (background_index << 4) | foreground_index;
            
            console_key.set_value("ScreenColors", &screen_colors)
                .map_err(|e| ApplyError::RegistryWrite(
                    format!("Failed to write ScreenColors: {}", e)
                ))?;

            Ok(())
        }
    }

    /// Reads current console colors from registry
    pub fn read_current_colors(&self) -> Result<ConsoleColors, ReadError> {
        #[cfg(not(windows))]
        {
            return Err(ReadError::RegistryError(
                "Registry operations are only supported on Windows".to_string()
            ));
        }

        #[cfg(windows)]
        {
            // Open HKEY_CURRENT_USER\Console with read permissions
            let hkcu = RegKey::predef(HKEY_CURRENT_USER);
            let console_key = hkcu.open_subkey_with_flags(&self.console_key_path, KEY_READ)
                .map_err(|e| ReadError::RegistryError(
                    format!("Failed to open Console registry key: {}", e)
                ))?;

            // Read all 16 ColorTable entries
            let mut color_table = Vec::with_capacity(16);
            for i in 0..16 {
                let key_name = format!("ColorTable{:02}", i);
                let color_value: u32 = console_key.get_value(&key_name)
                    .map_err(|e| ReadError::RegistryError(
                        format!("Failed to read {}: {}", key_name, e)
                    ))?;
                color_table.push(color_value);
            }

            // Read ScreenColors value
            let screen_colors: u32 = console_key.get_value("ScreenColors")
                .map_err(|e| ReadError::RegistryError(
                    format!("Failed to read ScreenColors: {}", e)
                ))?;

            Ok(ConsoleColors {
                color_table,
                screen_colors,
            })
        }
    }

    /// Writes color table to registry
    #[cfg(windows)]
    fn write_color_table(&self, console_key: &RegKey, colors: &ColorScheme) -> Result<(), WriteError> {
        // Map theme colors to registry ColorTable entries based on the design's mapping table
        let color_mapping = [
            ("ColorTable00", &colors.black),           // Index 0
            ("ColorTable01", &colors.blue),            // Index 1
            ("ColorTable02", &colors.green),           // Index 2
            ("ColorTable03", &colors.cyan),            // Index 3
            ("ColorTable04", &colors.red),             // Index 4
            ("ColorTable05", &colors.magenta),         // Index 5
            ("ColorTable06", &colors.yellow),          // Index 6
            ("ColorTable07", &colors.white),           // Index 7
            ("ColorTable08", &colors.bright_black),    // Index 8
            ("ColorTable09", &colors.bright_blue),     // Index 9
            ("ColorTable10", &colors.bright_green),    // Index 10
            ("ColorTable11", &colors.bright_cyan),     // Index 11
            ("ColorTable12", &colors.bright_red),      // Index 12
            ("ColorTable13", &colors.bright_magenta),  // Index 13
            ("ColorTable14", &colors.bright_yellow),   // Index 14
            ("ColorTable15", &colors.bright_white),    // Index 15
        ];

        // Write each color to the registry
        for (key_name, hex_color) in color_mapping.iter() {
            let colorref = self.hex_to_colorref(hex_color)
                .map_err(|e| WriteError::RegistryError(
                    format!("Failed to convert color {} for {}: {}", hex_color, key_name, e)
                ))?;

            console_key.set_value(key_name, &colorref)
                .map_err(|e| {
                    if e.kind() == std::io::ErrorKind::PermissionDenied {
                        WriteError::PermissionDenied
                    } else {
                        WriteError::RegistryError(
                            format!("Failed to write {}: {}", key_name, e)
                        )
                    }
                })?;
        }

        Ok(())
    }

    /// Converts hex color (#RRGGBB) to Windows COLORREF format (0x00BBGGRR)
    fn hex_to_colorref(&self, hex: &str) -> Result<u32, ColorError> {
        // Validate format: must start with #
        if !hex.starts_with('#') {
            return Err(ColorError::InvalidFormat(
                format!("Color must start with '#', got: {}", hex)
            ));
        }

        // Validate length: must be exactly 7 characters (#RRGGBB)
        if hex.len() != 7 {
            return Err(ColorError::InvalidFormat(
                format!("Color must be 7 characters (#RRGGBB), got {} characters: {}", hex.len(), hex)
            ));
        }

        // Parse R, G, B components from hex string
        let r = u32::from_str_radix(&hex[1..3], 16)
            .map_err(|e| ColorError::ParseError(
                format!("Failed to parse red component '{}': {}", &hex[1..3], e)
            ))?;
        
        let g = u32::from_str_radix(&hex[3..5], 16)
            .map_err(|e| ColorError::ParseError(
                format!("Failed to parse green component '{}': {}", &hex[3..5], e)
            ))?;
        
        let b = u32::from_str_radix(&hex[5..7], 16)
            .map_err(|e| ColorError::ParseError(
                format!("Failed to parse blue component '{}': {}", &hex[5..7], e)
            ))?;

        // Convert RGB to BGR DWORD format for Windows registry
        // Windows COLORREF format: 0x00BBGGRR
        Ok((b << 16) | (g << 8) | r)
    }

    /// Converts Windows COLORREF format (0x00BBGGRR) to hex color (#RRGGBB)
    pub fn colorref_to_hex(&self, colorref: u32) -> String {
        // Extract RGB components from BGR DWORD format
        let r = colorref & 0xFF;
        let g = (colorref >> 8) & 0xFF;
        let b = (colorref >> 16) & 0xFF;
        
        // Format as uppercase #RRGGBB string
        format!("#{:02X}{:02X}{:02X}", r, g, b)
    }

    /// Converts hex color (#RRGGBB) back to Windows COLORREF format (0x00BBGGRR)
    /// This is a public wrapper around hex_to_colorref for use by other modules
    pub fn colorref_to_hex_inverse(&self, hex: &str) -> Result<u32, ColorError> {
        self.hex_to_colorref(hex)
    }
}

/// Represents console colors read from registry
#[derive(Debug)]
pub struct ConsoleColors {
    pub color_table: Vec<u32>,
    pub screen_colors: u32,
}

/// Errors that can occur when applying themes via registry
#[derive(Debug, Error)]
pub enum ApplyError {
    #[error("Failed to write registry: {0}")]
    RegistryWrite(String),
    
    #[error("Insufficient permissions. Run as administrator.")]
    PermissionDenied,
    
    #[error("Color conversion error: {0}")]
    ColorError(#[from] ColorError),
}

/// Errors that can occur when reading registry
#[derive(Debug, Error)]
pub enum ReadError {
    #[error("Registry read error: {0}")]
    RegistryError(String),
    
    #[error("Not implemented")]
    NotImplemented,
}

/// Errors that can occur when writing registry
#[derive(Debug, Error)]
pub enum WriteError {
    #[error("Registry write error: {0}")]
    RegistryError(String),
    
    #[error("Permission denied")]
    PermissionDenied,
    
    #[error("Not implemented")]
    NotImplemented,
}

/// Errors that can occur during color conversion
#[derive(Debug, Error)]
pub enum ColorError {
    #[error("Invalid color format: {0}")]
    InvalidFormat(String),
    
    #[error("Parse error: {0}")]
    ParseError(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_colorref_to_hex() {
        let handler = RegistryHandler::new();

        // Test Red: 0x000000FF -> #FF0000
        assert_eq!(handler.colorref_to_hex(0x000000FF), "#FF0000");

        // Test Green: 0x0000FF00 -> #00FF00
        assert_eq!(handler.colorref_to_hex(0x0000FF00), "#00FF00");

        // Test Blue: 0x00FF0000 -> #0000FF
        assert_eq!(handler.colorref_to_hex(0x00FF0000), "#0000FF");

        // Test White: 0x00FFFFFF -> #FFFFFF
        assert_eq!(handler.colorref_to_hex(0x00FFFFFF), "#FFFFFF");

        // Test Black: 0x00000000 -> #000000
        assert_eq!(handler.colorref_to_hex(0x00000000), "#000000");

        // Test mixed color (purple): 0x00800080 -> #800080
        assert_eq!(handler.colorref_to_hex(0x00800080), "#800080");

        // Test Dracula background-ish: 0x00362A28 -> #282A36
        assert_eq!(handler.colorref_to_hex(0x00362A28), "#282A36");
    }

    #[test]
    fn test_hex_to_colorref_and_back() {
        let handler = RegistryHandler::new();

        // Test round-trip conversion
        let test_colors = vec![
            "#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000",
            "#282A36", "#F8F8F2", "#50FA7B", "#BD93F9", "#FF5555",
        ];

        for hex_color in test_colors {
            let colorref = handler.hex_to_colorref(hex_color).unwrap();
            let converted_back = handler.colorref_to_hex(colorref);
            assert_eq!(hex_color, converted_back, 
                "Round trip failed for {}: got {}", hex_color, converted_back);
        }
    }

    #[test]
    fn test_hex_to_colorref_basic_colors() {
        let handler = RegistryHandler::new();

        // Test pure red: #FF0000 -> 0x000000FF
        assert_eq!(
            handler.hex_to_colorref("#FF0000").unwrap(),
            0x000000FF,
            "Red should convert to BGR format with B=0, G=0, R=255"
        );

        // Test pure green: #00FF00 -> 0x0000FF00
        assert_eq!(
            handler.hex_to_colorref("#00FF00").unwrap(),
            0x0000FF00,
            "Green should convert to BGR format with B=0, G=255, R=0"
        );

        // Test pure blue: #0000FF -> 0x00FF0000
        assert_eq!(
            handler.hex_to_colorref("#0000FF").unwrap(),
            0x00FF0000,
            "Blue should convert to BGR format with B=255, G=0, R=0"
        );
    }

    #[test]
    fn test_hex_to_colorref_grayscale() {
        let handler = RegistryHandler::new();

        // Test white: #FFFFFF -> 0x00FFFFFF
        assert_eq!(
            handler.hex_to_colorref("#FFFFFF").unwrap(),
            0x00FFFFFF,
            "White should convert to BGR format with all components at 255"
        );

        // Test black: #000000 -> 0x00000000
        assert_eq!(
            handler.hex_to_colorref("#000000").unwrap(),
            0x00000000,
            "Black should convert to BGR format with all components at 0"
        );

        // Test gray: #808080 -> 0x00808080
        assert_eq!(
            handler.hex_to_colorref("#808080").unwrap(),
            0x00808080,
            "Gray should convert to BGR format with all components at 128"
        );
    }

    #[test]
    fn test_hex_to_colorref_mixed_colors() {
        let handler = RegistryHandler::new();

        // Test cyan: #00FFFF -> 0x00FFFF00
        assert_eq!(
            handler.hex_to_colorref("#00FFFF").unwrap(),
            0x00FFFF00,
            "Cyan should convert to BGR format"
        );

        // Test magenta: #FF00FF -> 0x00FF00FF
        assert_eq!(
            handler.hex_to_colorref("#FF00FF").unwrap(),
            0x00FF00FF,
            "Magenta should convert to BGR format"
        );

        // Test yellow: #FFFF00 -> 0x0000FFFF
        assert_eq!(
            handler.hex_to_colorref("#FFFF00").unwrap(),
            0x0000FFFF,
            "Yellow should convert to BGR format"
        );
    }

    #[test]
    fn test_hex_to_colorref_case_insensitive() {
        let handler = RegistryHandler::new();

        // Test lowercase
        assert_eq!(
            handler.hex_to_colorref("#ff0000").unwrap(),
            0x000000FF,
            "Lowercase hex should be accepted"
        );

        // Test uppercase
        assert_eq!(
            handler.hex_to_colorref("#FF0000").unwrap(),
            0x000000FF,
            "Uppercase hex should be accepted"
        );

        // Test mixed case
        assert_eq!(
            handler.hex_to_colorref("#fF00Ff").unwrap(),
            0x00FF00FF,
            "Mixed case hex should be accepted"
        );
    }

    #[test]
    fn test_hex_to_colorref_real_theme_colors() {
        let handler = RegistryHandler::new();

        // Test Dracula theme background: #282a36
        assert_eq!(
            handler.hex_to_colorref("#282a36").unwrap(),
            0x00362a28,
            "Dracula background should convert correctly"
        );

        // Test Dracula foreground: #f8f8f2
        assert_eq!(
            handler.hex_to_colorref("#f8f8f2").unwrap(),
            0x00f2f8f8,
            "Dracula foreground should convert correctly"
        );

        // Test Dracula purple: #bd93f9
        assert_eq!(
            handler.hex_to_colorref("#bd93f9").unwrap(),
            0x00f993bd,
            "Dracula purple should convert correctly"
        );
    }

    #[test]
    fn test_hex_to_colorref_missing_hash() {
        let handler = RegistryHandler::new();

        let result = handler.hex_to_colorref("FF0000");
        assert!(result.is_err(), "Should reject color without #");

        match result.unwrap_err() {
            ColorError::InvalidFormat(msg) => {
                assert!(
                    msg.contains("must start with '#'"),
                    "Error message should mention missing # character"
                );
            }
            _ => panic!("Expected InvalidFormat error"),
        }
    }

    #[test]
    fn test_hex_to_colorref_invalid_length() {
        let handler = RegistryHandler::new();

        // Too short
        let result = handler.hex_to_colorref("#FF00");
        assert!(result.is_err(), "Should reject color that's too short");
        match result.unwrap_err() {
            ColorError::InvalidFormat(msg) => {
                assert!(
                    msg.contains("must be 7 characters"),
                    "Error message should mention incorrect length"
                );
            }
            _ => panic!("Expected InvalidFormat error"),
        }

        // Too long
        let result = handler.hex_to_colorref("#FF0000FF");
        assert!(result.is_err(), "Should reject color that's too long");
        match result.unwrap_err() {
            ColorError::InvalidFormat(msg) => {
                assert!(
                    msg.contains("must be 7 characters"),
                    "Error message should mention incorrect length"
                );
            }
            _ => panic!("Expected InvalidFormat error"),
        }
    }

    #[test]
    fn test_hex_to_colorref_invalid_hex_characters() {
        let handler = RegistryHandler::new();

        // Invalid character in red component
        let result = handler.hex_to_colorref("#GG0000");
        assert!(result.is_err(), "Should reject invalid hex character G");
        match result.unwrap_err() {
            ColorError::ParseError(msg) => {
                assert!(
                    msg.contains("red component"),
                    "Error message should identify which component failed"
                );
            }
            _ => panic!("Expected ParseError"),
        }

        // Invalid character in green component
        let result = handler.hex_to_colorref("#00ZZ00");
        assert!(result.is_err(), "Should reject invalid hex character Z");
        match result.unwrap_err() {
            ColorError::ParseError(msg) => {
                assert!(
                    msg.contains("green component"),
                    "Error message should identify which component failed"
                );
            }
            _ => panic!("Expected ParseError"),
        }

        // Invalid character in blue component
        let result = handler.hex_to_colorref("#0000XX");
        assert!(result.is_err(), "Should reject invalid hex character X");
        match result.unwrap_err() {
            ColorError::ParseError(msg) => {
                assert!(
                    msg.contains("blue component"),
                    "Error message should identify which component failed"
                );
            }
            _ => panic!("Expected ParseError"),
        }
    }

    #[test]
    fn test_hex_to_colorref_edge_cases() {
        let handler = RegistryHandler::new();

        // Test with all zeros except one component at max
        assert_eq!(
            handler.hex_to_colorref("#FF0000").unwrap(),
            0x000000FF,
            "Max red should work"
        );
        assert_eq!(
            handler.hex_to_colorref("#00FF00").unwrap(),
            0x0000FF00,
            "Max green should work"
        );
        assert_eq!(
            handler.hex_to_colorref("#0000FF").unwrap(),
            0x00FF0000,
            "Max blue should work"
        );

        // Test with single digit values (01, 02, etc.)
        assert_eq!(
            handler.hex_to_colorref("#010203").unwrap(),
            0x00030201,
            "Small values should convert correctly"
        );
    }

    #[test]
    fn test_hex_to_colorref_descriptive_errors() {
        let handler = RegistryHandler::new();

        // Test that error messages contain the input value
        let result = handler.hex_to_colorref("invalid");
        assert!(result.is_err());
        let err_msg = format!("{}", result.unwrap_err());
        assert!(
            err_msg.contains("invalid"),
            "Error message should include the invalid input"
        );

        // Test that parse errors are descriptive
        let result = handler.hex_to_colorref("#GGGGGG");
        assert!(result.is_err());
        let err_msg = format!("{}", result.unwrap_err());
        assert!(
            err_msg.contains("GG") || err_msg.contains("component"),
            "Parse error should mention the problematic component"
        );
    }
}
