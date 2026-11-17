// Backup and restore functionality for console settings

use crate::console_detector::ConsoleType;
use crate::registry_handler::RegistryHandler;
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use thiserror::Error;

/// Manages backup and restore operations for console settings
pub struct BackupManager {
    backup_dir: PathBuf,
}

impl BackupManager {
    /// Creates a new backup manager and ensures backup directory exists
    pub fn new() -> Result<Self, BackupError> {
        // Get backup directory location
        let backup_dir = if let Some(local_app_data) = dirs::data_local_dir() {
            local_app_data.join("cmd-theme-pack").join("backups")
        } else {
            return Err(BackupError::NoBackupLocation);
        };

        // Create backup directory if it doesn't exist
        if !backup_dir.exists() {
            fs::create_dir_all(&backup_dir).map_err(|e| {
                BackupError::CreationFailed(format!("Failed to create backup directory: {}", e))
            })?;
        }

        Ok(Self { backup_dir })
    }

    /// Creates a backup of current console settings
    /// Only creates backup if backup file doesn't already exist
    pub fn create_backup(&self, console_type: &ConsoleType) -> Result<(), BackupError> {
        let backup_path = self.get_backup_path(console_type);

        // Only create backup if it doesn't already exist
        if backup_path.exists() {
            return Ok(());
        }

        match console_type {
            ConsoleType::WindowsTerminal { settings_path } => {
                // Copy settings.json to wt_backup.json
                fs::copy(settings_path, &backup_path).map_err(|e| {
                    BackupError::CreationFailed(format!(
                        "Failed to backup Windows Terminal settings: {}",
                        e
                    ))
                })?;
            }
            ConsoleType::LegacyConsole => {
                // Export registry values to console_backup.json
                self.backup_registry_settings(&backup_path)?;
            }
            ConsoleType::Unknown => {
                return Err(BackupError::CreationFailed(
                    "Cannot create backup for unknown console type".to_string(),
                ));
            }
        }

        Ok(())
    }

    /// Restores console settings from backup
    pub fn restore_backup(&self, console_type: &ConsoleType) -> Result<(), RestoreError> {
        let backup_path = self.get_backup_path(console_type);

        // Check if backup exists before attempting restore
        if !self.backup_exists_for_type(console_type) {
            return Err(RestoreError::NoBackup);
        }

        match console_type {
            ConsoleType::WindowsTerminal { settings_path } => {
                // Restore settings.json from wt_backup.json
                fs::copy(&backup_path, settings_path).map_err(|e| {
                    RestoreError::RestoreFailed(format!(
                        "Failed to restore Windows Terminal settings: {}",
                        e
                    ))
                })?;
                
                println!("✓ Windows Terminal settings restored from backup successfully");
            }
            ConsoleType::LegacyConsole => {
                // Restore registry values from console_backup.json
                self.restore_registry_settings(&backup_path)?;
                
                println!("✓ Legacy Console settings restored from backup successfully");
            }
            ConsoleType::Unknown => {
                return Err(RestoreError::RestoreFailed(
                    "Cannot restore backup for unknown console type".to_string(),
                ));
            }
        }

        Ok(())
    }

    /// Checks if a backup exists for the detected console type
    pub fn backup_exists(&self) -> bool {
        // Check if any backup file exists
        self.backup_dir.join("wt_backup.json").exists()
            || self.backup_dir.join("console_backup.json").exists()
    }

    /// Checks if a backup exists for a specific console type
    fn backup_exists_for_type(&self, console_type: &ConsoleType) -> bool {
        self.get_backup_path(console_type).exists()
    }

    /// Gets the backup file path for a given console type
    fn get_backup_path(&self, console_type: &ConsoleType) -> PathBuf {
        match console_type {
            ConsoleType::WindowsTerminal { .. } => self.backup_dir.join("wt_backup.json"),
            ConsoleType::LegacyConsole => self.backup_dir.join("console_backup.json"),
            ConsoleType::Unknown => self.backup_dir.join("unknown_backup.json"),
        }
    }

    /// Backs up current registry settings to a JSON file
    fn backup_registry_settings(&self, backup_path: &PathBuf) -> Result<(), BackupError> {
        let registry_handler = RegistryHandler::new();

        // Read current registry colors
        let console_colors = registry_handler.read_current_colors().map_err(|e| {
            BackupError::CreationFailed(format!("Failed to read registry colors: {}", e))
        })?;

        // Convert color table to hex format for storage
        let mut color_table_hex = Vec::new();
        for colorref in &console_colors.color_table {
            let hex_color = registry_handler.colorref_to_hex(*colorref);
            color_table_hex.push(hex_color);
        }

        // Create backup JSON structure
        let backup_data = json!({
            "color_table": color_table_hex,
            "screen_colors": console_colors.screen_colors,
        });

        // Write backup to file
        let backup_json = serde_json::to_string_pretty(&backup_data).map_err(|e| {
            BackupError::CreationFailed(format!("Failed to serialize backup data: {}", e))
        })?;

        fs::write(backup_path, backup_json).map_err(|e| {
            BackupError::CreationFailed(format!("Failed to write backup file: {}", e))
        })?;

        Ok(())
    }

    /// Restores registry settings from a JSON backup file
    fn restore_registry_settings(&self, backup_path: &PathBuf) -> Result<(), RestoreError> {
        // Read backup file
        let backup_json = fs::read_to_string(backup_path)?;

        // Parse backup data
        let backup_data: serde_json::Value = serde_json::from_str(&backup_json)?;

        // Extract color table and screen colors
        let color_table_hex = backup_data
            .get("color_table")
            .and_then(|v| v.as_array())
            .ok_or_else(|| {
                RestoreError::RestoreFailed("Invalid backup file: missing color_table".to_string())
            })?;

        let screen_colors = backup_data
            .get("screen_colors")
            .and_then(|v| v.as_u64())
            .ok_or_else(|| {
                RestoreError::RestoreFailed(
                    "Invalid backup file: missing screen_colors".to_string(),
                )
            })? as u32;

        // Write colors back to registry
        #[cfg(windows)]
        {
            use winreg::enums::*;
            use winreg::RegKey;

            let hkcu = RegKey::predef(HKEY_CURRENT_USER);
            let console_key = hkcu
                .open_subkey_with_flags("Console", KEY_WRITE)
                .map_err(|e| {
                    RestoreError::RestoreFailed(format!(
                        "Failed to open Console registry key: {}",
                        e
                    ))
                })?;

            let registry_handler = RegistryHandler::new();

            // Restore all 16 ColorTable entries
            for (i, hex_color_value) in color_table_hex.iter().enumerate() {
                let hex_color = hex_color_value.as_str().ok_or_else(|| {
                    RestoreError::RestoreFailed(format!("Invalid color value at index {}", i))
                })?;

                // Convert hex to colorref
                let colorref = registry_handler
                    .colorref_to_hex_inverse(hex_color)
                    .map_err(|e| {
                        RestoreError::RestoreFailed(format!(
                            "Failed to convert color {}: {}",
                            hex_color, e
                        ))
                    })?;

                let key_name = format!("ColorTable{:02}", i);
                console_key.set_value(&key_name, &colorref).map_err(|e| {
                    RestoreError::RestoreFailed(format!("Failed to write {}: {}", key_name, e))
                })?;
            }

            // Restore ScreenColors
            console_key
                .set_value("ScreenColors", &screen_colors)
                .map_err(|e| {
                    RestoreError::RestoreFailed(format!("Failed to write ScreenColors: {}", e))
                })?;
        }

        #[cfg(not(windows))]
        {
            return Err(RestoreError::RestoreFailed(
                "Registry operations are only supported on Windows".to_string(),
            ));
        }

        Ok(())
    }
}

/// Errors that can occur during backup operations
#[derive(Debug, Error)]
pub enum BackupError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Failed to determine backup location")]
    NoBackupLocation,
    
    #[error("Backup creation failed: {0}")]
    CreationFailed(String),
}

/// Errors that can occur during restore operations
#[derive(Debug, Error)]
pub enum RestoreError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("No backup found")]
    NoBackup,
    
    #[error("Restore failed: {0}")]
    RestoreFailed(String),
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_backup_manager_creation() {
        // Test that BackupManager can be created and directory is created
        let manager = BackupManager::new();
        assert!(manager.is_ok(), "BackupManager should be created successfully");

        let manager = manager.unwrap();
        assert!(
            manager.backup_dir.exists(),
            "Backup directory should exist after creation"
        );
    }

    #[test]
    fn test_get_backup_path_windows_terminal() {
        let manager = BackupManager::new().unwrap();
        let test_path = PathBuf::from("C:\\test\\settings.json");
        let console_type = ConsoleType::WindowsTerminal {
            settings_path: test_path,
        };

        let backup_path = manager.get_backup_path(&console_type);
        assert!(
            backup_path.ends_with("wt_backup.json"),
            "Windows Terminal backup should be wt_backup.json"
        );
    }

    #[test]
    fn test_get_backup_path_legacy_console() {
        let manager = BackupManager::new().unwrap();
        let console_type = ConsoleType::LegacyConsole;

        let backup_path = manager.get_backup_path(&console_type);
        assert!(
            backup_path.ends_with("console_backup.json"),
            "Legacy Console backup should be console_backup.json"
        );
    }

    #[test]
    fn test_backup_exists_initially_false() {
        let manager = BackupManager::new().unwrap();
        // Clean up any existing backups
        let _ = fs::remove_file(manager.backup_dir.join("wt_backup.json"));
        let _ = fs::remove_file(manager.backup_dir.join("console_backup.json"));

        assert!(
            !manager.backup_exists(),
            "Should return false when no backups exist"
        );
    }

    #[test]
    fn test_backup_exists_with_wt_backup() {
        let manager = BackupManager::new().unwrap();
        let wt_backup_path = manager.backup_dir.join("wt_backup.json");

        // Create a dummy backup file
        fs::write(&wt_backup_path, "{}").unwrap();

        assert!(
            manager.backup_exists(),
            "Should return true when Windows Terminal backup exists"
        );

        // Clean up
        let _ = fs::remove_file(wt_backup_path);
    }

    #[test]
    fn test_backup_exists_with_console_backup() {
        let manager = BackupManager::new().unwrap();
        let console_backup_path = manager.backup_dir.join("console_backup.json");

        // Create a dummy backup file
        fs::write(&console_backup_path, "{}").unwrap();

        assert!(
            manager.backup_exists(),
            "Should return true when Legacy Console backup exists"
        );

        // Clean up
        let _ = fs::remove_file(console_backup_path);
    }

    #[test]
    fn test_create_backup_windows_terminal() {
        let manager = BackupManager::new().unwrap();

        // Create a temporary settings.json file
        let temp_dir = std::env::temp_dir().join("cmd-theme-test");
        fs::create_dir_all(&temp_dir).unwrap();
        let settings_path = temp_dir.join("settings.json");
        fs::write(&settings_path, r#"{"test": "data"}"#).unwrap();

        let console_type = ConsoleType::WindowsTerminal {
            settings_path: settings_path.clone(),
        };

        // Clean up any existing backup
        let backup_path = manager.get_backup_path(&console_type);
        let _ = fs::remove_file(&backup_path);

        // Create backup
        let result = manager.create_backup(&console_type);
        assert!(result.is_ok(), "Backup creation should succeed");

        // Verify backup file exists
        assert!(
            backup_path.exists(),
            "Backup file should exist after creation"
        );

        // Verify backup content matches original
        let backup_content = fs::read_to_string(&backup_path).unwrap();
        let original_content = fs::read_to_string(&settings_path).unwrap();
        assert_eq!(
            backup_content, original_content,
            "Backup content should match original"
        );

        // Clean up
        let _ = fs::remove_file(backup_path);
        let _ = fs::remove_dir_all(temp_dir);
    }

    #[test]
    fn test_create_backup_only_once() {
        let manager = BackupManager::new().unwrap();

        // Create a temporary settings.json file
        let temp_dir = std::env::temp_dir().join("cmd-theme-test-once");
        fs::create_dir_all(&temp_dir).unwrap();
        let settings_path = temp_dir.join("settings.json");
        fs::write(&settings_path, r#"{"test": "original"}"#).unwrap();

        let console_type = ConsoleType::WindowsTerminal {
            settings_path: settings_path.clone(),
        };

        // Clean up any existing backup
        let backup_path = manager.get_backup_path(&console_type);
        let _ = fs::remove_file(&backup_path);

        // Create first backup
        manager.create_backup(&console_type).unwrap();
        let first_backup_content = fs::read_to_string(&backup_path).unwrap();

        // Modify original file
        fs::write(&settings_path, r#"{"test": "modified"}"#).unwrap();

        // Try to create backup again
        manager.create_backup(&console_type).unwrap();
        let second_backup_content = fs::read_to_string(&backup_path).unwrap();

        // Backup should not have changed (only created once)
        assert_eq!(
            first_backup_content, second_backup_content,
            "Backup should not be overwritten if it already exists"
        );

        // Clean up
        let _ = fs::remove_file(backup_path);
        let _ = fs::remove_dir_all(temp_dir);
    }

    #[test]
    fn test_restore_backup_no_backup_error() {
        let manager = BackupManager::new().unwrap();

        let console_type = ConsoleType::LegacyConsole;
        let backup_path = manager.get_backup_path(&console_type);

        // Ensure no backup exists
        let _ = fs::remove_file(&backup_path);

        // Try to restore
        let result = manager.restore_backup(&console_type);
        assert!(result.is_err(), "Should fail when no backup exists");

        match result.unwrap_err() {
            RestoreError::NoBackup => {
                // Expected error
            }
            _ => panic!("Expected NoBackup error"),
        }
    }

    #[test]
    fn test_restore_backup_windows_terminal() {
        let manager = BackupManager::new().unwrap();

        // Create temporary settings file and backup
        let temp_dir = std::env::temp_dir().join("cmd-theme-test-restore");
        fs::create_dir_all(&temp_dir).unwrap();
        let settings_path = temp_dir.join("settings.json");
        fs::write(&settings_path, r#"{"test": "modified"}"#).unwrap();

        let console_type = ConsoleType::WindowsTerminal {
            settings_path: settings_path.clone(),
        };

        // Create a backup manually
        let backup_path = manager.get_backup_path(&console_type);
        fs::write(&backup_path, r#"{"test": "original"}"#).unwrap();

        // Restore backup
        let result = manager.restore_backup(&console_type);
        assert!(result.is_ok(), "Restore should succeed");

        // Verify settings.json was restored
        let restored_content = fs::read_to_string(&settings_path).unwrap();
        assert_eq!(
            restored_content,
            r#"{"test": "original"}"#,
            "Settings should be restored from backup"
        );

        // Clean up
        let _ = fs::remove_file(backup_path);
        let _ = fs::remove_dir_all(temp_dir);
    }

    #[test]
    fn test_backup_manager_different_console_types() {
        let manager = BackupManager::new().unwrap();

        // Test that different console types have different backup paths
        let temp_dir = std::env::temp_dir().join("cmd-theme-test-types");
        fs::create_dir_all(&temp_dir).unwrap();
        let settings_path = temp_dir.join("settings.json");

        let wt_console = ConsoleType::WindowsTerminal {
            settings_path: settings_path.clone(),
        };
        let legacy_console = ConsoleType::LegacyConsole;

        let wt_path = manager.get_backup_path(&wt_console);
        let legacy_path = manager.get_backup_path(&legacy_console);

        assert_ne!(
            wt_path, legacy_path,
            "Different console types should have different backup paths"
        );

        // Clean up
        let _ = fs::remove_dir_all(temp_dir);
    }
}
