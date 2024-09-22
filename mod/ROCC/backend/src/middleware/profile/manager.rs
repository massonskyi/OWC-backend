// profile_manager.rs
use crate::middleware::auth::{manager::UserManager, models::UserModel};
use super::models::UserProfile;
use std::collections::HashMap;

impl From<UserModel> for UserProfile {
    fn from(user_model: UserModel) -> Self {
        UserProfile {
            id: user_model.id,
            name: user_model.name,
            email: user_model.email,
            surname: user_model.surname,
            username: user_model.username,
            avatar: user_model.avatar,
            created_at: user_model.created_at,
            updated_at: user_model.updated_at
        }
    }
}

impl UserManager {
    pub async fn get_profile(&self, user_id: i32) -> Option<UserProfile> {
        let query = "SELECT id, name, surname, email, username, avatar, created_at, updated_at FROM users WHERE id = $1";
        let client = self.pool.lock().await;

        match client.query_one(query, &[&user_id]).await {
            Ok(row) => Some(UserProfile {
                id: row.get(0),
                name: row.get(1),
                surname: row.get(2),
                email: row.get(3),
                username: row.get(4),
                avatar: row.get(5),
                created_at: row.get(6),
                updated_at: row.get(7),
            }),
            Err(_) => None,
        }
    }

    pub async fn update_profile(&self, user_id: i32, update_data: HashMap<String, String>) -> Result<UserProfile, String> {
        // Call self.update_user, which returns a Result<UserModel, _>
        self.update_user(user_id, update_data)
            .await
            // Convert the UserModel to UserProfile on success
            .map(|user_model| user_model.into())
            // Convert the error into a String
            .map_err(|e| e.to_string())
    }

    pub async fn delete_profile(&self, user_id: i32) -> Result<(), String> {
        let query = "DELETE FROM users WHERE id = $1";
        let client = self.pool.lock().await;

        client.execute(query, &[&user_id])
            .await
            .map_err(|e| format!("Failed to delete profile: {}", e))
            .map(|_| ())
    }
}