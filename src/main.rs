// CMD Theme Pack - Main Entry Point
// A command-line utility for managing and applying color schemes to Windows Command Prompt

mod theme;
mod theme_loader;
mod console_detector;
mod wt_handler;
mod registry_handler;
mod backup_manager;
mod previewer;
mod cli;

use cli::Cli;

fn main() {
    // Entry point for the application
    // CLI parsing and command routing happens in cli.rs
    cli::run();
}
