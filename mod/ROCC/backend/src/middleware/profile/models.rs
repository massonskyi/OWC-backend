// profile_model.rs
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct UserProfile {
    pub id: i32,
    pub name: String,
    pub surname: String,
    pub email: String,
    pub username: String,
    pub avatar: String,
    pub created_at: String,
    pub updated_at: String,
}
