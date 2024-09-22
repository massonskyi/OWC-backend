use serde::{Serialize, Deserialize};


#[derive(Serialize, Deserialize, Debug)]
pub struct UserModel {
    pub id: i32,
    pub name: String,
    pub surname: String,
    pub age: i32,
    pub username: String,
    pub email: String,
    pub hash_password: String,

    pub created_at: String,

    pub updated_at: String,

    pub deleted_at: Option<String>, // Optional field
    pub last_active: String,
    pub role: String,
    pub avatar: String,
    pub status: String,
    pub token: String,
    
    // Uncomment and adjust if needed
    // pub workspaces: Vec<WorkspaceModel>,
}
impl Clone for UserModel {
    fn clone(&self) -> Self {
        Self { id: self.id.clone(), name: self.name.clone(), surname: self.surname.clone(), age: self.age.clone(), username: self.username.clone(), email: self.email.clone(), hash_password: self.hash_password.clone(), created_at: self.created_at.clone(), updated_at: self.updated_at.clone(), deleted_at: self.deleted_at.clone(), last_active:self.last_active.clone(), role: self.role.clone(), avatar: self.avatar.clone(), status: self.status.clone(), token: self.token.clone()}
    }
}