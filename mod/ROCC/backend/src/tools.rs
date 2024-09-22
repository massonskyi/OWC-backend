use chrono::Local;
use std::{error::Error, fs, path::Path};

pub fn create_logger_file() -> Result<String, Box<dyn Error>> {
    // Define the directory path
    let log_dir = "./log";

    // Check if the directory exists, if not, create it
    if !Path::new(log_dir).exists() {
        fs::create_dir_all(log_dir)?; // Creates the directory and any parent directories if necessary
    }

    // Get the current local time
    let now = Local::now();

    // Format it as a string (e.g., "2024-08-27_12-34-56")
    let datetime_str = now.format("%Y-%m-%d_%H-%M-%S").to_string();
    
    // Create the file path string
    let file_path = format!("{}/{}.log", log_dir, datetime_str);
    
    // Return the file path wrapped in a Result
    Ok(file_path)
}