// Test for Task 8.3: Verify get_current_scheme() implementation
// This test verifies the WindowsTerminalHandler can correctly read the current scheme

use std::fs;
use std::path::PathBuf;
use serde_json::json;

// Minimal implementations needed for testing
mod theme {
    use serde::{Deserialize, Serialize};

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Theme {
        pub schema_version: String,
        pub name: String,
        pub description: String,
        pub author: String,
        pub palette_type: PaletteType,
        pub colors: ColorScheme,
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum PaletteType {
        Dark,
        Light,
    }

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
}

mod wt_handler {
    use crate::theme::Theme;
    use std::path::PathBuf;
    use thiserror::Error;

    pub struct WindowsTerminalHandler {
        settings_path: PathBuf,
    }

    impl WindowsTerminalHandler {
        pub fn new(settings_path: PathBuf) -> Self {
            Self { settings_path }
        }

        pub fn apply_theme(&self, theme: &Theme) -> Result<(), ApplyError> {
            let mut settings = self.read_settings()?;
            self.add_or_update_scheme(&mut settings, theme);
            self.write_settings(settings)?;
            Ok(())
        }

        pub fn get_current_scheme(&self) -> Result<Option<String>, ReadError> {
            let settings = self.read_settings()?;
            
            let scheme_name = settings
                .get("profiles")
                .and_then(|profiles| profiles.get("defaults"))
                .and_then(|defaults| defaults.get("colorScheme"))
                .and_then(|scheme| scheme.as_str())
                .map(|s| s.to_string());
            
            Ok(scheme_name)
        }

        fn read_settings(&self) -> Result<serde_json::Value, ReadError> {
            use std::fs;
            let contents = fs::read_to_string(&self.settings_path)?;
            let settings: serde_json::Value = serde_json::from_str(&contents)?;
            Ok(settings)
        }

        fn write_settings(&self, settings: serde_json::Value) -> Result<(), WriteError> {
            use std::fs;
            let contents = serde_json::to_string_pretty(&settings)?;
            fs::write(&self.settings_path, contents).map_err(|e| {
                if e.kind() == std::io::ErrorKind::PermissionDenied {
                    WriteError::PermissionDenied
                } else {
                    WriteError::Io(e)
                }
            })?;
            Ok(())
        }

        fn add_or_update_scheme(&self, settings: &mut serde_json::Value, theme: &Theme) {
            use serde_json::json;
            
            let scheme = json!({
                "name": theme.name,
                "background": theme.colors.background,
                "foreground": theme.colors.foreground,
                "black": theme.colors.black,
                "red": theme.colors.red,
                "green": theme.colors.green,
                "yellow": theme.colors.yellow,
                "blue": theme.colors.blue,
                "magenta": theme.colors.magenta,
                "cyan": theme.colors.cyan,
                "white": theme.colors.white,
                "brightBlack": theme.colors.bright_black,
                "brightRed": theme.colors.bright_red,
                "brightGreen": theme.colors.bright_green,
                "brightYellow": theme.colors.bright_yellow,
                "brightBlue": theme.colors.bright_blue,
                "brightMagenta": theme.colors.bright_magenta,
                "brightCyan": theme.colors.bright_cyan,
                "brightWhite": theme.colors.bright_white,
            });
            
            if !settings.get("schemes").is_some() {
                settings["schemes"] = json!([]);
            }
            
            if let Some(schemes) = settings.get_mut("schemes").and_then(|s| s.as_array_mut()) {
                if let Some(existing_index) = schemes.iter().position(|s| {
                    s.get("name")
                        .and_then(|n| n.as_str())
                        .map(|n| n == theme.name)
                        .unwrap_or(false)
                }) {
                    schemes[existing_index] = scheme;
                } else {
                    schemes.push(scheme);
                }
            }
        }
    }

    #[derive(Debug, Error)]
    pub enum ApplyError {
        #[error("Failed to read settings: {0}")]
        Read(#[from] ReadError),
        
        #[error("Failed to write settings: {0}")]
        Write(#[from] WriteError),
    }

    #[derive(Debug, Error)]
    pub enum ReadError {
        #[error("IO error: {0}")]
        Io(#[from] std::io::Error),
        
        #[error("JSON parsing error: {0}")]
        Json(#[from] serde_json::Error),
    }

    #[derive(Debug, Error)]
    pub enum WriteError {
        #[error("IO error: {0}")]
        Io(#[from] std::io::Error),
        
        #[error("JSON serialization error: {0}")]
        Json(#[from] serde_json::Error),
        
        #[error("Permission denied")]
        PermissionDenied,
    }
}

fn main() {
    println!("Testing Task 8.3: get_current_scheme() implementation\n");

    // Create a temporary directory for test files
    let temp_dir = std::env::temp_dir().join("cmd_theme_test_8_3");
    fs::create_dir_all(&temp_dir).expect("Failed to create temp dir");

    // Test Case 1: Settings with colorScheme set
    println!("Test 1: Reading current scheme when colorScheme is set");
    let settings_path_1 = temp_dir.join("settings_with_scheme.json");
    let settings_with_scheme = json!({
        "profiles": {
            "defaults": {
                "colorScheme": "Dracula"
            }
        },
        "schemes": []
    });
    fs::write(&settings_path_1, serde_json::to_string_pretty(&settings_with_scheme).unwrap())
        .expect("Failed to write test file");

    let handler_1 = wt_handler::WindowsTerminalHandler::new(settings_path_1.clone());
    match handler_1.get_current_scheme() {
        Ok(Some(scheme)) => {
            println!("✓ Successfully read current scheme: {}", scheme);
            assert_eq!(scheme, "Dracula", "Expected 'Dracula' but got '{}'", scheme);
        }
        Ok(None) => panic!("✗ Expected Some(scheme) but got None"),
        Err(e) => panic!("✗ Error reading scheme: {}", e),
    }

    // Test Case 2: Settings without colorScheme set
    println!("\nTest 2: Reading current scheme when colorScheme is not set");
    let settings_path_2 = temp_dir.join("settings_without_scheme.json");
    let settings_without_scheme = json!({
        "profiles": {
            "defaults": {}
        },
        "schemes": []
    });
    fs::write(&settings_path_2, serde_json::to_string_pretty(&settings_without_scheme).unwrap())
        .expect("Failed to write test file");

    let handler_2 = wt_handler::WindowsTerminalHandler::new(settings_path_2.clone());
    match handler_2.get_current_scheme() {
        Ok(None) => println!("✓ Correctly returned None when colorScheme is not set"),
        Ok(Some(scheme)) => panic!("✗ Expected None but got Some({})", scheme),
        Err(e) => panic!("✗ Error reading scheme: {}", e),
    }

    // Test Case 3: Settings without profiles.defaults section
    println!("\nTest 3: Reading current scheme when profiles.defaults doesn't exist");
    let settings_path_3 = temp_dir.join("settings_no_defaults.json");
    let settings_no_defaults = json!({
        "profiles": {},
        "schemes": []
    });
    fs::write(&settings_path_3, serde_json::to_string_pretty(&settings_no_defaults).unwrap())
        .expect("Failed to write test file");

    let handler_3 = wt_handler::WindowsTerminalHandler::new(settings_path_3.clone());
    match handler_3.get_current_scheme() {
        Ok(None) => println!("✓ Correctly returned None when profiles.defaults doesn't exist"),
        Ok(Some(scheme)) => panic!("✗ Expected None but got Some({})", scheme),
        Err(e) => panic!("✗ Error reading scheme: {}", e),
    }

    // Test Case 4: Settings without profiles section
    println!("\nTest 4: Reading current scheme when profiles section doesn't exist");
    let settings_path_4 = temp_dir.join("settings_no_profiles.json");
    let settings_no_profiles = json!({
        "schemes": []
    });
    fs::write(&settings_path_4, serde_json::to_string_pretty(&settings_no_profiles).unwrap())
        .expect("Failed to write test file");

    let handler_4 = wt_handler::WindowsTerminalHandler::new(settings_path_4.clone());
    match handler_4.get_current_scheme() {
        Ok(None) => println!("✓ Correctly returned None when profiles section doesn't exist"),
        Ok(Some(scheme)) => panic!("✗ Expected None but got Some({})", scheme),
        Err(e) => panic!("✗ Error reading scheme: {}", e),
    }

    // Test Case 5: Different scheme names
    println!("\nTest 5: Reading various scheme names");
    let test_schemes = vec!["One Dark", "Solarized Dark", "Nord", "Tokyo Night"];
    for scheme_name in test_schemes {
        let settings_path = temp_dir.join(format!("settings_{}.json", scheme_name.replace(" ", "_")));
        let settings = json!({
            "profiles": {
                "defaults": {
                    "colorScheme": scheme_name
                }
            },
            "schemes": []
        });
        fs::write(&settings_path, serde_json::to_string_pretty(&settings).unwrap())
            .expect("Failed to write test file");

        let handler = wt_handler::WindowsTerminalHandler::new(settings_path.clone());
        match handler.get_current_scheme() {
            Ok(Some(scheme)) => {
                assert_eq!(scheme, scheme_name, "Expected '{}' but got '{}'", scheme_name, scheme);
                println!("  ✓ Successfully read scheme: {}", scheme);
            }
            Ok(None) => panic!("✗ Expected Some({}) but got None", scheme_name),
            Err(e) => panic!("✗ Error reading scheme {}: {}", scheme_name, e),
        }
    }

    // Cleanup
    fs::remove_dir_all(&temp_dir).ok();

    println!("\n========================================");
    println!("All tests passed! ✓");
    println!("========================================");
    println!("\nget_current_scheme() implementation is correct:");
    println!("  • Reads settings.json correctly");
    println!("  • Navigates to profiles.defaults.colorScheme");
    println!("  • Returns Option<String> with scheme name");
    println!("  • Handles missing sections gracefully (returns None)");
    println!("  • Works with various scheme names");
}
