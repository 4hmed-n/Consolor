// Theme data structures and color scheme definitions

use serde::{Deserialize, Serialize};

// Import ValidationError from theme_loader
use crate::theme_loader::ValidationError;

/// Represents a complete theme with metadata and color scheme
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Theme {
    pub schema_version: String,
    pub name: String,
    pub description: String,
    pub author: String,
    pub palette_type: PaletteType,
    pub colors: ColorScheme,
}

/// Indicates whether a theme is designed for dark or light backgrounds
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PaletteType {
    Dark,
    Light,
}

/// Complete color scheme with background, foreground, and 16 ANSI colors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColorScheme {
    pub background: String,
    pub foreground: String,
    pub black: String,
    pub red: String,
    pub green: String,
    pub yellow: String,
    pub blue: String,
    pub magenta: String,
    pub cyan: String,
    pub white: String,
    pub bright_black: String,
    pub bright_red: String,
    pub bright_green: String,
    pub bright_yellow: String,
    pub bright_blue: String,
    pub bright_magenta: String,
    pub bright_cyan: String,
    pub bright_white: String,
}

/// Validates that a string represents a valid hexadecimal RGB color in the format #RRGGBB
///
/// # Arguments
/// * `color` - A string slice representing a color value
///
/// # Returns
/// * `Ok(())` if the color is valid
/// * `Err(ValidationError)` with a specific error if validation fails
///
/// # Validation Rules
/// * Must start with '#' character
/// * Must be exactly 7 characters long (#RRGGBB)
/// * Characters 1-6 must be valid hexadecimal digits (0-9, A-F, a-f)
///
/// # Examples
/// ```
/// # use cmd_theme::theme::validate_hex_color;
/// assert!(validate_hex_color("#FF0000").is_ok());  // Valid red
/// assert!(validate_hex_color("#00ff00").is_ok());  // Valid green (lowercase)
/// assert!(validate_hex_color("FF0000").is_err());  // Missing #
/// assert!(validate_hex_color("#FF00").is_err());   // Too short
/// assert!(validate_hex_color("#GGGGGG").is_err()); // Invalid hex
/// ```
pub fn validate_hex_color(color: &str) -> Result<(), ValidationError> {
    // Must start with #
    if !color.starts_with('#') {
        return Err(ValidationError::MissingHash);
    }
    
    // Must be exactly 7 characters (#RRGGBB)
    if color.len() != 7 {
        return Err(ValidationError::InvalidLength);
    }
    
    // Characters 1-6 must be valid hex
    for c in color[1..].chars() {
        if !c.is_ascii_hexdigit() {
            return Err(ValidationError::InvalidHexCharacter);
        }
    }
    
    Ok(())
}

/// Validates that a theme has all required fields and valid values
///
/// # Arguments
/// * `theme` - A reference to the Theme to validate
///
/// # Returns
/// * `Ok(())` if the theme is valid
/// * `Err(ValidationError)` with a specific error if validation fails
///
/// # Validation Rules
/// * Schema version must be "1.0"
/// * Name must be non-empty
/// * Description must be non-empty
/// * Author must be non-empty
/// * All 18 color fields must be valid hex colors (#RRGGBB format)
///
/// # Examples
/// ```
/// # use cmd_theme::theme::{Theme, ColorScheme, PaletteType, validate_theme};
/// let theme = Theme {
///     schema_version: "1.0".to_string(),
///     name: "Test Theme".to_string(),
///     description: "A test theme".to_string(),
///     author: "Test Author".to_string(),
///     palette_type: PaletteType::Dark,
///     colors: ColorScheme {
///         background: "#000000".to_string(),
///         foreground: "#FFFFFF".to_string(),
///         black: "#000000".to_string(),
///         red: "#FF0000".to_string(),
///         green: "#00FF00".to_string(),
///         yellow: "#FFFF00".to_string(),
///         blue: "#0000FF".to_string(),
///         magenta: "#FF00FF".to_string(),
///         cyan: "#00FFFF".to_string(),
///         white: "#FFFFFF".to_string(),
///         bright_black: "#808080".to_string(),
///         bright_red: "#FF8080".to_string(),
///         bright_green: "#80FF80".to_string(),
///         bright_yellow: "#FFFF80".to_string(),
///         bright_blue: "#8080FF".to_string(),
///         bright_magenta: "#FF80FF".to_string(),
///         bright_cyan: "#80FFFF".to_string(),
///         bright_white: "#FFFFFF".to_string(),
///     },
/// };
/// assert!(validate_theme(&theme).is_ok());
/// ```
pub fn validate_theme(theme: &Theme) -> Result<(), ValidationError> {
    // Validate schema version
    const EXPECTED_VERSION: &str = "1.0";
    if theme.schema_version != EXPECTED_VERSION {
        return Err(ValidationError::InvalidSchemaVersion {
            expected: EXPECTED_VERSION.to_string(),
            actual: theme.schema_version.clone(),
        });
    }
    
    // Validate metadata fields are non-empty
    if theme.name.trim().is_empty() {
        return Err(ValidationError::MissingField("name".to_string()));
    }
    
    if theme.description.trim().is_empty() {
        return Err(ValidationError::MissingField("description".to_string()));
    }
    
    if theme.author.trim().is_empty() {
        return Err(ValidationError::MissingField("author".to_string()));
    }
    
    // Validate all color fields using hex color validator
    // Helper function to validate a color and provide context
    let validate_color = |field_name: &str, color: &str| -> Result<(), ValidationError> {
        validate_hex_color(color).map_err(|e| {
            ValidationError::InvalidColor(format!("{}: {} ({})", field_name, color, e))
        })
    };
    
    // Validate background and foreground
    validate_color("background", &theme.colors.background)?;
    validate_color("foreground", &theme.colors.foreground)?;
    
    // Validate standard ANSI colors
    validate_color("black", &theme.colors.black)?;
    validate_color("red", &theme.colors.red)?;
    validate_color("green", &theme.colors.green)?;
    validate_color("yellow", &theme.colors.yellow)?;
    validate_color("blue", &theme.colors.blue)?;
    validate_color("magenta", &theme.colors.magenta)?;
    validate_color("cyan", &theme.colors.cyan)?;
    validate_color("white", &theme.colors.white)?;
    
    // Validate bright ANSI colors
    validate_color("bright_black", &theme.colors.bright_black)?;
    validate_color("bright_red", &theme.colors.bright_red)?;
    validate_color("bright_green", &theme.colors.bright_green)?;
    validate_color("bright_yellow", &theme.colors.bright_yellow)?;
    validate_color("bright_blue", &theme.colors.bright_blue)?;
    validate_color("bright_magenta", &theme.colors.bright_magenta)?;
    validate_color("bright_cyan", &theme.colors.bright_cyan)?;
    validate_color("bright_white", &theme.colors.bright_white)?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_hex_colors() {
        // Standard uppercase
        assert!(validate_hex_color("#FF0000").is_ok());
        assert!(validate_hex_color("#00FF00").is_ok());
        assert!(validate_hex_color("#0000FF").is_ok());
        
        // Lowercase
        assert!(validate_hex_color("#ff0000").is_ok());
        assert!(validate_hex_color("#00ff00").is_ok());
        assert!(validate_hex_color("#0000ff").is_ok());
        
        // Mixed case
        assert!(validate_hex_color("#FfAa00").is_ok());
        
        // White and black
        assert!(validate_hex_color("#FFFFFF").is_ok());
        assert!(validate_hex_color("#000000").is_ok());
        
        // Various valid colors
        assert!(validate_hex_color("#282a36").is_ok());
        assert!(validate_hex_color("#BD93F9").is_ok());
    }

    #[test]
    fn test_missing_hash() {
        let result = validate_hex_color("FF0000");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), ValidationError::MissingHash));
        
        let result = validate_hex_color("00FF00");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), ValidationError::MissingHash));
    }

    #[test]
    fn test_invalid_length() {
        // Too short
        assert!(matches!(
            validate_hex_color("#FF"),
            Err(ValidationError::InvalidLength)
        ));
        assert!(matches!(
            validate_hex_color("#FF00"),
            Err(ValidationError::InvalidLength)
        ));
        assert!(matches!(
            validate_hex_color("#FF0000F"),
            Err(ValidationError::InvalidLength)
        ));
        
        // Too long
        assert!(matches!(
            validate_hex_color("#FF0000FF"),
            Err(ValidationError::InvalidLength)
        ));
        
        // Empty after hash
        assert!(matches!(
            validate_hex_color("#"),
            Err(ValidationError::InvalidLength)
        ));
    }

    #[test]
    fn test_invalid_hex_characters() {
        // Invalid characters
        assert!(matches!(
            validate_hex_color("#GGGGGG"),
            Err(ValidationError::InvalidHexCharacter)
        ));
        assert!(matches!(
            validate_hex_color("#FF00GG"),
            Err(ValidationError::InvalidHexCharacter)
        ));
        assert!(matches!(
            validate_hex_color("#ZZZZZZ"),
            Err(ValidationError::InvalidHexCharacter)
        ));
        
        // Special characters
        assert!(matches!(
            validate_hex_color("#FF-000"),
            Err(ValidationError::InvalidHexCharacter)
        ));
        assert!(matches!(
            validate_hex_color("#FF 000"),
            Err(ValidationError::InvalidHexCharacter)
        ));
    }

    #[test]
    fn test_edge_cases() {
        // Empty string
        assert!(matches!(
            validate_hex_color(""),
            Err(ValidationError::InvalidLength)
        ));
        
        // Only hash
        assert!(matches!(
            validate_hex_color("#"),
            Err(ValidationError::InvalidLength)
        ));
        
        // Hash in wrong position
        assert!(matches!(
            validate_hex_color("FF#0000"),
            Err(ValidationError::MissingHash)
        ));
    }

    // Helper function to create a valid test theme
    fn create_valid_theme() -> Theme {
        Theme {
            schema_version: "1.0".to_string(),
            name: "Test Theme".to_string(),
            description: "A test theme for validation".to_string(),
            author: "Test Author".to_string(),
            palette_type: PaletteType::Dark,
            colors: ColorScheme {
                background: "#000000".to_string(),
                foreground: "#FFFFFF".to_string(),
                black: "#000000".to_string(),
                red: "#FF0000".to_string(),
                green: "#00FF00".to_string(),
                yellow: "#FFFF00".to_string(),
                blue: "#0000FF".to_string(),
                magenta: "#FF00FF".to_string(),
                cyan: "#00FFFF".to_string(),
                white: "#FFFFFF".to_string(),
                bright_black: "#808080".to_string(),
                bright_red: "#FF8080".to_string(),
                bright_green: "#80FF80".to_string(),
                bright_yellow: "#FFFF80".to_string(),
                bright_blue: "#8080FF".to_string(),
                bright_magenta: "#FF80FF".to_string(),
                bright_cyan: "#80FFFF".to_string(),
                bright_white: "#FFFFFF".to_string(),
            },
        }
    }

    #[test]
    fn test_validate_theme_valid() {
        let theme = create_valid_theme();
        assert!(validate_theme(&theme).is_ok());
    }

    #[test]
    fn test_validate_theme_invalid_schema_version() {
        let mut theme = create_valid_theme();
        theme.schema_version = "2.0".to_string();
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::InvalidSchemaVersion { expected, actual } => {
                assert_eq!(expected, "1.0");
                assert_eq!(actual, "2.0");
            }
            _ => panic!("Expected InvalidSchemaVersion error"),
        }
    }

    #[test]
    fn test_validate_theme_empty_name() {
        let mut theme = create_valid_theme();
        theme.name = "".to_string();
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::MissingField(field) => {
                assert_eq!(field, "name");
            }
            _ => panic!("Expected MissingField error"),
        }
    }

    #[test]
    fn test_validate_theme_empty_description() {
        let mut theme = create_valid_theme();
        theme.description = "   ".to_string(); // Whitespace only
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::MissingField(field) => {
                assert_eq!(field, "description");
            }
            _ => panic!("Expected MissingField error"),
        }
    }

    #[test]
    fn test_validate_theme_empty_author() {
        let mut theme = create_valid_theme();
        theme.author = "".to_string();
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::MissingField(field) => {
                assert_eq!(field, "author");
            }
            _ => panic!("Expected MissingField error"),
        }
    }

    #[test]
    fn test_validate_theme_invalid_background_color() {
        let mut theme = create_valid_theme();
        theme.colors.background = "000000".to_string(); // Missing #
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::InvalidColor(msg) => {
                assert!(msg.contains("background"));
                assert!(msg.contains("000000"));
            }
            _ => panic!("Expected InvalidColor error"),
        }
    }

    #[test]
    fn test_validate_theme_invalid_foreground_color() {
        let mut theme = create_valid_theme();
        theme.colors.foreground = "#GGGGGG".to_string(); // Invalid hex
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::InvalidColor(msg) => {
                assert!(msg.contains("foreground"));
                assert!(msg.contains("#GGGGGG"));
            }
            _ => panic!("Expected InvalidColor error"),
        }
    }

    #[test]
    fn test_validate_theme_invalid_ansi_color() {
        let mut theme = create_valid_theme();
        theme.colors.red = "#FF00".to_string(); // Too short
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::InvalidColor(msg) => {
                assert!(msg.contains("red"));
                assert!(msg.contains("#FF00"));
            }
            _ => panic!("Expected InvalidColor error"),
        }
    }

    #[test]
    fn test_validate_theme_invalid_bright_color() {
        let mut theme = create_valid_theme();
        theme.colors.bright_blue = "#0000FF00".to_string(); // Too long
        
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::InvalidColor(msg) => {
                assert!(msg.contains("bright_blue"));
                assert!(msg.contains("#0000FF00"));
            }
            _ => panic!("Expected InvalidColor error"),
        }
    }

    #[test]
    fn test_validate_theme_multiple_invalid_fields() {
        let mut theme = create_valid_theme();
        theme.name = "".to_string();
        theme.colors.red = "invalid".to_string();
        
        // Should fail on the first validation error (empty name)
        let result = validate_theme(&theme);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::MissingField(field) => {
                assert_eq!(field, "name");
            }
            _ => panic!("Expected MissingField error"),
        }
    }

    #[test]
    fn test_validate_theme_with_lowercase_hex() {
        let mut theme = create_valid_theme();
        theme.colors.red = "#ff0000".to_string(); // Lowercase should be valid
        theme.colors.green = "#00Ff00".to_string(); // Mixed case should be valid
        
        assert!(validate_theme(&theme).is_ok());
    }

    #[test]
    fn test_validate_dracula_theme_structure() {
        // Test with a theme that matches the actual Dracula.json structure
        let theme = Theme {
            schema_version: "1.0".to_string(),
            name: "Dracula".to_string(),
            description: "A dark theme with purple and pink accents, designed for high contrast".to_string(),
            author: "Dracula Theme".to_string(),
            palette_type: PaletteType::Dark,
            colors: ColorScheme {
                background: "#282a36".to_string(),
                foreground: "#f8f8f2".to_string(),
                black: "#21222c".to_string(),
                red: "#ff5555".to_string(),
                green: "#50fa7b".to_string(),
                yellow: "#f1fa8c".to_string(),
                blue: "#bd93f9".to_string(),
                magenta: "#ff79c6".to_string(),
                cyan: "#8be9fd".to_string(),
                white: "#f8f8f2".to_string(),
                bright_black: "#6272a4".to_string(),
                bright_red: "#ff6e6e".to_string(),
                bright_green: "#69ff94".to_string(),
                bright_yellow: "#ffffa5".to_string(),
                bright_blue: "#d6acff".to_string(),
                bright_magenta: "#ff92df".to_string(),
                bright_cyan: "#a4ffff".to_string(),
                bright_white: "#ffffff".to_string(),
            },
        };
        
        assert!(validate_theme(&theme).is_ok());
    }
}
