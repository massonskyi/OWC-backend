use std::error::Error;

use std::env;
use dotenvy::dotenv;


pub fn establish_connection() -> Result<String, Box<dyn Error>> {
    dotenv().ok();  // Load environment variables from .env if available

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let host = env::var("DB_HOST").expect("Host not found");
    let port = env::var("DB_PORT").expect("Port not found");
    println!("Started connected to database on url{database_url} {host} {port}");
    Ok(database_url)
}