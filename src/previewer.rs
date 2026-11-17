// Theme preview functionality

use crate::theme::{ColorScheme, Theme};
use colored::*;

/// Handles theme preview display
pub struct ThemePreviewer;

impl ThemePreviewer {
    /// Displays a visual preview of a theme's metadata in a formatted box
    /// 
    /// This method displays the theme's name, description, author, and palette type
    /// in a nicely formatted box using terminal formatting from the colored crate.
    /// 
    /// # Arguments
    /// * `theme` - A reference to the Theme to preview
    /// 
    /// # Example
    /// ```no_run
    /// use cmd_theme::theme::Theme;
    /// use cmd_theme::previewer::ThemePreviewer;
    /// 
    /// let theme = // ... load theme
    /// ThemePreviewer::preview_theme(&theme);
    /// ```
    pub fn preview_theme(theme: &Theme) {
        // Display theme metadata in a formatted box
        println!("{}", "╔══════════════════════════════════════════════════════════╗".bright_blue());
        println!("{} {:<47}{}",
            "║".bright_blue(),
            format!("Theme: {}", theme.name).bold(),
            "║".bright_blue()
        );
        println!("{} {:<47}{}",
            "║".bright_blue(),
            format!("Description: {}", theme.description),
            "║".bright_blue()
        );
        println!("{} {:<47}{}",
            "║".bright_blue(),
            format!("Author: {}", theme.author),
            "║".bright_blue()
        );
        println!("{} {:<47}{}",
            "║".bright_blue(),
            format!("Type: {:?}", theme.palette_type),
            "║".bright_blue()
        );
        println!("{}", "╚══════════════════════════════════════════════════════════╝".bright_blue());
        println!();
        
        // Display color palette
        Self::display_color_palette(&theme.colors);
        
        println!();
        
        // Display sample content
        Self::display_sample_content(&theme.colors);
    }
    
    /// Displays the color palette with colored blocks showing all 16 ANSI colors
    /// 
    /// This method displays each color with:
    /// - Color name rendered on a background with the actual color
    /// - Hex value (#RRGGBB format)
    /// - Standard and bright variants displayed side by side
    /// - Background and foreground colors at the end
    /// 
    /// The text color on each colored block is automatically adjusted based on
    /// background brightness to ensure readability (black text for light colors,
    /// white text for dark colors).
    /// 
    /// # Arguments
    /// * `colors` - A reference to the ColorScheme to display
    /// 
    /// **Validates: Requirements 4.2, 4.3**
    fn display_color_palette(colors: &ColorScheme) {
        println!("Color Palette:");
        println!();
        
        // Helper function to create a colored block with text
        let display_color = |name: &str, hex: &str| {
            // Parse hex color to RGB
            let r = u8::from_str_radix(&hex[1..3], 16).unwrap_or(0);
            let g = u8::from_str_radix(&hex[3..5], 16).unwrap_or(0);
            let b = u8::from_str_radix(&hex[5..7], 16).unwrap_or(0);
            
            // Create colored block: show color name on colored background
            let colored_block = format!("  {}  ", name)
                .on_truecolor(r, g, b);
            
            // Determine text color based on brightness (use white text for dark colors, black for light)
            // Using the relative luminance formula: (299*R + 587*G + 114*B) / 1000
            let brightness = (r as u32 * 299 + g as u32 * 587 + b as u32 * 114) / 1000;
            let text_colored = if brightness > 128 {
                colored_block.black()
            } else {
                colored_block.white()
            };
            
            format!("{} {}", text_colored, hex)
        };
        
        // Display standard and bright variants side by side
        println!("  {:<42}  {}", 
            display_color("Black", &colors.black),
            display_color("Bright Black", &colors.bright_black)
        );
        println!("  {:<42}  {}", 
            display_color("Red", &colors.red),
            display_color("Bright Red", &colors.bright_red)
        );
        println!("  {:<42}  {}", 
            display_color("Green", &colors.green),
            display_color("Bright Green", &colors.bright_green)
        );
        println!("  {:<42}  {}", 
            display_color("Yellow", &colors.yellow),
            display_color("Bright Yellow", &colors.bright_yellow)
        );
        println!("  {:<42}  {}", 
            display_color("Blue", &colors.blue),
            display_color("Bright Blue", &colors.bright_blue)
        );
        println!("  {:<42}  {}", 
            display_color("Magenta", &colors.magenta),
            display_color("Bright Magenta", &colors.bright_magenta)
        );
        println!("  {:<42}  {}", 
            display_color("Cyan", &colors.cyan),
            display_color("Bright Cyan", &colors.bright_cyan)
        );
        println!("  {:<42}  {}", 
            display_color("White", &colors.white),
            display_color("Bright White", &colors.bright_white)
        );
        
        println!();
        
        // Display background and foreground colors
        println!("  {}    {}", 
            display_color("Background", &colors.background),
            display_color("Foreground", &colors.foreground)
        );
    }
    
    /// Displays sample content demonstrating how the theme looks with realistic terminal output
    /// 
    /// This method shows:
    /// - A realistic directory listing (like dir/ls output) using appropriate colors
    /// - Sample success messages in green
    /// - Sample warning messages in yellow
    /// - Sample error messages in red
    /// - Demonstrates foreground and background color combinations
    /// 
    /// # Arguments
    /// * `colors` - A reference to the ColorScheme to use for coloring the sample output
    /// 
    /// **Validates: Requirements 4.4**
    fn display_sample_content(colors: &ColorScheme) {
        println!("Sample Output:");
        println!();
        
        // Helper function to parse hex color to RGB for truecolor output
        let parse_hex = |hex: &str| -> (u8, u8, u8) {
            let r = u8::from_str_radix(&hex[1..3], 16).unwrap_or(0);
            let g = u8::from_str_radix(&hex[3..5], 16).unwrap_or(0);
            let b = u8::from_str_radix(&hex[5..7], 16).unwrap_or(0);
            (r, g, b)
        };
        
        // Parse theme colors
        let (fg_r, fg_g, fg_b) = parse_hex(&colors.foreground);
        let (cyan_r, cyan_g, cyan_b) = parse_hex(&colors.cyan);
        let (blue_r, blue_g, blue_b) = parse_hex(&colors.blue);
        let (white_r, white_g, white_b) = parse_hex(&colors.white);
        let (green_r, green_g, green_b) = parse_hex(&colors.green);
        let (yellow_r, yellow_g, yellow_b) = parse_hex(&colors.yellow);
        let (red_r, red_g, red_b) = parse_hex(&colors.red);
        
        // Display sample directory listing
        println!("  {} {}", 
            ">".truecolor(fg_r, fg_g, fg_b),
            "dir C:\\Windows".truecolor(fg_r, fg_g, fg_b)
        );
        println!("  {}", 
            "Directory of C:\\Windows".truecolor(cyan_r, cyan_g, cyan_b)
        );
        println!();
        
        // Sample directory entries with colors
        println!("  {}  {}    {}          {}",
            "01/15/2024  10:30 AM".truecolor(fg_r, fg_g, fg_b),
            "<DIR>".truecolor(cyan_r, cyan_g, cyan_b),
            " ".truecolor(fg_r, fg_g, fg_b),
            "System32".truecolor(blue_r, blue_g, blue_b)
        );
        println!("  {}  {}    {}          {}",
            "01/15/2024  10:30 AM".truecolor(fg_r, fg_g, fg_b),
            "<DIR>".truecolor(cyan_r, cyan_g, cyan_b),
            " ".truecolor(fg_r, fg_g, fg_b),
            "SysWOW64".truecolor(blue_r, blue_g, blue_b)
        );
        println!("  {}  {}  {}",
            "01/15/2024  11:45 AM".truecolor(fg_r, fg_g, fg_b),
            "    2,048,512".truecolor(fg_r, fg_g, fg_b),
            "notepad.exe".truecolor(white_r, white_g, white_b)
        );
        println!("  {}  {}  {}",
            "01/15/2024  11:45 AM".truecolor(fg_r, fg_g, fg_b),
            "      124,416".truecolor(fg_r, fg_g, fg_b),
            "explorer.exe".truecolor(white_r, white_g, white_b)
        );
        
        println!();
        
        // Sample status messages demonstrating different colors
        println!("  {}", 
            "[SUCCESS] Operation completed successfully".truecolor(green_r, green_g, green_b)
        );
        println!("  {}", 
            "[WARNING] Low disk space".truecolor(yellow_r, yellow_g, yellow_b)
        );
        println!("  {}", 
            "[ERROR] File not found".truecolor(red_r, red_g, red_b)
        );
        
        println!();
        
        // Demonstrate foreground and background combination
        let (bg_r, bg_g, bg_b) = parse_hex(&colors.background);
        println!("  {} {}",
            "Foreground on Background:".truecolor(fg_r, fg_g, fg_b),
            "Sample text".truecolor(fg_r, fg_g, fg_b).on_truecolor(bg_r, bg_g, bg_b)
        );
    }
}
