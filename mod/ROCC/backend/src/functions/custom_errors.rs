use std::error::Error;
use std::fmt;
// Define a custom error type
#[derive(Debug)]
pub struct CustomError(pub Box<dyn Error + Send + Sync + 'static>);

impl fmt::Display for CustomError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Error for CustomError {}

impl From<Box<dyn Error + Send + Sync + 'static>> for CustomError {
    fn from(error: Box<dyn Error + Send + Sync + 'static>) -> Self {
        CustomError(error)
    }
}