// Windows Terminal settings.json handler

use crate::theme::Theme;
use std::path::PathBuf;
use thiserror::Error;

/// Handles reading and modifying Windows Terminal settings.json
pub struct WindowsTerminalHandler {
    settings_path: PathBuf,
}

impl WindowsTerminalHandler {
    /// Creates a new Windows Terminal handler for the given settings path
    pub fn new(settings_path: PathBuf) -> Self {
        Self { settings_path }
    }

    /// Applies a theme to Windows Terminal by modifying settings.json
    pub fn apply_theme(&self, theme: &Theme) -> Result<(), ApplyError> {
        // Read current settings
        let mut settings = self.read_settings()?;
        
        // Add or update the color scheme
        self.add_or_update_scheme(&mut settings, theme);
        
        // Write back to file
        self.write_settings(settings)?;
        
        Ok(())
    }

    /// Gets the currently active color scheme name
    pub fn get_current_scheme(&self) -> Result<Option<String>, ReadError> {
        // Read current settings
        let settings = self.read_settings()?;
        
        // Navigate to defaults.colorScheme
        let scheme_name = settings
            .get("profiles")
            .and_then(|profiles| profiles.get("defaults"))
            .and_then(|defaults| defaults.get("colorScheme"))
            .and_then(|scheme| scheme.as_str())
            .map(|s| s.to_string());
        
        Ok(scheme_name)
    }

    /// Reads the Windows Terminal settings.json file
    fn read_settings(&self) -> Result<serde_json::Value, ReadError> {
        use std::fs;
        
        // Read the settings.json file
        let contents = fs::read_to_string(&self.settings_path)?;
        
        // Parse JSON while preserving structure
        let settings: serde_json::Value = serde_json::from_str(&contents)?;
        
        Ok(settings)
    }

    /// Writes the modified settings back to settings.json
    fn write_settings(&self, settings: serde_json::Value) -> Result<(), WriteError> {
        use std::fs;
        
        // Serialize with pretty printing (4-space indentation)
        let contents = serde_json::to_string_pretty(&settings)?;
        
        // Write to file
        fs::write(&self.settings_path, contents).map_err(|e| {
            if e.kind() == std::io::ErrorKind::PermissionDenied {
                WriteError::PermissionDenied
            } else {
                WriteError::Io(e)
            }
        })?;
        
        Ok(())
    }

    /// Adds or updates a color scheme in the settings
    fn add_or_update_scheme(&self, settings: &mut serde_json::Value, theme: &Theme) {
        use serde_json::json;
        
        // Create the Windows Terminal color scheme from our theme
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
        
        // Ensure the "schemes" array exists
        if !settings.get("schemes").is_some() {
            settings["schemes"] = json!([]);
        }
        
        // Get mutable reference to schemes array
        if let Some(schemes) = settings.get_mut("schemes").and_then(|s| s.as_array_mut()) {
            // Look for existing scheme with same name
            if let Some(existing_index) = schemes.iter().position(|s| {
                s.get("name")
                    .and_then(|n| n.as_str())
                    .map(|n| n == theme.name)
                    .unwrap_or(false)
            }) {
                // Update existing scheme
                schemes[existing_index] = scheme;
            } else {
                // Add new scheme
                schemes.push(scheme);
            }
        }
    }
}

/// Errors that can occur when applying themes
#[derive(Debug, Error)]
pub enum ApplyError {
    #[error("Failed to read settings: {0}")]
    Read(#[from] ReadError),
    
    #[error("Failed to write settings: {0}")]
    Write(#[from] WriteError),
}

/// Errors that can occur when reading settings
#[derive(Debug, Error)]
pub enum ReadError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
}

/// Errors that can occur when writing settings
#[derive(Debug, Error)]
pub enum WriteError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("JSON serialization error: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("Permission denied")]
    PermissionDenied,
}
