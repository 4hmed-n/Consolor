// Command-line interface and argument parsing

use clap::{CommandFactory, Parser, Subcommand};
use crate::console_detector::{ConsoleDetector, ConsoleType};
use crate::theme_loader::ThemeLoader;
use crate::backup_manager::BackupManager;
use crate::wt_handler::WindowsTerminalHandler;
use crate::registry_handler::RegistryHandler;
use crate::previewer::ThemePreviewer;
use colored::*;

/// CMD Theme Pack - Manage and apply CMD color themes
#[derive(Parser)]
#[command(name = "cmd-theme")]
#[command(about = "Manage and apply CMD color themes", long_about = None)]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    command: Commands,
}

/// Available CLI commands
#[derive(Subcommand)]
pub enum Commands {
    /// List all available themes
    List,
    
    /// Preview a theme without applying it
    Preview {
        /// Theme name to preview
        theme_name: String,
    },
    
    /// Apply a theme to the console
    Apply {
        /// Theme name to apply
        theme_name: String,
        
        /// Skip backup creation
        #[arg(long)]
        no_backup: bool,
    },
    
    /// Restore console settings from backup
    Restore,
    
    /// Display help information
    Help,
}

/// Main CLI entry point
pub fn run() {
    let cli = Cli::parse();

    match cli.command {
        Commands::List => {
            handle_list();
        }
        Commands::Preview { theme_name } => {
            handle_preview(&theme_name);
        }
        Commands::Apply { theme_name, no_backup } => {
            handle_apply(&theme_name, no_backup);
        }
        Commands::Restore => {
            handle_restore();
        }
        Commands::Help => {
            Cli::command().print_help().unwrap();
        }
    }
}

/// Handle list command
/// 
/// Lists all available themes with their metadata.
/// Indicates which theme is currently applied (for Windows Terminal).
/// 
/// **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
fn handle_list() {
    // Load themes using ThemeLoader
    let mut loader = match ThemeLoader::new() {
        Ok(loader) => loader,
        Err(e) => {
            eprintln!("{} Failed to load themes: {}", "ERROR:".red().bold(), e);
            std::process::exit(1);
        }
    };
    
    // Load user themes from directory
    if let Err(e) = loader.load_all_themes() {
        eprintln!("{} Failed to load user themes: {}", "WARNING:".yellow().bold(), e);
    }
    
    // Get all themes
    let themes = loader.list_themes();
    
    // Check if no themes found
    if themes.is_empty() {
        println!("{}", "No themes available.".yellow());
        println!();
        println!("Themes are embedded in the executable or can be added to:");
        println!("  %LOCALAPPDATA%\\cmd-theme-pack\\themes\\");
        return;
    }
    
    // Detect console type to check for current scheme
    let console_type = ConsoleDetector::detect();
    let current_scheme = match &console_type {
        ConsoleType::WindowsTerminal { settings_path } => {
            let handler = WindowsTerminalHandler::new(settings_path.clone());
            handler.get_current_scheme().ok().flatten()
        }
        _ => None,
    };
    
    // Display themes with formatting
    println!("Available Themes:");
    println!();
    
    for theme in &themes {
        // Check if this is the currently active theme
        let is_active = current_scheme.as_ref() == Some(&theme.name);
        
        // Display theme with indicator
        if is_active {
            println!("  {} {} {}", "●".green(), theme.name.bold(), "[ACTIVE]".green());
        } else {
            println!("  {}", theme.name.bold());
        }
        
        // Display metadata
        println!("      {}", theme.description);
        println!("      {} by {} • {:?}", 
            "Type:".dimmed(),
            theme.author,
            theme.palette_type
        );
        println!();
    }
    
    // Display summary
    println!("Total: {} theme{}", themes.len(), if themes.len() != 1 { "s" } else { "" });
}

/// Handle preview command
/// 
/// Loads the requested theme and displays a visual preview using ThemePreviewer.
/// If the theme is not found, displays an error message listing available themes.
/// 
/// This function is read-only and does not modify Console_Settings.
/// 
/// # Arguments
/// * `theme_name` - Name of the theme to preview
/// 
/// **Validates: Requirements 4.1, 4.5, 5.6**
fn handle_preview(theme_name: &str) {
    // Load themes using ThemeLoader
    let mut loader = match ThemeLoader::new() {
        Ok(loader) => loader,
        Err(e) => {
            eprintln!("{} Failed to load themes: {}", "ERROR:".red().bold(), e);
            std::process::exit(1);
        }
    };
    
    // Load user themes from directory
    if let Err(e) = loader.load_all_themes() {
        eprintln!("{} Failed to load user themes: {}", "WARNING:".yellow().bold(), e);
    }
    
    // Find the requested theme by name
    match loader.get_theme(theme_name) {
        Some(theme) => {
            // Use ThemePreviewer to display the theme
            ThemePreviewer::preview_theme(theme);
        }
        None => {
            // Theme not found - show error and list available themes
            eprintln!("{} Theme '{}' not found", "ERROR:".red().bold(), theme_name);
            eprintln!();
            eprintln!("Available themes:");
            
            let themes = loader.list_themes();
            if themes.is_empty() {
                eprintln!("  (no themes available)");
            } else {
                for theme in themes {
                    eprintln!("  - {}", theme.name);
                }
            }
            eprintln!();
            eprintln!("Use 'cmd-theme list' to see all available themes with descriptions.");
            std::process::exit(1);
        }
    }
}

/// Handle apply command
/// 
/// Detects console type, loads theme, creates backup, and applies the theme.
/// 
/// # Arguments
/// * `theme_name` - Name of the theme to apply
/// * `no_backup` - If true, skip backup creation
/// 
/// **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**
fn handle_apply(theme_name: &str, no_backup: bool) {
    // Detect console type
    let console_type = ConsoleDetector::detect();
    
    // Load theme
    let mut loader = match ThemeLoader::new() {
        Ok(loader) => loader,
        Err(e) => {
            eprintln!("{} Failed to load themes: {}", "ERROR:".red().bold(), e);
            std::process::exit(1);
        }
    };
    
    // Load user themes
    if let Err(e) = loader.load_all_themes() {
        eprintln!("{} Failed to load user themes: {}", "WARNING:".yellow().bold(), e);
    }
    
    // Get the requested theme
    let theme = match loader.get_theme(theme_name) {
        Some(theme) => theme.clone(),
        None => {
            eprintln!("{} Theme '{}' not found", "ERROR:".red().bold(), theme_name);
            eprintln!();
            eprintln!("Available themes:");
            
            let themes = loader.list_themes();
            if themes.is_empty() {
                eprintln!("  (no themes available)");
            } else {
                for t in themes {
                    eprintln!("  - {}", t.name);
                }
            }
            eprintln!();
            eprintln!("Use 'cmd-theme list' to see all available themes.");
            std::process::exit(1);
        }
    };
    
    // Create backup unless no_backup flag is set
    if !no_backup {
        let backup_manager = match BackupManager::new() {
            Ok(manager) => manager,
            Err(e) => {
                eprintln!("{} Failed to initialize backup manager: {}", "ERROR:".red().bold(), e);
                std::process::exit(1);
            }
        };
        
        // Only create backup if one doesn't already exist
        if !backup_manager.backup_exists() {
            if let Err(e) = backup_manager.create_backup(&console_type) {
                eprintln!("{} Failed to create backup: {}", "ERROR:".red().bold(), e);
                eprintln!("Use --no-backup flag to skip backup creation.");
                std::process::exit(1);
            }
            println!("{} Backup created successfully", "✓".green());
        }
    }
    
    // Apply theme based on console type
    match &console_type {
        ConsoleType::WindowsTerminal { settings_path } => {
            let handler = WindowsTerminalHandler::new(settings_path.clone());
            
            match handler.apply_theme(&theme) {
                Ok(()) => {
                    println!("{} Theme '{}' applied successfully to Windows Terminal!", "✓".green(), theme.name);
                    println!();
                    println!("Restart Windows Terminal or open a new tab to see the changes.");
                }
                Err(e) => {
                    eprintln!("{} Failed to apply theme: {}", "ERROR:".red().bold(), e);
                    
                    // Check for permission errors
                    if e.to_string().contains("permission") || e.to_string().contains("denied") {
                        eprintln!();
                        eprintln!("Ensure Windows Terminal is not running and you have write access.");
                    }
                    
                    std::process::exit(1);
                }
            }
        }
        ConsoleType::LegacyConsole => {
            let handler = RegistryHandler::new();
            
            match handler.apply_theme(&theme) {
                Ok(()) => {
                    println!("{} Theme '{}' applied successfully to Legacy Console!", "✓".green(), theme.name);
                    println!();
                    println!("Open a new Command Prompt window to see the changes.");
                }
                Err(e) => {
                    eprintln!("{} Failed to apply theme: {}", "ERROR:".red().bold(), e);
                    
                    // Check for permission errors
                    if e.to_string().contains("permission") || e.to_string().contains("denied") {
                        eprintln!();
                        eprintln!("Try running cmd-theme from an elevated command prompt (Run as Administrator).");
                    }
                    
                    std::process::exit(1);
                }
            }
        }
        ConsoleType::Unknown => {
            eprintln!("{} Unable to detect console type", "ERROR:".red().bold());
            eprintln!("This tool supports Windows Terminal and Legacy Console (CMD).");
            std::process::exit(1);
        }
    }
}

/// Handle restore command
/// 
/// Restores console settings from the backup file.
/// 
/// **Validates: Requirements 6.3, 6.4, 6.5**
fn handle_restore() {
    // Detect console type
    let console_type = ConsoleDetector::detect();
    
    // Initialize backup manager
    let backup_manager = match BackupManager::new() {
        Ok(manager) => manager,
        Err(e) => {
            eprintln!("{} Failed to initialize backup manager: {}", "ERROR:".red().bold(), e);
            std::process::exit(1);
        }
    };
    
    // Check if backup exists
    if !backup_manager.backup_exists() {
        eprintln!("{} No backup found", "ERROR:".red().bold());
        eprintln!();
        eprintln!("A backup is created automatically when you first apply a theme.");
        eprintln!("Use 'cmd-theme apply <theme>' to apply a theme and create a backup.");
        std::process::exit(1);
    }
    
    // Restore from backup
    match backup_manager.restore_backup(&console_type) {
        Ok(()) => {
            // Success message is printed by restore_backup
        }
        Err(e) => {
            eprintln!("{} Failed to restore from backup: {}", "ERROR:".red().bold(), e);
            std::process::exit(1);
        }
    }
}
