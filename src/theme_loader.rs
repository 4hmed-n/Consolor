// Theme loading, parsing, and validation logic

use crate::theme::Theme;
use std::collections::HashMap;
use std::path::PathBuf;
use thiserror::Error;

/// Manages loading themes from embedded resources and filesystem
pub struct ThemeLoader {
    embedded_themes: HashMap<String, Theme>,
    user_themes: HashMap<String, Theme>,
}

impl ThemeLoader {
    /// Creates a new theme loader instance and loads all embedded themes
    /// 
    /// This method loads themes embedded at compile time using include_str! macro.
    /// Invalid themes are skipped with warnings logged to stderr.
    /// 
    /// # Returns
    /// * `Ok(Self)` with all valid embedded themes loaded
    /// * `Err(ThemeError)` if there's a critical loading error
    /// 
    /// # Embedded Themes
    /// The following themes are embedded at compile time:
    /// - Dracula, SolarizedDark, SolarizedLight, Monokai, Nord
    /// - OneDark, OneLight, GruvboxDark, TokyoNight, GithubLight
    pub fn new() -> Result<Self, ThemeError> {
        let mut loader = Self {
            embedded_themes: HashMap::new(),
            user_themes: HashMap::new(),
        };
        
        // Load all embedded themes using include_str! macro
        // Each theme is compiled into the binary at build time
        loader.load_embedded_theme("Dracula", include_str!("themes/Dracula.json"));
        loader.load_embedded_theme("SolarizedDark", include_str!("themes/SolarizedDark.json"));
        loader.load_embedded_theme("SolarizedLight", include_str!("themes/SolarizedLight.json"));
        loader.load_embedded_theme("Monokai", include_str!("themes/Monokai.json"));
        loader.load_embedded_theme("Nord", include_str!("themes/Nord.json"));
        loader.load_embedded_theme("OneDark", include_str!("themes/OneDark.json"));
        loader.load_embedded_theme("OneLight", include_str!("themes/OneLight.json"));
        loader.load_embedded_theme("GruvboxDark", include_str!("themes/GruvboxDark.json"));
        loader.load_embedded_theme("TokyoNight", include_str!("themes/TokyoNight.json"));
        loader.load_embedded_theme("GithubLight", include_str!("themes/GithubLight.json"));
        
        Ok(loader)
    }
    
    /// Loads and validates a single embedded theme from JSON string
    /// 
    /// # Arguments
    /// * `name` - The theme identifier (for error reporting)
    /// * `json_content` - The JSON string content of the theme
    /// 
    /// # Behavior
    /// * On success: theme is added to embedded_themes HashMap
    /// * On parse error: logs warning to stderr and skips the theme
    /// * On validation error: logs warning to stderr and skips the theme
    fn load_embedded_theme(&mut self, name: &str, json_content: &str) {
        match serde_json::from_str::<Theme>(json_content) {
            Ok(theme) => {
                // Validate the theme structure
                if let Err(e) = crate::theme::validate_theme(&theme) {
                    eprintln!("Warning: Skipping invalid embedded theme '{}': {}", name, e);
                    return;
                }
                
                // Store in HashMap keyed by theme name
                self.embedded_themes.insert(theme.name.clone(), theme);
            }
            Err(e) => {
                eprintln!("Warning: Failed to parse embedded theme '{}': {}", name, e);
            }
        }
    }

    /// Loads all themes from user directory
    /// 
    /// Scans the user themes directory (%LOCALAPPDATA%\cmd-theme-pack\themes\)
    /// for .json files and attempts to parse them as themes.
    /// 
    /// # Behavior
    /// * Creates the user themes directory if it doesn't exist
    /// * Scans for all .json files in the directory
    /// * Validates each theme on load
    /// * Invalid themes are skipped with warnings logged to stderr
    /// * User themes are stored in user_themes HashMap
    /// 
    /// # Returns
    /// * `Ok(())` if the loading process completes (even if some themes failed)
    /// * `Err(ThemeError)` if there's a critical I/O error accessing the directory
    pub fn load_all_themes(&mut self) -> Result<(), ThemeError> {
        // Get user themes directory path
        let user_themes_dir = self.get_user_themes_directory()?;
        
        // Create directory if it doesn't exist
        if !user_themes_dir.exists() {
            std::fs::create_dir_all(&user_themes_dir)?;
        }
        
        // Scan for .json files in the directory
        if user_themes_dir.is_dir() {
            match std::fs::read_dir(&user_themes_dir) {
                Ok(entries) => {
                    for entry in entries {
                        if let Ok(entry) = entry {
                            let path = entry.path();
                            
                            // Only process .json files
                            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("json") {
                                self.load_user_theme_from_file(&path);
                            }
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Warning: Failed to read user themes directory: {}", e);
                }
            }
        }
        
        Ok(())
    }
    
    /// Gets the user themes directory path
    /// 
    /// # Returns
    /// * `Ok(PathBuf)` containing the path to %LOCALAPPDATA%\cmd-theme-pack\themes\
    /// * `Err(ThemeError)` if LOCALAPPDATA cannot be determined
    fn get_user_themes_directory(&self) -> Result<PathBuf, ThemeError> {
        // Get LOCALAPPDATA directory
        let local_app_data = std::env::var("LOCALAPPDATA")
            .map_err(|_| ThemeError::InvalidFormat(
                "Could not determine LOCALAPPDATA directory".to_string()
            ))?;
        
        // Build path: %LOCALAPPDATA%\cmd-theme-pack\themes\
        let mut path = PathBuf::from(local_app_data);
        path.push("cmd-theme-pack");
        path.push("themes");
        
        Ok(path)
    }
    
    /// Loads and validates a single user theme from a file
    /// 
    /// # Arguments
    /// * `path` - Path to the .json theme file
    /// 
    /// # Behavior
    /// * Reads the file contents
    /// * Parses JSON into Theme structure
    /// * Validates the theme
    /// * On success: adds theme to user_themes HashMap
    /// * On failure: logs warning to stderr and skips the theme
    fn load_user_theme_from_file(&mut self, path: &PathBuf) {
        let file_name = path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");
        
        // Read file contents
        let json_content = match std::fs::read_to_string(path) {
            Ok(content) => content,
            Err(e) => {
                eprintln!("Warning: Failed to read user theme file '{}': {}", file_name, e);
                return;
            }
        };
        
        // Parse JSON
        match serde_json::from_str::<Theme>(&json_content) {
            Ok(theme) => {
                // Validate the theme structure
                if let Err(e) = crate::theme::validate_theme(&theme) {
                    eprintln!("Warning: Skipping invalid user theme '{}': {}", file_name, e);
                    return;
                }
                
                // Store in user_themes HashMap keyed by theme name
                self.user_themes.insert(theme.name.clone(), theme);
            }
            Err(e) => {
                eprintln!("Warning: Failed to parse user theme file '{}': {}", file_name, e);
            }
        }
    }

    /// Retrieves a theme by name
    pub fn get_theme(&self, name: &str) -> Option<&Theme> {
        // User themes override embedded themes
        self.user_themes.get(name).or_else(|| self.embedded_themes.get(name))
    }

    /// Returns a list of all available themes
    /// 
    /// User themes with the same name as embedded themes will override them.
    /// The returned list contains no duplicates.
    /// 
    /// # Returns
    /// A vector of theme references containing:
    /// - All user themes (these take priority)
    /// - All embedded themes not overridden by user themes
    pub fn list_themes(&self) -> Vec<&Theme> {
        use std::collections::HashSet;
        
        let mut themes: Vec<&Theme> = Vec::new();
        let mut seen_names: HashSet<&str> = HashSet::new();
        
        // First, add all user themes (these have priority)
        for theme in self.user_themes.values() {
            themes.push(theme);
            seen_names.insert(&theme.name);
        }
        
        // Then, add embedded themes that weren't overridden by user themes
        for theme in self.embedded_themes.values() {
            if !seen_names.contains(theme.name.as_str()) {
                themes.push(theme);
            }
        }
        
        themes
    }

    /// Validates a theme structure
    pub fn validate_theme(&self, theme: &Theme) -> Result<(), ValidationError> {
        crate::theme::validate_theme(theme)
    }
}

/// Errors that can occur during theme operations
#[derive(Debug, Error)]
pub enum ThemeError {
    #[error("Theme not found: {0}")]
    NotFound(String),
    
    #[error("Invalid theme file: {0}")]
    InvalidFormat(String),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
}

/// Validation errors for theme structure
#[derive(Debug, Error)]
pub enum ValidationError {
    #[error("Missing required field: {0}")]
    MissingField(String),
    
    #[error("Invalid color format: {0}")]
    InvalidColor(String),
    
    #[error("Invalid schema version: expected {expected}, got {actual}")]
    InvalidSchemaVersion { expected: String, actual: String },
    
    #[error("Color must start with '#' character")]
    MissingHash,
    
    #[error("Color must be exactly 7 characters (#RRGGBB)")]
    InvalidLength,
    
    #[error("Color contains invalid hexadecimal character")]
    InvalidHexCharacter,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_theme_loader_new() {
        // Create a new theme loader
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Should have embedded themes loaded
        assert!(!loader.embedded_themes.is_empty(), "Embedded themes should be loaded");
        
        // Should have no user themes initially
        assert!(loader.user_themes.is_empty(), "User themes should be empty initially");
    }

    #[test]
    fn test_embedded_themes_count() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Should have exactly 10 embedded themes
        assert_eq!(
            loader.embedded_themes.len(),
            10,
            "Should have 10 embedded themes, found {}",
            loader.embedded_themes.len()
        );
    }

    #[test]
    fn test_embedded_themes_names() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Expected theme names
        let expected_themes = vec![
            "Dracula",
            "SolarizedDark",
            "SolarizedLight",
            "Monokai",
            "Nord",
            "OneDark",
            "OneLight",
            "GruvboxDark",
            "TokyoNight",
            "GithubLight",
        ];
        
        // Check each expected theme exists
        for theme_name in expected_themes {
            assert!(
                loader.embedded_themes.contains_key(theme_name),
                "Theme '{}' should be loaded",
                theme_name
            );
        }
    }

    #[test]
    fn test_get_theme_embedded() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Should retrieve Dracula theme
        let theme = loader.get_theme("Dracula");
        assert!(theme.is_some(), "Dracula theme should be found");
        
        let theme = theme.unwrap();
        assert_eq!(theme.name, "Dracula");
        assert_eq!(theme.schema_version, "1.0");
        assert!(!theme.description.is_empty());
        assert!(!theme.author.is_empty());
    }

    #[test]
    fn test_get_theme_not_found() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Should return None for non-existent theme
        let theme = loader.get_theme("NonExistentTheme");
        assert!(theme.is_none(), "Non-existent theme should return None");
    }

    #[test]
    fn test_embedded_themes_valid_structure() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // All embedded themes should be valid (already validated during load)
        for (name, theme) in &loader.embedded_themes {
            assert_eq!(
                &theme.name, name,
                "Theme name '{}' should match HashMap key '{}'",
                theme.name, name
            );
            
            // Validate theme structure
            let validation_result = crate::theme::validate_theme(theme);
            assert!(
                validation_result.is_ok(),
                "Embedded theme '{}' should be valid: {:?}",
                name,
                validation_result.err()
            );
        }
    }

    #[test]
    fn test_embedded_themes_all_colors_valid() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Check that all themes have valid color values
        for (name, theme) in &loader.embedded_themes {
            // Validate background and foreground
            assert!(
                crate::theme::validate_hex_color(&theme.colors.background).is_ok(),
                "Theme '{}' has invalid background color: {}",
                name,
                theme.colors.background
            );
            assert!(
                crate::theme::validate_hex_color(&theme.colors.foreground).is_ok(),
                "Theme '{}' has invalid foreground color: {}",
                name,
                theme.colors.foreground
            );
            
            // Validate all 16 ANSI colors
            let colors = vec![
                &theme.colors.black,
                &theme.colors.red,
                &theme.colors.green,
                &theme.colors.yellow,
                &theme.colors.blue,
                &theme.colors.magenta,
                &theme.colors.cyan,
                &theme.colors.white,
                &theme.colors.bright_black,
                &theme.colors.bright_red,
                &theme.colors.bright_green,
                &theme.colors.bright_yellow,
                &theme.colors.bright_blue,
                &theme.colors.bright_magenta,
                &theme.colors.bright_cyan,
                &theme.colors.bright_white,
            ];
            
            for color in colors {
                assert!(
                    crate::theme::validate_hex_color(color).is_ok(),
                    "Theme '{}' has invalid color: {}",
                    name,
                    color
                );
            }
        }
    }

    #[test]
    fn test_list_themes_embedded_only() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        let themes = loader.list_themes();
        
        // Should have all embedded themes
        assert_eq!(themes.len(), 10, "Should list 10 themes");
        
        // All themes should be present
        let theme_names: Vec<String> = themes.iter().map(|t| t.name.clone()).collect();
        assert!(theme_names.contains(&"Dracula".to_string()));
        assert!(theme_names.contains(&"Nord".to_string()));
        assert!(theme_names.contains(&"TokyoNight".to_string()));
    }

    #[test]
    fn test_dracula_theme_details() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        let theme = loader.get_theme("Dracula").expect("Dracula theme should exist");
        
        // Verify Dracula theme specific details
        assert_eq!(theme.name, "Dracula");
        assert_eq!(theme.schema_version, "1.0");
        assert_eq!(theme.colors.background, "#282a36");
        assert_eq!(theme.colors.foreground, "#f8f8f2");
        assert_eq!(theme.colors.red, "#ff5555");
        assert_eq!(theme.colors.blue, "#bd93f9");
        
        // Verify it's a dark theme
        match theme.palette_type {
            crate::theme::PaletteType::Dark => (),
            _ => panic!("Dracula should be a Dark theme"),
        }
    }

    #[test]
    fn test_validate_theme_method() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        let theme = loader.get_theme("Nord").expect("Nord theme should exist");
        
        // Should validate successfully
        let result = loader.validate_theme(theme);
        assert!(result.is_ok(), "Nord theme should validate: {:?}", result.err());
    }

    #[test]
    fn test_get_user_themes_directory() {
        let loader = ThemeLoader::new().expect("Failed to create theme loader");
        let result = loader.get_user_themes_directory();
        
        assert!(result.is_ok(), "Should successfully get user themes directory");
        
        let path = result.unwrap();
        let path_str = path.to_string_lossy();
        
        // Should contain the expected path components
        assert!(path_str.contains("cmd-theme-pack"), "Path should contain 'cmd-theme-pack'");
        assert!(path_str.contains("themes"), "Path should contain 'themes'");
    }

    #[test]
    fn test_load_all_themes_creates_directory() {
        let mut loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Call load_all_themes - should create directory if it doesn't exist
        let result = loader.load_all_themes();
        
        // Should succeed even if directory doesn't exist initially
        assert!(result.is_ok(), "load_all_themes should succeed: {:?}", result.err());
        
        // Verify directory was created
        let user_dir = loader.get_user_themes_directory().unwrap();
        assert!(user_dir.exists(), "User themes directory should exist after load_all_themes");
        assert!(user_dir.is_dir(), "User themes path should be a directory");
    }

    #[test]
    fn test_user_theme_override() {
        let mut loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Get an embedded theme
        let embedded_theme = loader.get_theme("Dracula").expect("Dracula should exist");
        assert_eq!(embedded_theme.name, "Dracula");
        
        // Create a mock user theme with the same name
        let user_theme = crate::theme::Theme {
            schema_version: "1.0".to_string(),
            name: "Dracula".to_string(),
            description: "User's custom Dracula theme".to_string(),
            author: "Custom Author".to_string(),
            palette_type: crate::theme::PaletteType::Dark,
            colors: crate::theme::ColorScheme {
                background: "#111111".to_string(),
                foreground: "#EEEEEE".to_string(),
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
        };
        
        // Manually add user theme to simulate loading from file
        loader.user_themes.insert(user_theme.name.clone(), user_theme.clone());
        
        // get_theme should return the user version, not the embedded one
        let retrieved = loader.get_theme("Dracula").expect("Dracula should exist");
        assert_eq!(retrieved.description, "User's custom Dracula theme");
        assert_eq!(retrieved.author, "Custom Author");
        assert_eq!(retrieved.colors.background, "#111111");
    }

    #[test]
    fn test_list_themes_user_override() {
        let mut loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Initially should have 10 embedded themes
        let initial_themes = loader.list_themes();
        assert_eq!(initial_themes.len(), 10, "Should start with 10 embedded themes");
        
        // Add a user theme with same name as embedded (Dracula)
        let user_dracula = crate::theme::Theme {
            schema_version: "1.0".to_string(),
            name: "Dracula".to_string(),
            description: "User's custom Dracula".to_string(),
            author: "User".to_string(),
            palette_type: crate::theme::PaletteType::Dark,
            colors: crate::theme::ColorScheme {
                background: "#111111".to_string(),
                foreground: "#EEEEEE".to_string(),
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
        };
        loader.user_themes.insert("Dracula".to_string(), user_dracula);
        
        // Add a completely new user theme
        let user_custom = crate::theme::Theme {
            schema_version: "1.0".to_string(),
            name: "CustomTheme".to_string(),
            description: "A custom user theme".to_string(),
            author: "User".to_string(),
            palette_type: crate::theme::PaletteType::Light,
            colors: crate::theme::ColorScheme {
                background: "#FFFFFF".to_string(),
                foreground: "#000000".to_string(),
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
        };
        loader.user_themes.insert("CustomTheme".to_string(), user_custom);
        
        // Now list themes
        let themes = loader.list_themes();
        
        // Should have 11 themes total (10 embedded - 1 overridden + 1 new + 1 user override)
        // = 10 embedded + 1 new user theme = 11 total
        assert_eq!(themes.len(), 11, "Should have 11 themes (10 embedded + 1 new user)");
        
        // Find Dracula in the list
        let dracula = themes.iter().find(|t| t.name == "Dracula").expect("Dracula should be in list");
        assert_eq!(dracula.description, "User's custom Dracula", "Dracula should be the user version");
        assert_eq!(dracula.author, "User", "Dracula should have user author");
        
        // Find CustomTheme in the list
        let custom = themes.iter().find(|t| t.name == "CustomTheme").expect("CustomTheme should be in list");
        assert_eq!(custom.description, "A custom user theme");
        
        // Verify no duplicate Dracula entries
        let dracula_count = themes.iter().filter(|t| t.name == "Dracula").count();
        assert_eq!(dracula_count, 1, "Should only have one Dracula theme in the list");
    }

    #[test]
    fn test_list_themes_multiple_user_overrides() {
        let mut loader = ThemeLoader::new().expect("Failed to create theme loader");
        
        // Override multiple embedded themes
        let themes_to_override = vec!["Dracula", "Nord", "Monokai"];
        
        for theme_name in &themes_to_override {
            let user_theme = crate::theme::Theme {
                schema_version: "1.0".to_string(),
                name: theme_name.to_string(),
                description: format!("User's {}", theme_name),
                author: "User".to_string(),
                palette_type: crate::theme::PaletteType::Dark,
                colors: crate::theme::ColorScheme {
                    background: "#111111".to_string(),
                    foreground: "#EEEEEE".to_string(),
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
            };
            loader.user_themes.insert(theme_name.to_string(), user_theme);
        }
        
        let themes = loader.list_themes();
        
        // Should still have 10 themes (no new ones, just overrides)
        assert_eq!(themes.len(), 10, "Should still have 10 themes");
        
        // Verify each overridden theme is the user version
        for theme_name in &themes_to_override {
            let theme = themes.iter().find(|t| t.name == *theme_name)
                .expect(&format!("{} should be in list", theme_name));
            assert_eq!(theme.author, "User", "{} should be user version", theme_name);
            assert_eq!(theme.description, format!("User's {}", theme_name));
            
            // Verify no duplicates
            let count = themes.iter().filter(|t| t.name == *theme_name).count();
            assert_eq!(count, 1, "Should only have one {} in the list", theme_name);
        }
    }
}
