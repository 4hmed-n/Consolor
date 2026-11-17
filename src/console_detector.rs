// Console type detection (Windows Terminal vs Legacy Console)

use std::path::PathBuf;

/// Represents the type of console environment detected
#[derive(Debug, Clone)]
pub enum ConsoleType {
    WindowsTerminal { settings_path: PathBuf },
    LegacyConsole,
    Unknown,
}

/// Detects which console system is in use
pub struct ConsoleDetector;

impl ConsoleDetector {
    /// Detects the console type by checking for Windows Terminal installation
    pub fn detect() -> ConsoleType {
        if let Some(settings_path) = Self::get_windows_terminal_settings_path() {
            ConsoleType::WindowsTerminal { settings_path }
        } else {
            ConsoleType::LegacyConsole
        }
    }

    /// Checks if Windows Terminal is installed and returns settings.json path
    fn get_windows_terminal_settings_path() -> Option<PathBuf> {
        // Check standard Windows Terminal locations
        if let Some(local_app_data) = dirs::data_local_dir() {
            // Packaged version
            let packaged_path = local_app_data
                .join("Packages")
                .join("Microsoft.WindowsTerminal_8wekyb3d8bbwe")
                .join("LocalState")
                .join("settings.json");
            
            if packaged_path.exists() {
                return Some(packaged_path);
            }
            
            // Unpackaged version
            let unpackaged_path = local_app_data
                .join("Microsoft")
                .join("Windows Terminal")
                .join("settings.json");
            
            if unpackaged_path.exists() {
                return Some(unpackaged_path);
            }
        }
        
        None
    }
}
